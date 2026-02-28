# Canard Architecture Analysis

> Generated 2026-02-28 — reflects the current codebase state after consent-flow removal.
> Mistral LLM is **not connected**; a clean stub exists for future integration.

---

## 1. Architecture Summary (No Mistral)

Canard is a real-time voice-based social-engineering simulation platform. The current architecture implements a **bidirectional streaming voice pipeline** where:

- **Twilio** handles telephony — outbound call initiation, Media Streams WebSocket for real-time bidirectional audio, status callbacks for call lifecycle events.
- **ElevenLabs** provides voice capabilities — Realtime STT (WebSocket, VAD auto-commit) for live transcription, TTS (`ulaw_8000` format) for agent speech synthesis, and batch STT (Scribe v1) for post-call recording transcription.
- **Supabase** (PostgreSQL) persists all state — participants, scenarios, campaigns, calls, turns, and analysis results.
- **FastAPI** orchestrates everything — Twilio webhook handlers, WebSocket endpoint, REST API for the dashboard, and media serving.
- **Mistral** is **not connected** — a deterministic stub (`generate_agent_reply()`) echoes user input for end-to-end pipeline testing. The stub has a documented replacement path.

### Component Map

| Component | Role | File(s) |
|-----------|------|---------|
| FastAPI app | HTTP server, routing, CORS, lifespan | `app/main.py` (59 lines) |
| Config | Environment variables via pydantic-settings | `app/config.py` (36 lines) |
| Twilio webhooks | `/voice`, `/gather`, `/status` HTTP handlers | `app/twilio_voice/routes.py` (lines 67–225) |
| Twilio WebSocket | `/stream` bidirectional Media Stream | `app/twilio_voice/routes.py` (lines 233–457) |
| Twilio REST client | Outbound call initiation | `app/twilio_voice/client.py` (41 lines) |
| TwiML generators | XML response builders | `app/twilio_voice/twiml.py` (138 lines) |
| ElevenLabs TTS | Text → `ulaw_8000` audio bytes (SDK) | `app/integrations/elevenlabs.py` (lines 68–107) |
| ElevenLabs Realtime STT | Live audio → committed transcripts (raw WS) | `app/integrations/elevenlabs.py` (lines 175–331) |
| ElevenLabs Batch STT | Recording URL → transcript (SDK) | `app/integrations/elevenlabs.py` (lines 140–172) |
| Agent stub | Deterministic echo reply (no LLM) | `app/twilio_voice/routes.py` (lines 42–59) |
| Agent loop (unused) | Mistral chat completion loop | `app/agent/loop.py` (53 lines) |
| Session store | In-memory call session state | `app/agent/memory.py` (65 lines) |
| Prompts | System prompt builder, greeting constants | `app/agent/prompts.py` (34 lines) |
| Call lifecycle | Start, update, complete call operations | `app/services/calls.py` (103 lines) |
| Post-call analysis | Risk scoring via Mistral (when connected) | `app/services/analysis.py` (66 lines) |
| Media store | In-memory audio blob storage | `app/services/media.py` (27 lines) |
| DB queries | Supabase CRUD for all tables | `app/db/queries.py` (172 lines) |
| PII redaction | Regex-based sensitive data masking | `app/agent/redaction.py` |

---

## 2. End-to-End Call Flow (Step-by-step)

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌───────────┐     ┌──────────┐
│ Dashboard │────▶│ FastAPI  │────▶│  Twilio  │────▶│ Callee's  │     │ Supabase │
│           │     │ Backend  │◀───▶│  Cloud   │     │  Phone    │     │    DB    │
└──────────┘     └────┬─────┘     └────┬─────┘     └───────────┘     └──────────┘
                      │                │
                      │    ┌───────────┴───────────┐
                      │    │  Media Stream (WSS)    │
                      │    │  Bidirectional Audio   │
                      │    └───────────┬───────────┘
                      │                │
                 ┌────┴────┐     ┌────┴────┐
                 │Eleven   │     │ Agent   │
                 │Labs API │     │ Stub    │
                 │TTS + STT│     │(Mistral)│
                 └─────────┘     └─────────┘
