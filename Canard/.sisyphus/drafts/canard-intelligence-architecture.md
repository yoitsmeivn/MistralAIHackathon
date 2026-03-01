# Canard Intelligence Architecture — Complete Technical Reference

> **Purpose**: Enterprise-grade technical reference for the Canard voice-based social-engineering simulation platform. Covers every file, every integration, every data flow, and every extension point — so you understand the entire system before building.
>
> **Audience**: Developers working on Canard (you).
>
> **Last Updated**: February 2026 | Mistral AI Hackathon

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Real-Time Voice Pipeline](#2-real-time-voice-pipeline)
3. [File-by-File Codebase Map](#3-file-by-file-codebase-map)
4. [Mistral Agent Brain — Deep Dive](#4-mistral-agent-brain--deep-dive)
5. [Twilio Integration](#5-twilio-integration)
6. [ElevenLabs Integration](#6-elevenlabs-integration)
7. [W&B Weave Tracing](#7-wb-weave-tracing)
8. [Database Schema & Data Flows](#8-database-schema--data-flows)
9. [Configuration & Environment Variables](#9-configuration--environment-variables)
10. [Known Issues & TODOs](#10-known-issues--todos)
11. [Future Capabilities](#11-future-capabilities)
12. [Optimization Plan Reference](#12-optimization-plan-reference)

---

## 1. System Overview

### What Canard Does

Canard is a **voice-based social-engineering simulation platform**. It:

1. Places realistic outbound phone calls to employees via Twilio
2. An AI agent (powered by Mistral LLM) plays the role of a social engineer
3. The agent attempts scripted attack scenarios (phishing, pretexting, etc.)
4. All speech is processed in real-time: STT (ElevenLabs) → LLM (Mistral) → TTS (ElevenLabs)
5. After the call, Mistral analyzes the transcript and assigns a risk score
6. Results are displayed on a dashboard for security training teams

### Architecture Diagram

```
                            ┌─────────────────────────┐
                            │     Next.js Dashboard    │
                            │       (apps/web/)        │
                            │                          │
                            │  - Start calls           │
                            │  - View risk scores      │
                            │  - Campaign management   │
                            │  - Employee analytics    │
                            └────────────┬────────────┘
                                         │ HTTP REST
                                         ▼
┌────────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (services/api/)                │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │  API Routes   │  │  Services    │  │  Twilio Voice Handlers   │ │
│  │  /api/calls   │  │  calls.py    │  │  /twilio/voice           │ │
│  │  /api/campaigns│ │  analysis.py │  │  /twilio/status          │ │
│  │  /api/employees│ │  campaigns.py│  │  /twilio/recording       │ │
│  │  /api/dashboard│ │  media.py    │  │  /twilio/stream (WS)    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────────┘ │
│         │                 │                      │                 │
│  ┌──────┴─────────────────┴──────────────────────┴───────────────┐ │
│  │                    Agent Brain (agent/)                        │ │
│  │  loop.py — session lifecycle + turn execution                 │ │
│  │  memory.py — in-memory session store with message history     │ │
│  │  prompts.py — system prompt builder with safety guardrails    │ │
│  │  scoring.py — post-call risk analysis via Mistral             │ │
│  │  redaction.py — PII regex engine (email/phone/SSN/CC/codes)  │ │
│  └──────────────────────────┬────────────────────────────────────┘ │
│                             │                                      │
│  ┌──────────────────────────┴────────────────────────────────────┐ │
│  │                 Integrations Layer                             │ │
│  │  mistral.py — LLM chat completion + transcript analysis       │ │
│  │  elevenlabs.py — TTS, batch STT, realtime STT WebSocket      │ │
│  └──────┬──────────────────────┬─────────────────────────────────┘ │
│         │                      │                                   │
│  ┌──────┴───────┐       ┌─────┴──────┐                            │
│  │  Database     │       │  Models     │                           │
│  │  db/client.py │       │  Pydantic   │                           │
│  │  db/queries.py│       │  data models│                           │
│  └──────┬───────┘       └────────────┘                            │
└─────────┼──────────────────────────────────────────────────────────┘
          │
    ┌─────┼─────────────────────────────────────────┐
    │     ▼              ▼              ▼            │
    │  ┌────────┐  ┌──────────┐  ┌──────────────┐  │
    │  │Supabase│  │  Twilio   │  │  ElevenLabs  │  │
    │  │Postgres│  │  Voice    │  │  TTS + STT   │  │
    │  └────────┘  └──────────┘  └──────────────┘  │
    │                    ▲                          │
    │              ┌─────┴──────┐                   │
    │              │  Mistral   │                   │
    │              │  LLM API   │                   │
    │              └────────────┘                   │
    │          External Services                    │
    └───────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js + React | Dashboard UI |
| **Backend** | Python 3.11 + FastAPI + Uvicorn | API server |
| **LLM** | Mistral AI (`mistral-small-latest`) | Agent brain + risk analysis |
| **TTS** | ElevenLabs (voice synthesis) | Agent voice output |
| **STT** | ElevenLabs Scribe v1 (Realtime + Batch) | User speech recognition |
| **Telephony** | Twilio Voice + Media Streams | Phone calls + bidirectional audio |
| **Database** | Supabase (PostgreSQL) | Persistent data storage |
| **Tracing** | W&B Weave (planned) | LLM observability |
| **Infra** | Docker + docker-compose | Containerized deployment |

### Repository Structure

```
Canard/
├── canard_details.json          # Database schema documentation
├── README.md                    # Project README
├── .env.example                 # Environment variable template
├── pnpm-workspace.yaml          # Monorepo config
│
├── apps/
│   └── web/                     # Next.js dashboard (frontend)
│
├── packages/
│   └── shared/                  # Shared TypeScript types
│
└── services/
    └── api/                     # Python FastAPI backend
        ├── Dockerfile
        ├── docker-compose.yml
        ├── requirements.txt
        ├── pyproject.toml
        ├── tests/               # pytest test suite
        │   ├── conftest.py
        │   ├── test_redaction.py
        │   ├── test_models.py
        │   └── test_health.py
        └── app/                 # Application code
            ├── main.py          # FastAPI app entry point
            ├── config.py        # Settings (env vars)
            ├── agent/           # Agent brain
            ├── db/              # Database layer
            ├── integrations/    # External service clients
            ├── models/          # Pydantic data models
            ├── routes/          # API route handlers
            ├── services/        # Business logic
            └── twilio_voice/    # Twilio voice handlers
```

---

## 2. Real-Time Voice Pipeline


### The Complete Call Lifecycle

Every call follows this lifecycle from start to finish:

```
pending --> ringing --> in-progress --> [streaming voice loop] --> completed --> analyzed
```

### Step-by-Step Flow

#### Phase 1: Call Initiation (Dashboard to Twilio)

```
1. DASHBOARD: User clicks Start Call
   POST /api/calls/start {employee_id, script_id, caller_id?}

2. API ROUTE: routes/calls.py
   Validates employee and script exist in Supabase
   INSERT INTO calls (status=pending)
   Calls services/calls.py::start_call()

3. SERVICE: services/calls.py::start_call()
   Calls twilio_voice/client.py::make_outbound_call()
   Twilio REST API: POST /Accounts/{SID}/Calls.json
     Params: to=employee_phone, from_=twilio_number,
             url={PUBLIC_BASE_URL}/twilio/voice,
             record=True,
             status_callback={PUBLIC_BASE_URL}/twilio/status
   Returns: twilio_call_sid
   UPDATE calls SET twilio_call_sid=X, status=ringing, started_at

4. TWILIO: Dials the employee phone number
   When answered, Twilio POSTs to /twilio/voice
```

#### Phase 2: WebSocket Handshake (Twilio to Server)

```
5. WEBHOOK: POST /twilio/voice (twilio_voice/routes.py)
   Receives: CallSid, CallStatus
   Looks up call record by twilio_call_sid
   Returns TwiML: Response > Connect > Stream url=wss://server/twilio/stream
     with Parameter name=call_id value={uuid}
   This tells Twilio: open a bidirectional WebSocket

6. TWILIO: Opens WebSocket to /twilio/stream
   Sends: {event: connected}
   Sends: {event: start, streamSid: ..., start: {callSid: ...}}
   Now audio can flow both directions over this single WebSocket

7. SERVER: WebSocket handler (twilio_voice/routes.py)
   Accepts WebSocket connection
   Consumes connected and start messages
   Extracts: stream_sid, call_id, twilio_call_sid
   Creates CallSessionData (twilio_voice/session.py)
```

#### Phase 3: Greeting (Server to Twilio to Employee Phone)

```
8. SERVER: Generates greeting audio
   ElevenLabs TTS: text_to_speech('Hello! Lets begin.')
   Receives: audio_bytes in ulaw_8000 format (mu-law 8kHz)
   Encodes audio to base64
   Sends to Twilio over WebSocket:
     {event: media, streamSid: ..., media: {payload: base64_audio}}
   Employee hears: 'Hello! Lets begin.'
   Records TurnRecord(role=AGENT, text=greeting, turn_index=0)
```

#### Phase 4: Real-Time Voice Loop (The Core)

This is the heart of Canard. Two concurrent async tasks run simultaneously:

```
Task A: _receive_twilio()          Task B: _agent_loop()
  Receives audio from Twilio          Processes speech + generates
  and feeds it to STT                 agent responses
       |                                   |
       +---------- audio_queue -----------+
            (asyncio.Queue[bytes|None])


DETAILED FLOW:

  Employee speaks into phone
       |
       v
  Twilio captures audio as mulaw chunks (160 bytes per 20ms frame)
       |
       v
  Twilio sends over WebSocket: {event: media, media: {payload: base64}}
       |
       v
  Task A: _receive_twilio()
    - Decode base64 to raw bytes
    - Put bytes into audio_queue
    - (Also handles: stop, mark, dtmf events)
       |
       v
  audio_queue (asyncio.Queue)
       |
       v
  ElevenLabs Realtime STT WebSocket
    - Protocol: wss://api.elevenlabs.io/v1/speech-to-text/realtime
    - Audio format: ulaw_8000 (matches Twilio native format)
    - Commit strategy: VAD (Voice Activity Detection)
    - Concurrent send/receive:
        _send_audio(): Reads from queue, sends to ElevenLabs
        _receive_transcripts(): Yields committed transcripts
    - When speaker finishes sentence: yields committed_transcript string
       |
       v
  Task B: _agent_loop()
    1. RECEIVE: Gets committed_transcript from STT iterator
    2. REDACT: redact_pii(transcript) -> RedactionResult
    3. RECORD: session.add_turn(USER, redacted_text)
    4. GENERATE: generate_agent_reply(call_id, transcript)
                 !!! CURRENTLY A STUB - returns echo !!!
                 TODO: Replace with agent/loop.py::run_turn()
                 Which calls Mistral LLM with full message history
    5. SYNTHESIZE: text_to_speech(agent_reply)
                   ElevenLabs TTS returns audio_bytes (ulaw_8000)
    6. SEND: Send audio to Twilio over WebSocket
             {event: media, media: {payload: base64(audio)}}
    7. MARK: Send mark for turn tracking
             {event: mark, mark: {name: agent_turn_N}}
    8. RECORD: session.add_turn(AGENT, text, tts_ms, audio_bytes)
    9. LOOP: Back to step 1 - wait for next user utterance
       |
       v
  Employee hears agent response through phone
  (cycle repeats until call ends)
```

#### Phase 5: Call Completion and Analysis

```
9. CALL ENDS (employee hangs up or call times out)
   Twilio sends {event: stop} over WebSocket
   Task A puts None in audio_queue
   Both tasks complete, are cancelled
   Session summary logged: session.to_summary_dict()
   TODO(db): Persist all turns, update call, run analysis

10. TWILIO: POSTs to /twilio/status
    Receives: CallSid, CallStatus=completed, RecordingUrl
    If RecordingUrl present:
      ElevenLabs batch STT: speech_to_text_from_url(RecordingUrl)
      Gets full recording transcript
    Updates call: status=completed, ended_at, recording_url
    TODO: run_post_call_analysis()

11. ANALYSIS (services/analysis.py)
    Fetches call + scenario from DB
    Formats transcript from turns + recording
    Calls Mistral: score_call(transcript, scenario_description)
    Returns: {risk_score (0-100), flags, summary, coaching}
    Stores analysis in DB, updates call with risk_score

12. DASHBOARD: Displays results
    GET /api/calls/{call_id} -> CallEnriched with risk, flags, summary
```

### Audio Format Notes

| Property | Value | Why |
|----------|-------|-----|
| **Codec** | mu-law (ulaw) | Twilio Media Streams native format |
| **Sample Rate** | 8000 Hz | Telephony standard |
| **Bit Depth** | 8-bit | mu-law compressed |
| **Frame Size** | 160 bytes | 20ms per frame |
| **ElevenLabs TTS output** | `ulaw_8000` | Matches Twilio, no transcoding needed |
| **ElevenLabs STT input** | `ulaw_8000` | Matches Twilio, no transcoding needed |

**Key insight**: The entire audio pipeline stays in `ulaw_8000` format. No transcoding happens at any point. Twilio sends ulaw, ElevenLabs STT accepts ulaw, ElevenLabs TTS outputs ulaw, and we send ulaw back to Twilio.

### Latency Profile

```
User speaks -> [Twilio ~50ms] -> [STT VAD commit ~200-500ms] -> [Mistral LLM ~500-2000ms]
           -> [ElevenLabs TTS ~200-500ms] -> [Twilio ~50ms] -> Agent speaks

Total round-trip: ~1-3 seconds (acceptable for phone conversation)
Bottleneck: Mistral LLM response time
Optimization: Streaming chat completions (planned in optimization work plan)
```

---

## 3. File-by-File Codebase Map


### 3.1 Entry Point and Configuration

#### `app/main.py` — FastAPI Application Entry Point
- **What it does**: Initializes FastAPI app with CORS middleware, registers all routers, defines app lifespan
- **Key functions**:
  - `lifespan(_app: FastAPI)` — async context manager for startup/shutdown
  - App-level: CORS middleware with `allow_origins=["*"]`
- **Registers routers**: health, calls, campaigns, employees, callers, scripts, dashboard, twilio_voice
- **Imports from**: All route modules, config
- **External services**: None directly

#### `app/config.py` — Environment Configuration
- **What it does**: Pydantic v2 Settings class loading all env vars from `../../.env`
- **Key class**: `Settings(BaseSettings)` with `model_config` pointing to `../../.env`
- **Fields**:
  - Twilio: `twilio_account_sid`, `twilio_auth_token`, `twilio_from_number`, `public_base_url`
  - Mistral: `mistral_api_key`, `mistral_base_url` (default: `https://api.mistral.ai`), `mistral_model` (default: `mistral-small-latest`)
  - ElevenLabs: `elevenlabs_api_key`, `elevenlabs_voice_id` (default: `21m00Tcm4TlvDq8ikWAM`)
  - Supabase: `supabase_url`, `supabase_service_role_key`
  - Safety: `store_raw_transcripts` (bool, default false)
  - Server: `port` (default 8000)
- **Singleton**: `settings = Settings()` at module level

---

### 3.2 Agent Brain (`app/agent/`)

This is where the AI intelligence lives.

#### `app/agent/loop.py` — Agent Conversation Loop
- **What it does**: Manages full agent session lifecycle: start, turn execution, end
- **Key functions**:
  - `async start_session(call_id: str, script_id: str, system_prompt: str)` — Creates session in SessionStore with system prompt as first message
  - `async run_turn(call_id: str, user_speech: str) -> str` — Executes one conversation turn:
    1. Redacts PII from user speech
    2. Adds user message to session history
    3. Calls `chat_completion(session.messages)` (Mistral LLM)
    4. Adds assistant response to session history
    5. Trims message history to last 20
    6. Returns agent reply text
  - `async end_session(call_id: str) -> list[dict]` — Retrieves message history and removes session
- **Imports**: `session_store` (memory.py), `redact_pii` (redaction.py), `chat_completion` (integrations/mistral.py)
- **External services**: Mistral LLM via chat_completion
- **CRITICAL NOTE**: This module is NOT wired to the WebSocket voice loop. `generate_agent_reply()` in routes.py is a stub.

#### `app/agent/memory.py` — In-Memory Session Store
- **What it does**: Thread-safe in-memory store for active call sessions with message history
- **Key classes**:
  - `CallSession` (dataclass) — `call_id`, `script_id`, `messages: list[dict]`, `turn_count`, `max_turns=10`
  - `SessionStore` — Thread-safe (RLock) session manager:
    - `create(call_id, script_id, system_prompt) -> CallSession`
    - `get(call_id) -> CallSession | None`
    - `add_message(call_id, role, content)` — Appends {role, content} to messages list
    - `remove(call_id)`
    - `trim_messages(call_id, keep=20)` — Keeps system message + last N messages
- **Singleton**: `session_store = SessionStore()` at module level
- **IMPORTANT**: This is SEPARATE from `twilio_voice/session.py::CallSessionData`. Two independent session systems exist.

#### `app/agent/prompts.py` — System Prompt Builder
- **What it does**: Builds the system prompt that defines agent personality and behavior
- **Key functions**:
  - `build_system_prompt(scenario_name: str, script_guidelines: str) -> str`
    - Builds comprehensive prompt with:
      - Scenario context (e.g., 'IT support pretexting')
      - Safety guardrails (no real credentials, training exercise framing)
      - Behavioral instructions (concise, conversational, escalate pressure safely)
      - Output format directive (plain text, no JSON/markdown)
- **Constants**: `STREAM_GREETING = "Hello! Let's begin."`
- **HOW TO ADD NEW AGENT PERSONALITIES**: Modify this function or create new prompt templates. The `script_guidelines` parameter is where scenario-specific behavior is injected. See Section 4 for details.

#### `app/agent/scoring.py` — Post-Call Risk Analysis
- **What it does**: Formats transcripts and calls Mistral to analyze call risk
- **Key functions**:
  - `format_transcript(turns: list[dict]) -> str` — Converts turn dicts to readable format: `User: ...\nAgent: ...`
  - `async score_call(transcript_text: str, scenario_description: str) -> dict` — Calls Mistral with analysis prompt, returns:
    - `risk_score` (0-100, clamped)
    - `flags` (list of strings)
    - `summary` (text)
    - `coaching` (text)
- **Imports**: `analyze_transcript` from integrations/mistral.py

#### `app/agent/redaction.py` — PII Redaction Engine
- **What it does**: Detects and masks PII before storing/processing text
- **Key class**: `RedactionResult` (dataclass) — `redacted_text`, `original_text`, `redactions: list[dict]`, `has_sensitive_content`
- **Key function**: `redact_pii(text: str) -> RedactionResult`
- **Patterns detected**:
  - Emails: `[REDACTED_EMAIL]`
  - Phone numbers: `[REDACTED_PHONE]`
  - SSNs: `[REDACTED_SSN]`
  - Credit card numbers: `[REDACTED_CC]`
  - Passwords (after 'password is'): `[REDACTED_PASSWORD]`
  - Numeric codes (4-8 digits): `[REDACTED_CODE]`
- **Algorithm**: Finds all matches, sorts by position, resolves overlaps, replaces

---

### 3.3 Integrations (`app/integrations/`)

#### `app/integrations/mistral.py` — Mistral LLM Client
- **What it does**: Raw httpx async client for Mistral API (NOT using official SDK)
- **Key functions**:
  - `async chat_completion(messages: list[dict], model: str | None = None, temperature: float = 0.7, max_tokens: int | None = None) -> str`
    - POST to `{mistral_base_url}/v1/chat/completions`
    - Returns: `choices[0].message.content` (string)
    - Timeout: 45 seconds
    - Used by: `agent/loop.py::run_turn()` for agent replies
  - `async analyze_transcript(transcript: str, scenario_description: str) -> dict`
    - Sends analysis prompt + transcript to Mistral
    - Extracts JSON from response using `_extract_json_object()`
    - Returns: `{risk_score, flags, summary, coaching}`
    - Used by: `agent/scoring.py::score_call()`
  - `_extract_json_object(content: str) -> dict` — Parses JSON from LLM text response (handles markdown code blocks)
- **OPTIMIZATION PLANNED**: Migrate to `mistralai` SDK v1+ for auto-tracing with W&B Weave. See optimization plan.

#### `app/integrations/elevenlabs.py` — ElevenLabs TTS/STT Client
- **What it does**: Uses official AsyncElevenLabs SDK for text-to-speech and speech-to-text
- **Key functions**:
  - `async text_to_speech(text: str, voice_id: str | None = None, output_format: str = 'ulaw_8000') -> bytes`
    - Voice settings: stability=0.75, similarity_boost=0.85, style=0.0, speed=1.0
    - Returns: raw audio bytes in ulaw_8000 format
    - Used by: WebSocket handler for greeting + agent turns
  - `async speech_to_text(audio_bytes: bytes, filename: str = 'recording.wav', language_code: str | None = None) -> str`
    - Batch STT using Scribe v1 model
    - Used by: recording transcription
  - `async speech_to_text_from_url(audio_url: str, language_code: str | None = None) -> str`
    - Transcribes from public HTTPS URL (Twilio RecordingUrl)
    - Used by: /twilio/status webhook for recording transcription
  - `async realtime_stt_session(audio_queue: asyncio.Queue[bytes | None], language_code: str | None = None) -> AsyncIterator[str]`
    - WebSocket streaming STT — the CORE of the real-time pipeline
    - Protocol: `wss://api.elevenlabs.io/v1/speech-to-text/realtime`
    - Params: `model_id=scribe_v1`, `audio_format=ulaw_8000`, `commit_strategy=vad`
    - Yields: committed transcript strings (one per sentence/utterance)
    - Runs concurrent `_send_audio()` and `_receive_transcripts()` tasks

---

### 3.4 Twilio Voice Handlers (`app/twilio_voice/`)

#### `app/twilio_voice/routes.py` — 575 lines, THE MOST COMPLEX FILE
- **What it does**: All Twilio webhook handlers + WebSocket stream handler
- **Endpoints**:
  - `POST /twilio/voice` — Entry webhook when call is answered. Returns TwiML to open Media Stream.
  - `POST /twilio/status` — Call completion webhook. Transcribes recording, updates call.
  - `POST /twilio/recording` — Recording completion webhook. Logs metadata.
  - `WebSocket /twilio/stream` — **Real-time bidirectional audio** (see Section 2 for full flow)
- **Key functions**:
  - `generate_agent_reply(_call_id: str, transcript: str) -> str` — **STUB! Returns echo.** This is where Mistral should be called.
  - `_lookup_call_safe(twilio_call_sid: str) -> dict | None` — Safe DB lookup by CallSid
  - `_update_call_safe(call_id: str, data: dict)` — Safe DB update (synchronous, blocks event loop)
- **External services**: Twilio (WebSocket), ElevenLabs (TTS + Realtime STT)

#### `app/twilio_voice/session.py` — Call Session Data Accumulator
- **What it does**: Structured in-memory storage for ALL data during a live call
- **Key classes**:
  - `TurnRole(Enum)` — USER, AGENT
  - `TurnRecord` — role, text, redacted_text, turn_index, timestamp_utc, tts_duration_ms, stt_duration_ms, audio_bytes_sent
  - `ErrorRecord` — source (stt/tts/twilio/agent/websocket), error_type, message, timestamp_utc, context
  - `MarkRecord` — Twilio mark acknowledgement
  - `DtmfRecord` — DTMF digit received
  - `CallSessionData` — Main class accumulating:
    - Identity: call_id, twilio_call_sid, stream_sid
    - Timing: stream_started_at, stream_ended_at, greeting_sent_at, first_user_speech_at
    - Turns: turns list, next_turn_index
    - Recording: recording_url, recording_sid, recording_duration, recording_transcript
    - Events: errors, marks, dtmf_events
    - Status: call_status, disconnect_reason
    - Metrics: total_stt_ms, total_tts_ms, total_agent_ms, audio_chunks_received, audio_bytes_sent_total
    - Methods: add_turn(), add_error(), add_mark(), add_dtmf(), to_summary_dict()
- **Module-level**: `_active_sessions` dict, `create_session()`, `get_session()`, `remove_session()`
- **IMPORTANT**: This is SEPARATE from `agent/memory.py::SessionStore`

#### `app/twilio_voice/twiml.py` — TwiML Response Builders
- **Key functions**:
  - `stream_response(call_id: str) -> str` — TwiML to open Media Stream with call_id parameter
  - `error_hangup(text: str) -> str` — TwiML to say error message and hang up
  - `_ws_base_url() -> str` — Converts HTTP(S) base URL to WS(S)

#### `app/twilio_voice/client.py` — Twilio REST Client
- **Key functions**:
  - `make_outbound_call(to_number, webhook_url, status_callback_url, recording_callback_url) -> str`
    - Uses Twilio REST API to initiate outbound call
    - Params: to, from_, url, record=True, status_callback, recording_status_callback
    - Returns: Twilio CallSid
  - `_get_client() -> Client` — Cached Twilio REST client singleton

---

### 3.5 Services Layer (`app/services/`)

#### `app/services/calls.py` — Call Orchestration
- **Key functions**:
  - `async start_call(employee_id, script_id, caller_id?, campaign_id?, assignment_id?) -> dict`
    - Validates employee + script exist
    - Creates call record in DB (status=pending)
    - Initiates Twilio outbound call via make_outbound_call()
    - Updates call with twilio_call_sid, status=ringing, started_at
    - Returns: updated call dict
  - `update_call_status(call_id, status)` — Updates call status, sets ended_at if terminal
  - `async handle_call_completed(call_id, recording_url?, recording_transcript?)` — TODO: finalize call

#### `app/services/analysis.py` — Post-Call Analysis Pipeline
- **Key functions**:
  - `async run_post_call_analysis(call_id, recording_transcript?) -> dict | None`
    - Fetches call + scenario from DB
    - Gets turns for call
    - Formats transcript
    - Calls score_call() (Mistral)
    - Creates analysis record in DB
    - Returns: analysis dict
- **WARNING**: Calls DB functions (`get_scenario()`, `get_turns_for_call()`, `create_analysis()`) that may not exist in queries.py

#### `app/services/campaigns.py` — Campaign CRUD
- **Key functions**: `create_campaign()`, `get_campaign()`, `list_campaigns()`

#### `app/services/media.py` — In-Memory Audio Storage
- **Key functions**:
  - `store_audio(audio_bytes) -> str` — Stores audio, returns UUID media_id
  - `get_audio(media_id) -> bytes | None`
  - `remove_audio(media_id)`
  - `get_audio_url(media_id) -> str` — Returns `{public_base_url}/media/{media_id}`
- **Storage**: Module-level `_audio_store` dict (in-memory, lost on restart)

---

### 3.6 Database Layer (`app/db/`)

#### `app/db/client.py` — Supabase Client Singleton
- `get_supabase() -> Client` — Returns authenticated Supabase sync client
- Raises ValueError if SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing

#### `app/db/queries.py` — 328 lines of CRUD Operations
- **Organizations**: `create_organization()`, `get_organization()`, `get_organization_by_slug()`
- **Users**: `create_user()`, `get_user()`, `get_user_by_email()`, `list_users()`
- **Employees**: `create_employee()`, `get_employee()`, `list_employees()`, `update_employee()`
- **Callers**: `create_caller()`, `get_caller()`, `list_callers()`
- **Scripts**: `create_script()`, `get_script()`, `list_scripts()`
- **Campaigns**: `create_campaign()`, `get_campaign()`, `list_campaigns()`, `update_campaign()`
- **Campaign Assignments**: `create_campaign_assignment()`, `list_campaign_assignments()`, `update_campaign_assignment()`
- **Calls**: `create_call()`, `get_call()`, `update_call()`, `list_calls()`, `get_call_by_sid()`
- **Helpers**: `_first_or_none(data)`, `_execute(query, context)` (error handling)
- **MISSING**: `get_turns_for_call()`, `create_analysis()`, `get_scenario()` (called by analysis.py but not implemented)

---

### 3.7 API Routes (`app/routes/`)

| File | Endpoints | Purpose |
|------|-----------|---------|
| `calls.py` | `POST /api/calls/start`, `GET /api/calls/`, `GET /api/calls/{id}` | Start calls, list/get call details |
| `campaigns.py` | `POST /api/campaigns/`, `GET /api/campaigns/`, `GET /api/campaigns/{id}` | Campaign CRUD |
| `employees.py` | `GET /api/employees/` | List employees with aggregated call stats |
| `callers.py` | `GET /api/callers/` | List callers/personas with call stats |
| `scripts.py` | `GET /api/scripts/` | List available attack scripts |
| `dashboard.py` | `GET /api/dashboard/stats`, `/risk-distribution`, `/risk-by-department`, `/calls-over-time` | Dashboard analytics |
| `health.py` | `GET /health` | Liveness check with timestamp |

---

### 3.8 Data Models (`app/models/`)

All models use Pydantic v2 with camelCase serialization for frontend compatibility.

| File | Key Models | Purpose |
|------|-----------|---------|
| `api.py` | `StartCallRequest`, `StartCallResponse`, `CallEnriched`, `EmployeeListItem`, `CallerListItem`, `CampaignListItem`, `DashboardStatResponse`, `RiskDistributionResponse`, `CallsOverTimeResponse` | API request/response models |
| `calls.py` | `Call` | Full call record with all metadata |
| `campaigns.py` | `Campaign` | Campaign record |
| `employees.py` | `Employee` | Employee record |
| `scripts.py` | `Script` | Script with system_prompt, objectives, escalation_steps |
| `callers.py` | `Caller` | Caller/persona record |
| `users.py` | `User` | User account |
| `organizations.py` | `Organization` | Organization record |
| `campaign_assignments.py` | `CampaignAssignment` | Employee-to-campaign mapping |

---

## 4. Mistral Agent Brain — Deep Dive


### Where Mistral Is Called

There are exactly **TWO** places Mistral LLM is called in the codebase:

1. **`integrations/mistral.py::chat_completion()`** — For agent conversation replies
   - Called by: `agent/loop.py::run_turn()`
   - Endpoint: `POST {mistral_base_url}/v1/chat/completions`
   - Model: `settings.mistral_model` (default: `mistral-small-latest`)
   - Temperature: 0.7
   - Returns: string (assistant message content)

2. **`integrations/mistral.py::analyze_transcript()`** — For post-call risk scoring
   - Called by: `agent/scoring.py::score_call()`
   - Same endpoint, but with analysis-specific prompt
   - Returns: structured dict {risk_score, flags, summary, coaching}

Both use raw httpx async client (NOT the official Mistral SDK). The optimization plan migrates to `mistralai` SDK.

### How the Agent Thinks

```
1. System prompt is set at session start:
   build_system_prompt(scenario_name, script_guidelines) -> str
   This includes:
   - Scenario context (e.g., 'You are a social engineer conducting an IT support pretexting attack')
   - Safety guardrails (no real credential harvesting, training exercise framing)
   - Behavioral directives (be concise, conversational, escalate pressure)
   - Output format (plain text only)

2. Each turn adds to message history:
   messages = [
     {role: 'system', content: system_prompt},
     {role: 'user', content: 'Hello?'},
     {role: 'assistant', content: 'Hi! This is IT support...'},
     {role: 'user', content: 'What do you need?'},
     ... up to 20 messages kept
   ]

3. Full message history is sent to Mistral on every turn:
   chat_completion(messages) -> next agent reply

4. Memory is trimmed to prevent context overflow:
   trim_messages(keep=20) keeps system message + last 20 messages
```

### How to Add New Agent Personalities

Agent personalities are defined through **Scripts** in the database and the `build_system_prompt()` function.

#### Option 1: Via the Scripts Table (Database)
The `scripts` table has these key fields:
- `name` — Script identifier (e.g., 'IT Support Pretexting')
- `attack_type` — Category (e.g., 'pretexting', 'phishing', 'vishing')
- `difficulty` — How aggressive the agent should be
- `system_prompt` — Custom system prompt for this scenario (overrides default)
- `objectives` — JSON list of what the agent should try to extract
- `escalation_steps` — JSON list of how to escalate pressure
- `description` — Human-readable description

To add a new personality: INSERT a new row in the `scripts` table with a custom `system_prompt`.

#### Option 2: Via Callers Table (Personas)
The `callers` table defines the persona the agent assumes:
- `persona_name` — Name the agent uses (e.g., 'John from IT')
- `persona_role` — Role claimed (e.g., 'Senior IT Administrator')
- `persona_company` — Company claimed
- `attack_type` — Type of social engineering
- `phone_number` — Outbound number used

Currently, caller data is NOT injected into the prompt. The optimization plan (Task 3) adds dynamic injection of Script + Caller data into system prompts.

#### Option 3: Modify `build_system_prompt()` Directly
File: `app/agent/prompts.py`
This function takes `scenario_name` and `script_guidelines` and builds the full prompt.
You can:
- Add new personality templates
- Add dynamic data injection (employee name, company, department)
- Create different prompt styles for different attack types
- Add multi-turn strategy instructions

### How to Make the Agent Smarter

The optimization plan covers these improvements:

1. **Dynamic prompt injection** (Task 3): Pull Script objectives, escalation_steps, difficulty, and Caller persona into the system prompt at runtime
2. **Token-aware memory** (Task 4): Replace naive trim_messages(keep=20) with tiktoken-based token counting to maximize context usage within model limits
3. **Streaming completions** (Task 5): Stream tokens as they arrive instead of waiting for full response, reducing perceived latency
4. **W&B Weave tracing** (Task 2): See exactly what the agent thinks, what it sends, what it receives, with full timing data

---

## 5. Twilio Integration


### How Twilio Connects to Canard

Twilio provides the phone infrastructure. It handles the actual phone call and sends/receives audio over WebSocket.

### Setup Requirements

1. **Twilio Account**: You need `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`
2. **Phone Number**: A Twilio phone number set as `TWILIO_FROM_NUMBER`
3. **Public URL**: Your server must be reachable from the internet (`PUBLIC_BASE_URL`)
   - For local dev: use ngrok or Cloudflare Tunnel
   - Example: `PUBLIC_BASE_URL=https://abc123.ngrok.io`
4. **Webhook Configuration**: Twilio needs to POST to your webhooks (this is done automatically via the REST API when making outbound calls)

### Webhook Endpoints

| Endpoint | Method | Triggered By | Returns |
|----------|--------|-------------|---------|
| `/twilio/voice` | POST | Twilio when call is answered | TwiML to open Media Stream |
| `/twilio/status` | POST | Twilio when call status changes (initiated, ringing, answered, completed) | 200 OK |
| `/twilio/recording` | POST | Twilio when recording is ready | 200 OK |
| `/twilio/stream` | WebSocket | Twilio Media Stream connection | Bidirectional audio |

### How Outbound Calls Work

```
1. Your code calls: make_outbound_call(to_number, webhook_url, status_callback_url)
2. Twilio REST API: POST /Accounts/{SID}/Calls.json
   - to: employee phone number
   - from_: your Twilio number
   - url: {PUBLIC_BASE_URL}/twilio/voice (webhook for when call is answered)
   - record: True (full call recording)
   - status_callback: {PUBLIC_BASE_URL}/twilio/status
   - status_callback_event: [initiated, ringing, answered, completed]
   - recording_status_callback: {PUBLIC_BASE_URL}/twilio/recording
   - recording_status_callback_event: [completed]
3. Twilio dials the number
4. When answered, Twilio POSTs to /twilio/voice
5. /twilio/voice returns TwiML telling Twilio to open a Media Stream WebSocket
6. Twilio connects via WebSocket and streams audio bidirectionally
```

### Twilio Media Streams Protocol

The WebSocket at `/twilio/stream` uses Twilio Media Streams protocol:

**Incoming messages from Twilio:**
- `{event: 'connected'}` — WebSocket established
- `{event: 'start', streamSid: '...', start: {callSid: '...', tracks: ['inbound'], ...}}` — Stream started
- `{event: 'media', media: {payload: 'base64_audio', track: 'inbound', timestamp: '...'}}` — Audio chunk (20ms)
- `{event: 'stop'}` — Stream ending (call disconnecting)
- `{event: 'mark', mark: {name: 'agent_turn_N'}}` — Mark acknowledgement (audio played)
- `{event: 'dtmf', dtmf: {digit: '1'}}` — DTMF tone detected

**Outgoing messages to Twilio:**
- `{event: 'media', streamSid: '...', media: {payload: 'base64_audio'}}` — Send audio to caller
- `{event: 'mark', streamSid: '...', mark: {name: 'agent_turn_N'}}` — Set a mark for playback tracking
- `{event: 'clear', streamSid: '...'}` — Clear audio queue (interrupt)

### Key Twilio Concepts

- **CallSid**: Unique ID for each call (assigned by Twilio)
- **StreamSid**: Unique ID for each Media Stream session
- **Media Streams**: Bidirectional audio over WebSocket (the core of real-time processing)
- **TwiML**: XML-based language for controlling call behavior
- **Recording**: Twilio records the full call separately; RecordingUrl is delivered via /twilio/status

---

## 6. ElevenLabs Integration


### How ElevenLabs Powers Canard's Voice

ElevenLabs provides both the agent's voice (TTS) and ears (STT).

### Text-to-Speech (TTS)

```python
async text_to_speech(text: str, voice_id: str | None = None, output_format: str = 'ulaw_8000') -> bytes
```

- **SDK**: `AsyncElevenLabs` (official SDK)
- **Voice settings**: stability=0.75, similarity_boost=0.85, style=0.0, speed=1.0
- **Output format**: `ulaw_8000` (mu-law 8kHz) — matches Twilio native format, no transcoding needed
- **Default voice**: `settings.elevenlabs_voice_id` (default: `21m00Tcm4TlvDq8ikWAM` = 'Rachel')
- **Used in**: Greeting generation, agent response audio
- **Latency**: ~200-500ms per utterance

### Batch Speech-to-Text (STT)

```python
async speech_to_text(audio_bytes: bytes, ...) -> str
async speech_to_text_from_url(audio_url: str, ...) -> str
```

- **Model**: Scribe v1
- **Used for**: Transcribing Twilio recording after call completes
- **NOT used for**: Real-time speech during the call (that uses Realtime STT)

### Realtime Speech-to-Text (The Core)

```python
async realtime_stt_session(audio_queue: asyncio.Queue[bytes | None], ...) -> AsyncIterator[str]
```

This is the most critical integration — it powers real-time speech recognition during calls.

- **Protocol**: WebSocket to `wss://api.elevenlabs.io/v1/speech-to-text/realtime`
- **Model**: Scribe v1
- **Audio format**: `ulaw_8000` (matches Twilio format)
- **Commit strategy**: `vad` (Voice Activity Detection) — commits transcript when speaker pauses
- **How it works**:
  1. Opens WebSocket connection to ElevenLabs
  2. Sends audio_format and model_id in connection URL params
  3. Two concurrent tasks:
     - `_send_audio()`: Reads from audio_queue, sends base64-encoded chunks to ElevenLabs
     - `_receive_transcripts()`: Receives transcript events from ElevenLabs
  4. ElevenLabs sends two types of transcript events:
     - `partial_transcript`: Intermediate (not used by Canard)
     - `committed_transcript`: Final, speaker finished sentence (this is what Canard uses)
  5. Yields committed transcript strings to the agent loop

### ElevenLabs Voice Settings Explained

| Setting | Value | Effect |
|---------|-------|--------|
| `stability` | 0.75 | Higher = more consistent, less expressive. Good for professional impersonation. |
| `similarity_boost` | 0.85 | Higher = more similar to original voice. Set high for realistic persona. |
| `style` | 0.0 | Style exaggeration disabled. Keeps output natural. |
| `speed` | 1.0 | Normal speed. Could increase for urgency effect. |

### How to Change the Agent's Voice

1. **Different ElevenLabs voice**: Change `ELEVENLABS_VOICE_ID` in `.env`
2. **Different voice settings**: Modify `text_to_speech()` in `integrations/elevenlabs.py`
3. **Different TTS provider**: Replace `text_to_speech()` implementation (must output `ulaw_8000`)

---

## 7. W&B Weave Tracing


### Current State: No Tracing

Currently, Canard has ZERO observability into what the LLM is doing. You cannot see:
- What prompts are sent to Mistral
- What responses come back
- How long each call takes
- What errors occur
- How token usage trends over time

### What W&B Weave Will Provide

W&B Weave is a **mandatory** integration (hackathon sponsor requirement from Weights & Biases).

#### Automatic Tracing (via Mistral SDK Migration)
When you do `weave.init('canard')` and use the `mistralai` SDK, Weave **autopatches** all LLM calls:

```python
import weave
from mistralai import Mistral

weave.init('canard')  # This autopatches mistralai
client = Mistral(api_key=settings.mistral_api_key)

# Every call to client.chat.complete() is now automatically traced:
# - Input messages
# - Output response
# - Token usage (prompt + completion)
# - Latency (ms)
# - Model used
# - Temperature and other params
# - Errors if any
```

#### Manual Tracing (via @weave.op() decorator)
For non-LLM functions, use the `@weave.op()` decorator:

```python
import weave

@weave.op()
async def run_turn(call_id: str, user_speech: str) -> str:
    # This function is now traced:
    # - Input args (call_id, user_speech)
    # - Return value
    # - Duration
    # - Any nested weave.op() calls are linked as children
    ...

@weave.op()
async def score_call(transcript_text: str, scenario_description: str) -> dict:
    # This traces the scoring pipeline
    ...
```

#### What You See in the W&B Dashboard
- **Call tree**: Hierarchical view of all function calls within a request
- **Token usage**: Charts of prompt/completion tokens over time
- **Latency**: Distribution of response times
- **Errors**: Failed calls with full context
- **Cost**: Estimated cost per call based on token usage
- **Comparison**: Compare different model versions, prompts, temperatures

#### Weave Monitors (For Voice Agents)
Weave Monitors support audio scoring:
- Score agent performance on recorded calls
- Track quality metrics over time
- Set up automated evaluation pipelines
- Useful for comparing prompt versions or model upgrades

#### Graceful Degradation
Weave is designed to be non-blocking:
```python
try:
    weave.init('canard')
except Exception:
    pass  # App works without Weave
```
If `WANDB_API_KEY` is not set, the app runs normally without tracing. No calls fail.

#### Environment Variables for Weave
- `WANDB_API_KEY` — Required for W&B cloud tracing
- `WANDB_PROJECT` — Optional, defaults to 'canard'
- All tracing data is sent to wandb.ai cloud

---

## 8. Database Schema & Data Flows


### Tables

Canard uses Supabase (hosted PostgreSQL) with these tables:

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `organizations` | Multi-tenant org container | id, name, slug |
| `users` | User accounts (org members) | id, org_id, email, role |
| `employees` | Target participants for calls | id, org_id, full_name, email, phone, department, job_title, risk_level |
| `callers` | AI agent personas | id, org_id, persona_name, persona_role, persona_company, attack_type, phone_number |
| `scripts` | Attack scenario definitions | id, org_id, name, attack_type, difficulty, system_prompt, objectives, escalation_steps |
| `campaigns` | Batch call campaigns | id, org_id, name, description, attack_vector, status, scheduled_at |
| `campaign_assignments` | Employee-to-campaign mapping | id, campaign_id, employee_id, status |
| `calls` | Individual call records | id, org_id, employee_id, script_id, caller_id, campaign_id, status, twilio_call_sid, risk_score, transcript, flags, ai_summary |
| `turns` | Conversation turns | id, call_id, role, text, text_redacted, turn_index |
| `analysis` | Post-call risk analysis | id, call_id, risk_score, flags, summary, coaching |

### Data Flow Through Tables

```
1. Setup phase:
   organizations -> users -> employees (target people)
                         -> callers (AI personas)
                         -> scripts (attack scenarios)

2. Campaign creation:
   campaigns -> campaign_assignments (links employees)

3. Call execution:
   calls (created with employee_id + script_id)
     -> turns (user + agent messages, per-turn during call)
     -> analysis (post-call risk scoring)

4. Results query:
   calls JOIN employees -> employee risk view
   calls JOIN campaigns -> campaign progress view
   calls JOIN analysis -> detailed risk breakdown
```

### Database Schema Reference

The full database schema is documented in `canard_details.json` at the repository root. This file contains complete table definitions, relationships, and column types.

### Missing Database Functions (Known Issue)

The following functions are called in `services/analysis.py` but do NOT exist in `db/queries.py`:
- `get_scenario()` — Should fetch script details for analysis context
- `get_turns_for_call()` — Should fetch all turns for a call
- `create_analysis()` — Should store analysis results

These need to be implemented before post-call analysis works end-to-end.

---

## 9. Configuration & Environment Variables


### Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `PORT` | No | `8000` | API server port |
| `PUBLIC_BASE_URL` | Yes (prod) | `http://localhost:8000` | Public URL for Twilio webhooks |
| `TWILIO_ACCOUNT_SID` | Yes | `""` | Twilio account identifier |
| `TWILIO_AUTH_TOKEN` | Yes | `""` | Twilio auth secret |
| `TWILIO_FROM_NUMBER` | Yes | `""` | Your Twilio phone number |
| `MISTRAL_API_KEY` | Yes | `""` | Mistral AI API key |
| `MISTRAL_BASE_URL` | No | `https://api.mistral.ai` | Override for proxy/self-hosted |
| `MISTRAL_MODEL` | No | `mistral-small-latest` | Model for agent conversations |
| `ELEVENLABS_API_KEY` | Yes | `""` | ElevenLabs API key |
| `ELEVENLABS_VOICE_ID` | No | `21m00Tcm4TlvDq8ikWAM` | Voice profile ID (Rachel) |
| `SUPABASE_URL` | Yes | `""` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | `""` | Supabase backend access key |
| `STORE_RAW_TRANSCRIPTS` | No | `false` | Keep raw (unredacted) transcripts |
| `WANDB_API_KEY` | For tracing | N/A | W&B Weave API key (planned) |

### Configuration Loading

- Config file: `app/config.py`
- Env file location: `../../.env` (relative to `services/api/app/`)
- Loaded by: Pydantic v2 `BaseSettings` with `model_config = SettingsConfigDict(env_file='../../.env')`
- Singleton: `settings = Settings()` at module level
- Access: `from app.config import settings` then `settings.mistral_api_key`

---

## 10. Known Issues & TODOs


### Critical Issues (Blocking Features)

1. **`generate_agent_reply()` is a STUB** (`twilio_voice/routes.py:36`)
   - Returns: `"I heard you say: {transcript}"` (echo)
   - Should call: `agent/loop.py::run_turn()` with Mistral LLM
   - Impact: Agent responses are NOT intelligent during live calls
   - Status: User chose to address separately from optimization plan

2. **Two separate session systems** not connected
   - `agent/memory.py::SessionStore` — LLM context (message history)
   - `twilio_voice/session.py::CallSessionData` — streaming pipeline data
   - They don't share data. Wiring them is needed for full agent integration.

3. **Missing DB functions** in `db/queries.py`
   - `get_scenario()`, `get_turns_for_call()`, `create_analysis()` are called but don't exist
   - Blocks: post-call analysis pipeline

4. **Turns not persisted during stream** (`routes.py:434, 463`)
   - User and agent turns only exist in-memory during the call
   - If call crashes, all conversation data is lost
   - TODO: Write to DB via create_turn()

5. **Synchronous DB in async context** (`routes.py:565`)
   - `_update_call_safe()` uses sync Supabase client in async handlers
   - Can block the event loop
   - TODO: Use asyncio.to_thread() or async DB client

### Non-Critical TODOs

6. **`twilio_call_sid` column** (`routes.py:82, 547`)
   - Current lookup uses most recent 'ringing' call (unreliable for concurrent calls)
   - Need: proper indexed column in calls table

7. **Recording metadata not persisted** (`routes.py:207`)
   - /twilio/recording webhook logs but doesn't save to DB

8. **Post-call analysis not triggered** (`routes.py:171`)
   - /twilio/status should call run_post_call_analysis() but doesn't

9. **Session cleanup persistence** (`routes.py:523`)
   - Stream cleanup logs summary but doesn't persist turns/metrics/errors

---

## 11. Future Capabilities


### RAG (Retrieval-Augmented Generation)

Currently not implemented, but could enhance agent effectiveness:
- **Employee data retrieval**: Pull employee's department, past call history, role-specific info
- **Knowledge base**: Company policy documents the agent can reference during calls
- **Attack playbooks**: Retrieve relevant attack techniques based on scenario type
- **Implementation**: Use Mistral's function calling + a vector store (Supabase pgvector or external)

### Mistral Function Calling / Tool Use

Mistral supports function calling which could enable:
- **Live data lookup**: Agent queries employee DB during call
- **Escalation triggers**: Agent calls a function when certain conditions are met
- **Scoring during call**: Real-time risk assessment as the call progresses
- **Implementation**: Add tool definitions to chat_completion() messages, handle tool_calls in response

### Voxtral (Mistral's Voice Model)

Mistral offers Voxtral for speech-to-text:
- **Voxtral Mini Transcribe V2**: Batch STT with speaker diarization, word timestamps, 13 languages, up to 3 hours
- **Voxtral Realtime**: Live STT with sub-200ms latency, streaming, open weights (Apache 2.0)
- **Current decision**: Keep ElevenLabs STT (already integrated and working)
- **Future option**: Replace ElevenLabs STT with Voxtral Realtime for an all-Mistral stack
- **Note**: Voxtral is STT ONLY — you still need ElevenLabs (or another provider) for TTS

### Multi-Agent Scenarios

Future capability for complex simulations:
- **Multiple AI agents**: Different personas calling the same target
- **Coordinated attacks**: Sequential calls building on previous interactions
- **Red team simulation**: Full campaign with varying attack vectors

### Streaming Chat Completions

Planned in the optimization work plan (Task 5):
- **Currently**: Wait for full Mistral response before TTS
- **Planned**: Stream tokens as they arrive, start TTS on first sentence
- **Benefit**: Reduces perceived latency by ~500-1000ms
- **Implementation**: `client.chat.stream()` with sentence boundary detection

### Advanced Tracing

Beyond basic W&B Weave:
- **Audio evaluation**: Score recorded calls automatically
- **A/B testing**: Compare different prompts/models on same scenarios
- **Cost tracking**: Per-call cost analysis (LLM tokens + TTS + STT)
- **Alerting**: Set up alerts for high-risk scores or errors

---

## 12. Optimization Plan Reference

The existing work plan at `.sisyphus/plans/agent-optimization-tracing.md` covers:

1. **Task 1**: Migrate `integrations/mistral.py` from raw httpx to `mistralai` SDK v1+ with streaming
2. **Task 2**: Add W&B Weave tracing (`weave.init()` + `@weave.op()` on all agent functions)
3. **Task 3**: Enhance system prompts with dynamic Script/Caller data injection
4. **Task 4**: Token-aware memory management in `agent/memory.py`
5. **Task 5**: Create separate `chat_completion_stream()` for real-time voice latency
6. **Task 6**: Minimal smoke tests

To execute: run `/start-work` to begin the optimization work.
