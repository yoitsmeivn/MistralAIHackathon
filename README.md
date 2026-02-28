# Canard 🦆 — Voice Agent Web Service

Canard is a hackathon-built voice agent web service. You type a message, an AI agent replies using Mistral, and you can hear the reply spoken aloud via ElevenLabs text-to-speech — all from a browser.

---

## What Is This Project?

Canard is a **monorepo** containing two main pieces that talk to each other:

1. **A Python/FastAPI backend** — receives your text, sends it to Mistral AI for a response, and can convert any text to speech via ElevenLabs.
2. **A Next.js web frontend** — a dark-themed chat UI where you type messages, see the conversation, and click a button to hear replies read aloud.

The frontend calls the backend API. The backend calls Mistral and ElevenLabs. That's the whole flow.

---

## Languages & Technologies

| Layer | Language | Framework / Runtime | Purpose |
|-------|----------|-------------------|---------|
| **Backend API** | Python 3.11+ | FastAPI + uvicorn | REST API server, agent logic, LLM & TTS integration |
| **Frontend** | TypeScript | Next.js 15 (React 19) | Chat UI, audio playback in browser |
| **Shared types** | TypeScript | — | Type definitions for API contracts (reference package) |
| **Workspace** | — | pnpm | Monorepo package management for TypeScript packages |

---

## Dependencies

### Python Backend (`services/api/`)

| Package | Version | What it does |
|---------|---------|-------------|
| `fastapi` | ≥ 0.115 | Web framework for the API endpoints |
| `uvicorn[standard]` | ≥ 0.34 | ASGI server that runs FastAPI |
| `httpx` | ≥ 0.28 | Async HTTP client for calling Mistral & ElevenLabs APIs |
| `pydantic` | ≥ 2.10 | Data validation and request/response models |
| `pydantic-settings` | ≥ 2.7 | Loads config from `.env` file into typed settings |
| `python-dotenv` | ≥ 1.0 | `.env` file loading |

### Web Frontend (`apps/web/`)

| Package | Version | What it does |
|---------|---------|-------------|
| `next` | ≥ 15.3 | React framework with App Router, dev server, build |
| `react` | ≥ 19.1 | UI rendering |
| `react-dom` | ≥ 19.1 | DOM rendering for React |
| `typescript` | ≥ 5.7 | Type checking |

### External APIs (not installed — called over HTTP)

| Service | What it does | Endpoint called |
|---------|-------------|-----------------|
| **Mistral AI** | LLM chat completions (generates agent replies) | `POST {base_url}/v1/chat/completions` |
| **ElevenLabs** | Text-to-speech (converts text to mp3 audio) | `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}` |

---

## Project Structure