```

### Step-by-step flow:

1. **Dashboard triggers call** — `POST /api/calls/start` with `participant_id` and `scenario_id`.
   - `services/calls.py:start_call()` (line 16) validates participant opt-in and scenario existence.
   - Creates call record in Supabase with status `pending`.
   - Calls `twilio_voice/client.py:make_outbound_call()` (line 22) which uses `Client.calls.create()`.
   - Updates call status to `ringing` with `twilio_call_sid`.

2. **Twilio connects** — When callee answers, Twilio sends POST to `/twilio/voice`.
   - `routes.py:twilio_voice()` (line 67) receives `CallSid` and `CallStatus`.
   - Looks up call record via `get_or_create_call_for_webhook(CallSid)` → `queries.get_call_by_sid()`.
   - If no call record found → returns `say_and_hangup("An error occurred. Goodbye.")`.
   - Updates call: `{"consented": True, "status": "in-progress"}`.
   - Returns `twiml.stream_response(call_id)` — TwiML with `<Say>` greeting + `<Connect><Stream>`.

3. **Caller hears greeting** — Twilio executes the `<Say>` TwiML:
   - `STREAM_GREETING`: "Hello, this is a security awareness training exercise. Let's begin."
   - Defined in `agent/prompts.py` (line 12), used in `twiml.py:stream_response()` (line 131).

4. **WebSocket opens** — Twilio opens WSS connection to `/twilio/stream`.
   - `routes.py:twilio_stream()` (line 234) accepts the WebSocket.
   - **Phase 1 — Handshake** (lines 270–316): Consumes `connected` and `start` messages.
   - Extracts `stream_sid` and `call_id` from `start.customParameters.call_id`.
   - Validates call record exists in Supabase.

5. **Bidirectional audio streaming begins** — Phase 2 (lines 324–457):
   - Two concurrent async tasks: `_receive_twilio()` and `_agent_loop()`.
   - `_receive_twilio()` (line 329): Reads Twilio `media` messages, base64-decodes μ-law audio, puts chunks into `audio_queue`. Also handles `stop`, `mark`, and `dtmf` events.
   - `_agent_loop()` (line 366): Consumes from `audio_queue` via ElevenLabs Realtime STT.

6. **Caller speaks → STT** — Audio flows through ElevenLabs Realtime STT:
   - `elevenlabs.py:realtime_stt_session()` (line 175) opens WSS to `wss://api.elevenlabs.io/v1/speech-to-text/realtime`.
   - Audio format: `ulaw_8000`, commit strategy: `vad` (auto-commit on silence).
   - Yields `committed_transcript` strings when caller finishes a sentence.

7. **Agent generates reply** — `_agent_loop()` calls `generate_agent_reply(call_id, transcript)`:
   - **Current stub** (line 42): Returns `"I heard you say: {transcript}. Is there anything else you'd like to discuss?"`.
   - **Future**: Replace body with `return await run_turn(call_id, transcript)` to use Mistral.

8. **TTS → Caller hears agent** — Agent text is synthesized:
   - `elevenlabs.py:text_to_speech()` (line 68) converts text → `ulaw_8000` bytes via AsyncElevenLabs SDK.
   - Audio is base64-encoded and sent back over the WebSocket as a Twilio `media` message.
   - A `mark` message follows for playback tracking (lines 423–435).

9. **Turn persistence** — Each user and agent turn is saved:
   - `_save_turn()` (line 464) applies PII redaction via `redact_pii()`.
   - Stores `text_redacted` (always) and optionally `text_raw` (if `STORE_RAW_TRANSCRIPTS=true`).
   - Writes to Supabase `turns` table via `queries.create_turn()`.

10. **Repeat** — Steps 6–9 loop until the caller hangs up or the WebSocket closes.

11. **Call ends** — Twilio sends POST to `/twilio/status` with `CallStatus=completed`.
    - `routes.py:twilio_status()` (line 179) receives the callback.
    - If `RecordingUrl` is present, transcribes via `speech_to_text_from_url()` (ElevenLabs batch STT).
    - Calls `handle_call_completed()` which:
      - Updates call status to `completed` with `ended_at` timestamp.
      - Ends the agent session (`end_session(call_id)`).
      - Runs `run_post_call_analysis()` for risk scoring (requires Mistral — currently a no-op without API key).

---

## 3. Option 2 Compliance Checklist

**Option 2**: "Use Mistral directly as your agent 'brain,' and ElevenLabs only for TTS/STT."

