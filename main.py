import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

VAPI_PUBLIC_KEY = os.getenv("VAPI_PUBLIC_KEY", "")
QUESTIONS_PATH = Path(__file__).parent / "questions.json"
TRANSCRIPTS_DIR = Path(__file__).parent / "transcripts"
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Voice Interview")


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
        "ENDING THE CONVERSATION:\n"
        "Only when you have gathered enough information on ALL key topics above, "
        "summarize what you've learned back to the farmer, thank them for their "
        "time, and let them know the team will now analyze their situation and "
        "come back with recommendations."
    )


@app.get("/api/config")
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
                "provider": "openai",
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                ],
            },
            "voice": {
                "provider": "vapi",
                "voiceId": "Elliot",
            },
            "silenceTimeoutSeconds": 120,
            "maxDurationSeconds": 1800,
        },
    }


class TranscriptMessage(BaseModel):
    role: str
    content: str
    timestamp: str | None = None


class TranscriptPayload(BaseModel):
    interviewTitle: str
    messages: list[TranscriptMessage]


@app.post("/api/transcripts")
def save_transcript(payload: TranscriptPayload):
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"interview_{ts}.json"
    filepath = TRANSCRIPTS_DIR / filename
    filepath.write_text(json.dumps(payload.model_dump(), indent=2))
    return {"status": "saved", "filename": filename}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