```
canard/
│
├── .env.example              # Template for environment variables
├── .gitignore                # Git ignore rules (Node + Python)
├── package.json              # pnpm workspace root scripts
├── pnpm-workspace.yaml       # Declares workspace packages
├── tsconfig.base.json        # Shared TypeScript compiler config
│
├── services/
│   └── api/                  # ── PYTHON BACKEND (FastAPI) ──
│       ├── pyproject.toml    # Python project metadata & deps
│       ├── requirements.txt  # Pinned Python dependencies
│       └── app/
│           ├── main.py       # FastAPI app creation, CORS, router registration
│           ├── config.py     # Settings loaded from .env via pydantic-settings
│           ├── models.py     # Pydantic models for API requests/responses
│           │
│           ├── routes/
│           │   ├── agent.py  # POST /api/agent/text  — chat with the agent
│           │   │             # POST /api/agent/tts   — text to speech
│           │   └── health.py # GET  /health           — health check
│           │
│           ├── lib/
│           │   ├── mistral.py    # call_llm() — calls Mistral chat completions via httpx
│           │   ├── elevenlabs.py # text_to_speech() — calls ElevenLabs TTS via httpx
│           │   └── sessions.py   # In-memory session store (Python dict)
│           │
│           └── agents/
│               ├── types.py  # Dataclasses: Message, AgentConfig, ConversationState, etc.
│               ├── agent.py  # run_agent_turn() — the core agent loop
│               ├── tools.py  # ToolRegistry — register & execute tool handlers
│               └── memory.py # trim_messages(), create_initial_state()
│
├── apps/
│   └── web/                  # ── TYPESCRIPT FRONTEND (Next.js) ──
│       ├── package.json
│       ├── tsconfig.json
│       ├── next.config.ts    # Proxies /api/* requests to the Python backend
│       └── src/
│           ├── app/
│           │   ├── layout.tsx    # Root HTML layout, imports global CSS
│           │   ├── page.tsx      # Home page — renders ChatPage component
│           │   └── globals.css   # Dark theme styles (pure CSS, no framework)
│           └── components/
│               └── ChatPage.tsx  # Client component: chat UI, send messages, play audio
│
└── packages/
    └── shared/               # ── TYPESCRIPT TYPE REFERENCE ──
        ├── package.json      # @canard/shared
        ├── tsconfig.json
        └── src/
            ├── index.ts      # Re-exports types and utils
            ├── types.ts      # API contract interfaces, Message types, STT stubs
            └── utils.ts      # generateId(), formatTimestamp(), delay()
```

---

## How Everything Connects

```
┌─────────────────────┐        ┌──────────────────────────────────┐
│   Browser (3000)    │        │   FastAPI Backend (3001)          │
│                     │  HTTP  │                                   │
│  Next.js ChatPage   ├───────►│  POST /api/agent/text            │
│  - type message     │        │    → session_store.get_or_create  │
│  - see transcript   │        │    → run_agent_turn()             │
│  - click "Speak"    │        │      → call_llm() ──► Mistral AI │
│                     │◄───────┤    ← { reply, sessionId }        │
│                     │        │                                   │
│  fetch /api/agent/  │  HTTP  │  POST /api/agent/tts             │
│  tts ──────────────►├───────►│    → text_to_speech()             │
│  ← audio blob       │        │      → httpx POST ──► ElevenLabs │
│  → new Audio().play │◄───────┤    ← audio/mpeg bytes            │
└─────────────────────┘        └──────────────────────────────────┘
```

The Next.js frontend **never calls Mistral or ElevenLabs directly**. It only talks to the FastAPI backend. The `next.config.ts` rewrites proxy all `/api/*` requests from port 3000 to port 3001 so the browser doesn't hit CORS issues.

---

## How to Run Everything

### Prerequisites