| # | Requirement | Pass/Fail | Evidence | Fix (if needed) |
|---|-------------|-----------|----------|-----------------|
| 1 | **Mistral as agent brain** | ⚠️ STUB | `generate_agent_reply()` at `routes.py:42` is a deterministic echo. `agent/loop.py` has full Mistral integration via `chat_completion()` but is not wired to the streaming flow. | Replace stub body with `return await run_turn(call_id, transcript)`. See Section 4. |
| 2 | **ElevenLabs only for TTS/STT** | ✅ PASS | `elevenlabs.py` provides TTS (line 68), Realtime STT (line 175), and batch STT (line 140). No ElevenLabs Agents runtime. No ElevenLabs conversational AI. | — |
| 3 | **Maximum control over behavior** | ✅ PASS | All conversation logic is in `routes.py:_agent_loop()`. System prompt is fully customizable in `agent/prompts.py:build_system_prompt()`. PII redaction in `agent/redaction.py`. Turn persistence with redaction. | — |
| 4 | **Maximum control over logging** | ✅ PASS | Python `logging` throughout. Every stage logged: webhook entry, WebSocket events, STT transcripts, agent replies, TTS generation, turn persistence, errors. | — |
| 5 | **Maximum control over guardrails** | ✅ PASS | Safety guardrails in system prompt (lines 22–26 of `prompts.py`). PII redaction before persistence. `STORE_RAW_TRANSCRIPTS` flag defaults to `false`. | — |
| 6 | **Maximum control over analytics** | ✅ PASS | Every turn persisted to Supabase with role, redacted text, turn index. Post-call analysis with risk scoring. Recording transcription for richer analysis. | — |
| 7 | **Tight Twilio webhook integration** | ✅ PASS | `/twilio/voice` (entry), `/twilio/gather` (fallback), `/twilio/status` (lifecycle), `/twilio/stream` (WebSocket). Status callback handles `completed` with recording transcription. | — |
| 8 | **Recording callbacks** | ✅ PASS | `twilio_status()` at `routes.py:179` checks `RecordingUrl`, transcribes via ElevenLabs batch STT, passes to `handle_call_completed()`. | — |
| 9 | **Clean FastAPI backend** | ✅ PASS | Modular layout: `twilio_voice/`, `services/`, `agent/`, `db/`, `integrations/`, `models/`, `routes/`. Pydantic settings. CORS enabled. Health endpoint. | — |
| 10 | **Dashboard reads from backend** | ✅ PASS | REST endpoints: `GET /api/calls/`, `GET /api/calls/{id}`, `GET /api/campaigns/`, `POST /api/calls/start`. All read from Supabase. | — |
| 11 | **`ulaw_8000` audio format** | ✅ PASS | TTS: `output_format="ulaw_8000"` at `elevenlabs.py:96`. STT: `audio_format=ulaw_8000` in WebSocket URL at `elevenlabs.py:218`. Media endpoint: `audio/basic` MIME type at `main.py:52`. | — |
| 12 | **`commit_strategy=vad`** | ✅ PASS | `commit_strategy=vad` in Realtime STT WebSocket URL at `elevenlabs.py:219`. Client sends `"commit": False` — VAD handles auto-commit. | — |
| 13 | **No query params in Stream URL** | ✅ PASS | `twiml.py:stream_response()` (line 134) uses `<Parameter>` TwiML noun. `call_id` extracted from `start.customParameters` at `routes.py:296`. | — |
| 14 | **Bidirectional Media Stream** | ✅ PASS | `<Connect><Stream>` TwiML at `twiml.py:133-136`. WebSocket handler at `routes.py:234`. Sends `media` messages back with base64 audio at `routes.py:410-422`. | — |
| 15 | **No consent gather in primary flow** | ✅ PASS | `/twilio/voice` goes directly to `stream_response(call_id)` at `routes.py:84`. No `<Gather>` in the streaming path. | — |

**Summary**: 14/15 requirements PASS. 1 requirement (Mistral as agent brain) is a documented STUB ready for plug-in.

---

## 4. Where to Plug in Mistral Later

### Primary integration point

**File**: `services/api/app/twilio_voice/routes.py`
**Function**: `generate_agent_reply()` (lines 42–59)

```python
# CURRENT (stub):
async def generate_agent_reply(call_id: str, transcript: str) -> str:
    if not transcript.strip():
        return "Sorry, I didn't catch that. Could you please repeat?"
    return f"I heard you say: {transcript}. Is there anything else you'd like to discuss?"

# FUTURE (with Mistral):
async def generate_agent_reply(call_id: str, transcript: str) -> str:
    from app.agent import run_turn
    return await run_turn(call_id, transcript)
```

**Input**: `call_id` (str) — internal UUID, `transcript` (str) — user's spoken text from STT.
**Output**: `str` — agent's text response, sent to ElevenLabs TTS.

### Session initialization

Before `generate_agent_reply()` can use `run_turn()`, the agent session must be initialized. This code is already written but commented out in the `/twilio/gather` consent handler (`routes.py` lines 121–130). For the streaming flow, add equivalent initialization in `/twilio/voice` or at the start of `_agent_loop()`:

```python
# In /twilio/voice handler, after updating call status:
scenario = queries.get_scenario(call["scenario_id"])
if scenario:
    system_prompt = build_system_prompt(
        scenario["name"], scenario["script_guidelines"]
    )
    await start_session(call_id, call["scenario_id"], system_prompt)
```

### Step-by-step connection guide

1. **Create `app/integrations/mistral.py`** — Implement `chat_completion(messages: list[dict]) -> str` using the Mistral API. `agent/loop.py` (line 9) already imports `from app.integrations.mistral import chat_completion`.

