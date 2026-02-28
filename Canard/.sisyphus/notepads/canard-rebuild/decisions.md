# Canard Rebuild Decisions

## 2025-02-28 Initial Architecture
- Supabase sync client (not async) — simpler, supabase-py async is less mature
- Twilio Python helper for call creation + TwiML generation
- httpx async for Mistral and ElevenLabs (no SDK)
- In-memory dict for audio media storage (hackathon-simple, served via GET /media/{id})
- Regex-based PII redaction (emails, phones, SSNs, credit cards, MFA codes)
- Risk scoring via Mistral post-call analysis
- Turn-based conversation: Gather → Agent → TTS → Play → Gather loop

## 2026-02-28 Runtime Wiring
- Keep service boundaries thin: dashboard routes call `app/services/*`, while Twilio webhooks orchestrate call/session flow without adding DB-layer changes.
- Keep campaign listing as a local Supabase query in service layer until a dedicated `queries.list_campaigns` helper is introduced.

## 2026-02-28 Delivery Hardening
- Use `services/api/docker-compose.yml` with a single `api` service and `env_file: ../../.env` so local runtime behavior matches existing config path assumptions.
- Keep `.dockerignore` explicit (`.venv`, tests, pycache, env, git metadata) to reduce build context and avoid leaking local files into images.
- Keep health test minimal and dependency-safe by asserting response contract only (`status`, `timestamp`) instead of hitting DB-backed endpoints.
