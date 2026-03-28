import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google import genai
from pydantic import BaseModel

load_dotenv()

VAPI_PUBLIC_KEY = os.getenv("VAPI_PUBLIC_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
QUESTIONS_PATH = Path(__file__).parent / "questions.json"
TRANSCRIPTS_DIR = Path(__file__).parent / "transcripts"
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

gemini_client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

app = FastAPI(title="Voice Interview API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_questions() -> dict:
    with open(QUESTIONS_PATH) as f:
        return json.load(f)


def build_system_prompt(data: dict) -> str:
    questions_block = "\n".join(
        f"  {i + 1}. {q}" for i, q in enumerate(data["questions"])
    )
    return (
        f"{data['instructions']}\n\n"
        f"Interview: {data['interview_title']}\n\n"
        "CONVERSATION RULES:\n"
        "- This is a turn-based voice conversation. Ask ONE question at a time, "
        "then WAIT for the user to respond before continuing.\n"
        "- After the user answers, acknowledge their response briefly, then ask "
        "the next question.\n"
        "- If the user's answer is vague or incomplete, ask a follow-up to clarify "
        "before moving on.\n"
        "- Do NOT rush through questions. Be patient and conversational.\n"
        "- Do NOT end the conversation on your own until you have covered all the "
        "key topics below OR the user explicitly says they want to stop.\n"
        "- If the user says 'end session', 'stop', 'that's all', or similar, "
        "wrap up immediately.\n\n"
        f"Questions to cover:\n{questions_block}\n\n"
        "CRITICAL — NEVER STOP EARLY:\n"
        "- NEVER end the conversation prematurely. NEVER go silent.\n"
        "- If there is a pause, ask the next question or a follow-up.\n"
        "- If the user seems distracted, gently re-engage them.\n"
        "- ALWAYS keep the conversation going until ALL questions above "
        "have been covered.\n\n"
        "ENDING THE CONVERSATION:\n"
        "Only when you have gathered enough information on ALL key topics above, "
        "OR the user explicitly asks to stop:\n"
        "1. Summarize what you've learned back to the farmer.\n"
        "2. Thank them for their time.\n"
        "3. Let them know the team will now analyze their situation.\n"
        "4. IMMEDIATELY after your goodbye message, you MUST call the "
        "endCall function to hang up. Do NOT just go silent — you MUST "
        "call endCall to properly end the session."
    )


@app.get("/voice/config")
def get_config():
    data = load_questions()
    system_prompt = build_system_prompt(data)
    return {
        "publicKey": VAPI_PUBLIC_KEY,
        "interviewTitle": data["interview_title"],
        "assistantConfig": {
            "name": "GreenCredit Advisor",
            "firstMessage": (
                "Hey there! I'm your GreenCredit Copilot. "
                "I'm going to ask you a few simple questions about your farm "
                "so we can figure out the best green investment and financing "
                "options for you. Sound good?"
            ),
            "model": {
                "provider": "google",
                "model": "gemini-2.5-flash",
                "messages": [
                    {"role": "system", "content": system_prompt},
                ],
            },
            "voice": {
                "provider": "vapi",
                "voiceId": "Elliot",
            },
            "silenceTimeoutSeconds": 300,
            "maxDurationSeconds": 1800,
            "endCallFunctionEnabled": True,
            "endCallMessage": "Thanks for chatting! We'll analyze everything and get back to you with recommendations. Goodbye!",
            "hipaaEnabled": False,
            "backgroundDenoisingEnabled": True,
            "responseDelaySeconds": 1,
        },
    }


class TranscriptMessage(BaseModel):
    role: str
    content: str
    timestamp: str | None = None


class TranscriptPayload(BaseModel):
    interviewTitle: str
    messages: list[TranscriptMessage]


@app.post("/voice/transcripts")
def save_transcript(payload: TranscriptPayload):
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"interview_{ts}.json"
    filepath = TRANSCRIPTS_DIR / filename
    filepath.write_text(json.dumps(payload.model_dump(), indent=2))
    return {"status": "saved", "filename": filename}


EXTRACTION_PROMPT = """\
You are a data extraction assistant. Below is a transcript of a voice \
interview with a farmer or business owner about their green investment needs.

Extract as much structured information as possible into the following JSON \
schema. Use null for any field the user did not mention or that cannot be \
reasonably inferred. Do NOT make up data — only extract what was actually said.

Return ONLY valid JSON, no markdown fences, no commentary.

Schema:
{
  "businessName": string | null,
  "businessType": string | null,
  "address": string | null,
  "latitude": string | null,
  "longitude": string | null,
  "annualEnergy": string | null,        // in kWh if mentioned
  "estimatedBudget": string | null,
  "sustainabilityGoal": string | null,
  "additionalContext": string | null     // any other useful details the user \
shared (farm size, existing equipment, buildings, previous grant experience, \
energy sources, etc.) as a concise paragraph
}

Transcript:
"""


class ExtractPayload(BaseModel):
    messages: list[TranscriptMessage]


@app.post("/voice/extract")
def extract_from_transcript(payload: ExtractPayload):
    if not gemini_client:
        return JSONResponse(
            status_code=500,
            content={"error": "GOOGLE_API_KEY not configured"},
        )

    conversation = "\n".join(
        f"{msg.role.upper()}: {msg.content}" for msg in payload.messages if msg.content
    )

    questions_data = load_questions()
    questions_list = "\n".join(
        f"- {q}" for q in questions_data.get("questions", [])
    )
    context_hint = (
        f"\n\nThe interview was designed to cover these topics:\n{questions_list}\n"
    )

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=EXTRACTION_PROMPT + conversation + context_hint,
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        extracted = json.loads(raw)
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=422,
            content={"error": "Failed to parse extraction result"},
        )

    return {"extracted": extracted}