2. **Set `MISTRAL_API_KEY`** in `.env`. Config already reads it: `config.py` line 15.

3. **Initialize session in `/twilio/voice`** — Add the session initialization code above, after `queries.update_call(call_id, ...)` at `routes.py` line 83.

4. **Replace stub body** — Change `generate_agent_reply()` to call `run_turn()` as shown above.

5. **Test** — The `_agent_loop()` call-site at `routes.py` line 390 already `await`s `generate_agent_reply()`, so no signature change is needed.

### Existing Mistral infrastructure (ready but unused)

| File | What it does | Status |
|------|-------------|--------|
| `agent/loop.py:run_turn()` | Manages conversation history, calls `chat_completion()`, trims messages | Ready — needs `mistral.py` |
| `agent/loop.py:start_session()` | Creates `CallSession` with system prompt | Ready |
| `agent/loop.py:end_session()` | Cleans up session, returns history | Ready |
| `agent/memory.py:SessionStore` | Thread-safe in-memory session storage | Ready |
| `agent/memory.py:CallSession` | Dataclass with messages, turn_count, max_turns | Ready |
| `agent/prompts.py:build_system_prompt()` | Generates scenario-specific system prompt with safety guardrails | Ready |
| `agent/redaction.py:redact_pii()` | Regex PII masking before LLM input | Ready |
| `services/analysis.py:run_post_call_analysis()` | Post-call risk scoring (needs Mistral) | Ready — needs `mistral.py` |

---

## 5. Top 5 Risks

| # | Risk | Symptom | Why It Matters | How to Verify |
|---|------|---------|----------------|---------------|
| 1 | **ElevenLabs Realtime STT WebSocket drops** | `_agent_loop()` silently stops yielding transcripts. Caller speaks but agent never responds. No error logged if the WS closes cleanly. | The entire conversation loop depends on this single WebSocket. A drop means the call goes silent with no recovery. | Monitor logs for `"ElevenLabs Realtime STT error"` messages. Add a heartbeat/timeout: if no `committed_transcript` arrives within N seconds of audio being sent, log a warning and attempt reconnection. Currently no reconnection logic exists (`elevenlabs.py` line 280 — `break` on error, no retry). |
| 2 | **Latency budget exceeded** | Caller experiences >2s silence between speaking and hearing the agent. Feels unnatural, caller may hang up. | The pipeline is serial: STT commit → `generate_agent_reply()` → TTS → Twilio playback. Each step adds latency. ElevenLabs TTS with `optimize_streaming_latency=3` helps, but Mistral API latency (when connected) could push total >2s. | Measure round-trip time from `committed_transcript` log to `media` send log. Target: <1.5s for stub, <2.5s with Mistral. Consider streaming TTS (send chunks as they arrive) instead of waiting for full audio. |
| 3 | **In-memory state loss on restart** | `SessionStore` (`agent/memory.py`) and `_audio_store` (`services/media.py`) are Python dicts. Server restart = all active call sessions lost. Callers on active calls get no agent responses. | Hackathon-acceptable but production-dangerous. Any deployment, crash, or auto-restart wipes all state. | Check: `_audio_store` at `media.py:8` and `_sessions` at `memory.py:19` are plain dicts. For production: persist to Redis or Supabase. For now: document as known limitation. |
| 4 | **No call record for inbound CallSid** | `/twilio/voice` returns `say_and_hangup("An error occurred. Goodbye.")` at `routes.py:78`. Caller hears error and call ends. | This happens when Twilio calls back but no matching call record exists in Supabase (e.g., call was created but DB write failed, or CallSid mismatch). The `get_or_create_call_for_webhook()` function (`calls.py:102`) only does a lookup — it does NOT create. Despite its name, it's just `queries.get_call_by_sid()`. | Test: trigger a call, verify Supabase has the record before Twilio callback arrives. Rename `get_or_create_call_for_webhook` to `get_call_for_webhook` to avoid confusion, or implement actual create-on-miss logic. |
| 5 | **Audio format mismatch** | Caller hears static, garbled audio, or silence instead of agent speech. | If TTS returns non-μ-law audio, or if base64 encoding includes file headers, Twilio will play garbage. The `audio/basic` MIME type on the `/media/` endpoint (`main.py:52`) may not be recognized by Twilio `<Play>` in the fallback gather flow. | Verify: `_TWILIO_OUTPUT_FORMAT = "ulaw_8000"` at `elevenlabs.py:35`. Verify: no WAV/MP3 headers in TTS output (ElevenLabs `ulaw_8000` returns raw samples). Test: make a real call and confirm audio quality. The streaming flow sends raw base64 directly over WebSocket (correct), but the fallback `<Play>` flow serves via HTTP (may need `audio/x-mulaw` MIME type instead of `audio/basic`). |
