# Canard

Canard is a voice-based social-engineering simulation platform built for hackathon delivery speed.
The system places realistic training calls, records participant responses,
applies LLM-based analysis, and returns coaching-oriented risk signals.

This repository is now packaged for local development,
test execution, and containerized deployment from the same codebase.

## What is Canard

Canard helps teams run controlled phishing-via-phone simulations.
It is designed for security awareness programs,
red-team style training campaigns,
and rapid experimentation with conversational safety tooling.

Core outcomes:

- automated outbound call orchestration;
- consent-aware Twilio voice interactions;
- transcript handling with PII redaction;
- post-call risk scoring and coaching notes;
- API-first access for dashboards and automation scripts.

## Architecture

Canard is a monorepo with a Python API backend and a web dashboard frontend.
The backend coordinates Twilio webhooks,
Mistral reasoning,
ElevenLabs TTS,
and Supabase persistence.

Architecture overview:

```
┌──────────┐      ┌───────────┐      ┌────────────┐
│ Dashboard │─────▶│  FastAPI   │─────▶│  Supabase  │
│ (Frontend)│      │  Backend   │      │  (Postgres) │
└──────────┘      └─────┬─────┘      └────────────┘
                        │
              ┌─────────┼─────────┐
              ▼         ▼         ▼
         ┌────────┐ ┌────────┐ ┌──────────┐
         │ Twilio │ │Mistral │ │ElevenLabs│
         │ Voice  │ │  LLM   │ │   TTS    │
         └────────┘ └────────┘ └──────────┘
```

High-level data flow:

1. Dashboard triggers call creation through FastAPI.
2. FastAPI starts outbound call through Twilio.
3. Twilio webhooks drive conversation turns in real time.
4. User utterances are redacted before persistence.
5. Agent responses are synthesized with ElevenLabs and replayed to the callee.
6. Completion events trigger analysis and risk summary storage.

## Call Lifecycle

Each call follows a deterministic lifecycle for reliability:

1. `pending` on call object creation.
2. Twilio connects and requests `/twilio/voice`.
3. Consent prompt is played.
4. `/twilio/gather` receives speech/digits and updates `consented`.
5. Agent session initializes with scenario-specific prompt.
6. User turns and agent turns continue with gather/play loops.
7. `/twilio/status` updates terminal state.
8. On `completed`, analysis is generated and attached to call.

State transitions are persisted by backend services,
allowing dashboards to query status and risk in near real-time.

## Risk Scoring

Risk scoring is attached to each analyzed call.
The score represents training concern level,
not a punitive employee metric.

Typical score interpretation:

- `0-30`: low risk, participant resisted attack patterns;
- `31-60`: medium risk, partial disclosure or delayed resistance;
- `61-100`: high risk, direct compliance with social-engineering prompts.

Flag examples returned by analysis:

- credential disclosure intent;
- urgency-pressure susceptibility;
- callback verification omitted;
- policy bypass statements.

Coaching guidance is generated alongside numeric scoring
to keep outcomes action-oriented for training teams.

## Tech Stack

Backend:

- Python 3.11;
- FastAPI + Uvicorn;
- Pydantic v2 + pydantic-settings;
- Supabase Python SDK;
- Twilio Voice webhook integration;
- Mistral LLM API;
- ElevenLabs TTS API.

Frontend/workspace:

- Next.js + React (dashboard app);
- TypeScript workspace packages;
- pnpm monorepo tooling.

Operations:

- multi-stage Docker image for API service;
- docker-compose for local container deployment;
- pytest test suite for backend behavior checks.

## Project Structure

```
Canard/
├── .env.example
├── .gitignore
├── README.md
├── apps/
│   └── web/
├── packages/
│   └── shared/
├── services/
│   └── api/
│       ├── Dockerfile
│       ├── docker-compose.yml
│       ├── .dockerignore
│       ├── requirements.txt
│       ├── tests/
│       │   ├── __init__.py
│       │   ├── conftest.py
│       │   ├── test_redaction.py
│       │   ├── test_models.py
│       │   └── test_health.py
│       └── app/
│           ├── main.py
│           ├── config.py
│           ├── agent/
│           ├── db/
│           ├── models/
│           ├── routes/
│           ├── services/
│           └── twilio_voice/
└── pnpm-workspace.yaml
```

## Prerequisites

Required runtime tools:

- Python 3.11+
- pip
- Node.js 18+
- pnpm
- Docker Desktop (for container workflow)

External service credentials:

- Twilio account SID/auth token/phone number
- Mistral API key
- ElevenLabs API key (voice synthesis)
- Supabase URL and service role key

## Environment Variables

Canard API reads environment from repository root `.env`.
Path resolution is configured in `services/api/app/config.py`.

| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `TWILIO_ACCOUNT_SID` | Yes for real calls | `""` | Twilio project identifier |
| `TWILIO_AUTH_TOKEN` | Yes for real calls | `""` | Twilio auth secret |
| `TWILIO_FROM_NUMBER` | Yes for outbound calls | `""` | Verified Twilio number |
| `PUBLIC_BASE_URL` | Yes for webhooks in production | `http://localhost:8000` | Public HTTPS URL for Twilio callbacks |
| `MISTRAL_API_KEY` | Yes for agent replies | `""` | Mistral API credential |
| `MISTRAL_BASE_URL` | No | `https://api.mistral.ai` | Override for proxy/self-hosted gateway |
| `MISTRAL_MODEL` | No | `mistral-small-latest` | Model used for runtime turns |
| `ELEVENLABS_API_KEY` | Yes for TTS | `""` | ElevenLabs credential |
| `ELEVENLABS_VOICE_ID` | No | `21m00Tcm4TlvDq8ikWAM` | Voice profile ID |
| `SUPABASE_URL` | Yes for persistence | `""` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes for persistence | `""` | Backend DB access key |
| `STORE_RAW_TRANSCRIPTS` | No | `false` | Keep raw text only if policy allows |
| `PORT` | No | `8000` | API listener port |

