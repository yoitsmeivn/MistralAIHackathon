# Canard Rebuild Learnings

## Existing Codebase Patterns
- pyright: basic comment at top of files
- httpx async client for external API calls (not SDK)
- pydantic-settings for config with env_file pointing to ../../.env
- camelCase in Pydantic API models for frontend compatibility
- FastAPI with lifespan context manager
- CORS middleware with allow_origins=["*"]

## Twilio Python Patterns (from docs)
- `from twilio.rest import Client` → `Client(account_sid, auth_token)`
- Outbound: `client.calls.create(to=..., from_=..., url=..., status_callback=..., status_callback_event=[...])`
- TwiML: `from twilio.twiml.voice_response import VoiceResponse, Gather`
- Gather: `response.gather(input="speech dtmf", action="/twilio/gather", method="POST")`
- Webhook params: SpeechResult, CallSid, Digits, CallStatus
- Return TwiML as XML string with content-type application/xml

## Supabase Python Patterns (from docs)
- `from supabase import create_client, Client`
- `supabase = create_client(url, key)` — sync client
- Insert: `supabase.table("name").insert({...}).execute()`
- Select: `supabase.table("name").select("*").eq("field", val).execute()`
- Update: `supabase.table("name").update({...}).eq("field", val).execute()`
- Delete: `supabase.table("name").delete().eq("field", val).execute()`
- Response: `response.data` for list of dicts
- Use service_role_key for server-side (bypasses RLS)

## Architecture Decisions
- Keep services/api/ as the Python backend root
- Frontend (apps/web/) stays untouched
- SQL migrations in services/api/migrations/
- Docker files at services/api/ level
- Media files served from in-memory dict with UUID keys

## Rebuild Task Learnings
- Rebuilt `services/api/app/` into package-based layout (`models/`, `db/`, `integrations/`, placeholders) to support modular growth.
- Set `PORT=8000` and `PUBLIC_BASE_URL`/Twilio/Supabase defaults in `.env.example` and `app.config.Settings` for consent-call flow.
- Supabase access uses sync `create_client` singleton in `app/db/client.py`; query helpers centralized with `_execute` + safe `response.data` handling.
- Integration layer uses async `httpx` for both Mistral chat+analysis JSON extraction and ElevenLabs MP3 generation (no SDK usage).
- Initial SQL migration now defines all required tables, constraints, and indexes, including `gen_random_uuid()` keys and analysis risk checks.
- Backend runtime wiring now routes Twilio voice webhooks (`/twilio/voice`, `/twilio/gather`, `/twilio/status`) through form-encoded handlers that persist turns and drive agent + TTS loop responses.
- Added in-memory media service (`app/services/media.py`) and `GET /media/{media_id}` for Twilio playback URLs derived from `PUBLIC_BASE_URL`.

## 2026-02-28 Shippable Artifacts
- Multi-stage Docker image pattern now caches `requirements.txt` install in builder stage and keeps runtime slim with only `/usr/local` dependencies copied forward.
- API test suite can stay integration-free by targeting pure units (`redact_pii`, Pydantic models) and only using `TestClient` against `/health` endpoint.
- basedpyright in this repo is strict enough that test files benefit from `# pyright: reportMissingImports=false` to avoid environment-specific missing import noise.
- Root README can be used as deployment playbook; hackathon handoff quality improved by including endpoint table, call lifecycle, Twilio setup, and exact curl snippets.