- **Python 3.11+** (`python3 --version`)
- **Node.js 18+** (`node --version`)
- **pnpm** (`npm install -g pnpm`)
- A **Mistral AI** API key ([console.mistral.ai](https://console.mistral.ai))
- An **ElevenLabs** API key ([elevenlabs.io](https://elevenlabs.io)) — optional, only needed for TTS

### Step 1 — Clone and configure

```bash
git clone <your-repo-url> canard
cd canard
cp .env.example .env
```

Edit `.env` and fill in your keys:

```env
MISTRAL_API_KEY=your-mistral-api-key-here
MISTRAL_BASE_URL=https://api.mistral.ai
MISTRAL_MODEL=mistral-small-latest
ELEVENLABS_API_KEY=your-elevenlabs-key-here
ELEVENLABS_VOICE_ID=your-preferred-voice-id
PORT=3001
```

### Step 2 — Install Python backend dependencies

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ../..
```

### Step 3 — Install frontend dependencies

```bash
pnpm install
```

### Step 4 — Start both servers

You need **two terminals**:

**Terminal 1 — Python API backend:**
```bash
cd services/api
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 3001
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:3001
```

**Terminal 2 — Next.js frontend:**
```bash
pnpm dev:web
```

You should see:
```
▲ Next.js 15.x
- Local: http://localhost:3000
```

### Step 5 — Use it

1. Open **http://localhost:3000** in your browser
2. Type a message and press Enter (or click Send)
3. The agent replies using Mistral AI
4. Click **🔊 Speak** on any reply to hear it via ElevenLabs TTS

---

## API Endpoints

All endpoints are served by the FastAPI backend on port 3001.

### `POST /api/agent/text`

Chat with the agent. Creates a session automatically on the first call.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sessionId` | string | No | Reuse an existing session. Omit for a new one. |
| `text` | string | Yes | Your message to the agent. |

**Response:**
```json
{
  "reply": "Hello! I'm Canard. How can I help you?",
  "sessionId": "ses_a1b2c3d4e5f6g7h8"
}
```

### `POST /api/agent/tts`

Convert text to speech. Returns raw audio bytes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Text to speak. |
| `voiceId` | string | No | Override the default ElevenLabs voice. |

**Response:** Binary `audio/mpeg` data.

### `GET /health`

Simple health check.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-02-28T12:00:00.000000+00:00"
}
```

### Interactive API Docs

FastAPI auto-generates Swagger UI at **http://localhost:3001/docs** — you can test every endpoint directly from your browser.

---

## How the Agent Works

The agent loop lives in `services/api/app/agents/agent.py`:

1. **Receive user input** → adds it to the conversation's message list
2. **Call Mistral LLM** → sends the full conversation to `POST /v1/chat/completions`
3. **Check for tool calls** → if the LLM wants to call a tool, execute it and loop back (max 3 iterations)
4. **Return reply** → the assistant's text response + the updated conversation state
5. **Trim history** → keeps the last N messages (default 20) to stay within context limits, always preserving the system prompt

Sessions are stored in a Python `dict` in memory. They reset when the server restarts. This is intentional — it's a hackathon prototype, not a production system.

---

## How the Build Works

| Component | Build command | What happens |
|-----------|--------------|-------------|
| Python backend | No build step | Python is interpreted. Just run `uvicorn`. |
| Next.js frontend | `pnpm build:web` | Compiles TypeScript, bundles React, generates static pages |
| Shared types | `pnpm build:shared` | Runs `tsc --build` to compile TypeScript to JavaScript + declarations |
| Everything (TS) | `pnpm build` | Runs build across all pnpm workspace packages |

For development, you don't need to build anything — just run the servers in dev mode (they hot-reload).

---

## Environment Variables

All config is read from a single `.env` file at the repository root.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MISTRAL_API_KEY` | **Yes** | — | API key from [console.mistral.ai](https://console.mistral.ai) |
| `MISTRAL_BASE_URL` | No | `https://api.mistral.ai` | Base URL for Mistral API |
| `MISTRAL_MODEL` | No | `mistral-small-latest` | Which Mistral model to use |
| `ELEVENLABS_API_KEY` | For TTS | — | API key from [elevenlabs.io](https://elevenlabs.io) |
| `ELEVENLABS_VOICE_ID` | No | `21m00Tcm4TlvDq8ikWAM` | Default ElevenLabs voice |
| `PORT` | No | `3001` | Port for the Python API server |

The Python backend reads `.env` via `pydantic-settings` (configured to look at `../../.env` relative to `services/api/`). The Next.js frontend only needs `NEXT_PUBLIC_API_URL` if you want to point to a different backend URL (defaults to `http://localhost:3001`).

---

## Workspace Scripts (pnpm)

Run these from the repo root:

| Command | What it does |
|---------|-------------|
| `pnpm dev:web` | Start Next.js frontend in dev mode (port 3000) |
| `pnpm build:web` | Production build of the frontend |
| `pnpm build:shared` | Compile the shared TypeScript types package |
| `pnpm build` | Build all TypeScript workspace packages |
| `pnpm clean` | Delete all build outputs (dist/, .next/) |
| `pnpm typecheck` | Run TypeScript type checking across all packages |
