# Voice Assistant — GreenCredit Copilot

Real-time voice interview system that collects farm/business information through a conversational AI advisor. Built with **Vapi** (voice AI platform), **Gemini 2.5 Flash** (LLM), and integrated into the React frontend as a sidebar panel on the Intake page.

## Architecture

```
Browser (React + @vapi-ai/web SDK)
    │
    ├─► Vapi Cloud (WebRTC voice pipeline)
    │       ├─ STT: speech-to-text
    │       ├─ LLM: Gemini 2.5 Flash (generates responses)
    │       └─ TTS: Vapi voice "Elliot" (text-to-speech)
    │
    └─► voice_server.py (FastAPI, port 8001)
            ├─ GET  /voice/config       → assistant config + public key
            └─ POST /voice/transcripts  → saves completed transcripts
```

The browser talks directly to Vapi's infrastructure over WebRTC for the voice loop. The FastAPI backend only serves configuration and stores transcripts — it does not proxy audio or LLM calls.

## Quick Start

### Prerequisites

- Python 3.12+ with `fastapi`, `uvicorn`, `python-dotenv`
- Node.js 20+ (for the Vite frontend)
- A [Vapi](https://vapi.ai) account with a public key
- A Google API key (for Gemini, configured in Vapi dashboard)

### 1. Set environment variables

Add to your `.env` in the project root:

```
VAPI_PUBLIC_KEY=your-vapi-public-key
```

### 2. Start the voice backend

```bash
source venv/bin/activate
uvicorn voice_server:app --port 8001 --reload
```

### 3. Start the frontend

```bash
cd frontend
npm run dev
```

### 4. Open the app

Navigate to `http://localhost:5173/intake` — the voice assistant panel is on the right side. Click **Start Assessment** to begin.

## How It Works

1. The frontend fetches `/api/voice/config` which returns the Vapi public key and full assistant configuration (system prompt, model, voice settings).
2. On "Start Assessment", the `@vapi-ai/web` SDK requests microphone permission and opens a WebRTC session with Vapi's cloud.
3. Vapi orchestrates the full voice loop: STT transcribes user speech → Gemini generates a response → TTS speaks it back.
4. Final transcript messages stream back to the browser via Vapi events and render as chat bubbles in real time.
5. When the conversation ends (agent calls `endCall` or the user clicks End Session), the transcript is saved via `POST /api/voice/transcripts`.

## Configuration

### Interview Questions

Edit `questions.json` in the project root to customize the interview:

```json
{
  "interview_title": "Your Title",
  "instructions": "Persona and behavior instructions for the AI...",
  "questions": [
    "First question to ask",
    "Second question to ask"
  ]
}
```

### Voice & Model Settings (in `voice_server.py`)

| Setting | Current Value | Description |
|---|---|---|
| `model.provider` | `google` | LLM provider |
| `model.model` | `gemini-2.5-flash` | LLM model |
| `voice.provider` | `vapi` | TTS provider |
| `voice.voiceId` | `Elliot` | Voice persona |
| `silenceTimeoutSeconds` | `300` | Seconds of silence before auto-ending |
| `maxDurationSeconds` | `1800` | Maximum call duration (30 min) |
| `endCallFunctionEnabled` | `true` | Allows the model to hang up when done |
| `responseDelaySeconds` | `1` | Brief pause before responding |

## Project Structure

```
├── voice_server.py                  # FastAPI voice backend (port 8001)
├── questions.json                   # Interview questions & instructions
├── transcripts/                     # Saved interview transcripts (auto-created)
├── frontend/
│   ├── src/components/VoiceChat.tsx  # React component (Vapi integration)
│   └── vite.config.ts               # Proxy: /api/voice → localhost:8001
└── .env                             # VAPI_PUBLIC_KEY
```

## API Reference

### `GET /voice/config`

Returns the Vapi public key and assistant configuration.

**Response:**
```json
{
  "publicKey": "...",
  "interviewTitle": "GreenCredit Copilot — Farm Assessment",
  "assistantConfig": { ... }
}
```

### `POST /voice/transcripts`

Saves a completed interview transcript.

**Request body:**
```json
{
  "interviewTitle": "GreenCredit Copilot — Farm Assessment",
  "messages": [
    { "role": "assistant", "content": "Hey there! ...", "timestamp": "..." },
    { "role": "user", "content": "Hi, I have a farm ...", "timestamp": "..." }
  ]
}
```

**Response:**
```json
{ "status": "saved", "filename": "interview_20260328_135037.json" }
```
