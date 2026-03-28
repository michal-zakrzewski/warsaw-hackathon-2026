# Voice Interview

A web application that conducts voice interviews using AI. The agent asks questions from a configurable JSON file, speaks them aloud, listens to the candidate's spoken responses, and maintains a natural conversational flow.

Built with **FastAPI** (Python) and the **Vapi Web SDK** for real-time voice interaction.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your Vapi public key to .env
echo "VAPI_PUBLIC_KEY=your-key-here" > .env

# 3. Run the server
uvicorn main:app --reload

# 4. Open http://localhost:8000 in your browser
```

## How It Works

1. The backend loads interview questions from `questions.json` and builds a system prompt
2. The frontend fetches this config and starts a Vapi voice session in the browser
3. Vapi orchestrates the full loop: LLM generates responses, TTS speaks them, STT transcribes the user
4. The live transcript is displayed on screen and saved to `transcripts/` when the interview ends

## Project Structure

```
├── main.py            # FastAPI backend (API + static file serving)
├── questions.json     # Interview questions (edit to customize)
├── requirements.txt   # Python dependencies
├── .env               # VAPI_PUBLIC_KEY (not committed)
├── static/
│   ├── index.html     # Interview UI
│   ├── style.css      # Styling
│   └── app.js         # Vapi Web SDK integration
└── transcripts/       # Saved interview transcripts (auto-created)
```

## Customizing Questions

Edit `questions.json` to change the interview topic, instructions, and question list:

```json
{
  "interview_title": "Your Interview Title",
  "instructions": "Instructions for the AI interviewer on how to conduct the interview...",
  "questions": [
    "First question",
    "Second question"
  ]
}
```

## API Endpoints

| Method | Path               | Description                                  |
|--------|--------------------|----------------------------------------------|
| GET    | `/api/config`      | Returns Vapi public key + assistant config   |
| POST   | `/api/transcripts` | Saves a completed interview transcript       |
| GET    | `/`                | Serves the web UI                            |