Minimal local `.env` bootstrap:

```env
PORT=8000
PUBLIC_BASE_URL=http://localhost:8000
MISTRAL_API_KEY=replace-me
ELEVENLABS_API_KEY=replace-me
SUPABASE_URL=replace-me
SUPABASE_SERVICE_ROLE_KEY=replace-me
```

## Database Setup

Canard expects Supabase tables for participants,
scenarios,
campaigns,
calls,
turns,
and analysis output.

Suggested setup process:

1. Create a Supabase project.
2. Capture `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
3. Create schema/tables used by backend query functions.
4. Seed at least one participant and scenario for start-call testing.
5. Verify backend can fetch/create records through `/api/calls/start`.

Validation tip:

- If credentials are missing,
  backend operations that touch DB intentionally fail fast
  with a clear `SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required` error.

## Local Development

From repository root:

```bash
cp .env.example .env
```

Set up API virtual environment:

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run API service:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Optional dashboard workflow in a second terminal:

```bash
pnpm install
pnpm dev:web
```

Health check:

```bash
curl http://localhost:8000/health
```

## Docker Deployment

API Docker artifacts live in `services/api/`.
The image is multi-stage to keep final runtime light
while preserving dependency cache behavior.

Build API image:

```bash
cd services/api
docker build -t canard-api:local .
```

Run API container directly:

```bash
docker run --rm -p 8000:8000 --env-file ../../.env canard-api:local
```

Run with compose:

```bash
cd services/api
docker compose up --build
```

Stop compose stack:

```bash
docker compose down
```

Container healthcheck target:

- `GET /health` on internal port `8000` via `curl`.

## API Endpoints

Canard exposes ten primary endpoints used by dashboard/webhooks.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness check with timestamp |
| `POST` | `/api/calls/start` | Start a new call for participant/scenario |
| `GET` | `/api/calls/` | List calls with optional filters |
| `GET` | `/api/calls/{call_id}` | Retrieve detailed call data |
| `POST` | `/api/campaigns/` | Create campaign |
| `GET` | `/api/campaigns/` | List campaigns |
| `GET` | `/api/campaigns/{campaign_id}` | Fetch campaign details |
| `POST` | `/twilio/voice` | Twilio entry webhook for consent prompt |
| `POST` | `/twilio/gather` | Twilio gather webhook for turns/consent |
| `POST` | `/twilio/status` | Twilio status callback for completion updates |

Reference-only media route:

- `GET /media/{media_id}` serves generated audio clips.

## Twilio Webhook Setup

To connect Twilio Voice to a local environment,
use a tunnel (for example ngrok or Cloudflare Tunnel)
that exposes your local API.

Required webhook mapping:

- Voice URL: `https://<public-host>/twilio/voice`
- Status Callback URL: `https://<public-host>/twilio/status`

Behavior notes:

- `/twilio/voice` returns TwiML consent gather.
- `/twilio/gather` executes conversation loop and returns playable TwiML.
- `/twilio/status` finalizes state and triggers analysis on completion.

If callbacks fail:

1. Confirm `PUBLIC_BASE_URL` points to the reachable HTTPS origin.
2. Confirm Twilio number is configured for voice webhooks.
3. Confirm API logs show incoming `CallSid` values.

## curl Testing Examples

The following examples assume API running on `localhost:8000`.

```bash
# Start a call
curl -X POST http://localhost:8000/api/calls/start \
  -H "Content-Type: application/json" \
  -d '{"participant_id": "uuid-here", "scenario_id": "uuid-here"}'

# List calls
curl http://localhost:8000/api/calls/

# Get call detail
curl http://localhost:8000/api/calls/{call_id}
```

Campaign creation:

```bash
curl -X POST http://localhost:8000/api/campaigns/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Q1 Security Drill", "scenario_id": "uuid-here", "created_by": "security-team"}'
```

Health endpoint:

```bash
curl http://localhost:8000/health
```

## Running Tests

Run backend tests from `services/api/` using the project venv:

```bash
cd services/api
source .venv/bin/activate
python -m pytest tests/ -v
```

Current suite focus:

- redaction behavior for sensitive patterns;
- model validation/default values;
- health endpoint response contract.

Test design principle:

- no test should require live Twilio,
  live Mistral,
  or live Supabase credentials.

## Safety & Ethics

Canard is intended for authorized training and resilience exercises only.
Do not use this system for deception outside explicit,
documented consent and governance processes.

Recommended safeguards:

- obtain organizational authorization before any campaign;
- clearly define participant privacy and retention policy;
- default to redacted transcript storage;
- avoid collecting unnecessary personal data;
- keep audit logs for campaign configuration and operator actions;
- include opt-out and debrief procedures in campaign design.

Responsible usage boundaries:

- no credential harvesting for real production accounts;
- no calls to personal devices without policy approval;
- no hidden punitive scoring against individuals.

## License

No explicit license file is currently present in this repository.
Until a `LICENSE` file is added,
all rights are reserved by the project authors.

For hackathon demo sharing,
add a license file (for example MIT or Apache-2.0)
before external redistribution.
