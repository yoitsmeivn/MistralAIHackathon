# Canard Platform — Usage Guide

Canard is a vishing (voice phishing) simulation platform for security awareness training. It places automated AI-driven phone calls to employees, simulating social engineering attacks, then scores their responses.

---

## Core Entities

### Callers

**Purpose:** Identity/persona only — who the AI agent *is* during a call.

| Field | Description |
|-------|-------------|
| `persona_name` | Display name the agent introduces itself as |
| `persona_role` | Job title the agent claims (e.g. "IT Support Technician") |
| `persona_company` | Organization the agent claims to be from |
| `phone_number` | Outbound caller ID shown to the employee |
| `voice_profile` | `{ voice_id, voice_name }` — ElevenLabs voice used for TTS |
| `is_active` | Soft-delete flag |

Callers do **not** contain attack type, objectives, or behavioral instructions — those belong to scripts.

**API:**
- `GET /api/callers/` — List callers with call stats (total_calls, avg_success_rate)
- `POST /api/callers/` — Create caller
- `PATCH /api/callers/{id}` — Update caller fields
- `DELETE /api/callers/{id}` — Soft-delete (sets is_active=false)

**Frontend:** `/callers` — Card grid with search, create/edit dialog, voice selector dropdown (12 ElevenLabs premade voices).

---

### Scripts

**Purpose:** What the AI agent *does* during a call — the attack scenario, objectives, and escalation strategy.

| Field | Description |
|-------|-------------|
| `name` | Script display name |
| `attack_type` | Category (e.g. "Technical Support Scam", "Authority Impersonation") |
| `difficulty` | `easy` / `medium` / `hard` |
| `description` | Brief human-readable summary |
| `objectives` | JSON array of goals (e.g. `["get_password", "get_mfa_code"]`) |
| `escalation_steps` | JSON array of fallback tactics (e.g. `["threaten_system_lockout"]`) |
| `is_active` | Soft-delete flag |

Scripts are attached to campaigns via `campaign_scripts` join table.

**API:**
- `GET /api/scripts/` — List scripts (includes campaign_name if attached)
- `POST /api/scripts/` — Create script
- `PATCH /api/scripts/{id}` — Update script
- `DELETE /api/scripts/{id}` — Soft-delete

**Frontend:** `/scripts` — Table with create/edit dialog.

---

### Campaigns

**Purpose:** A testing exercise that groups calls together — targeting specific employees with specific scripts.

| Field | Description |
|-------|-------------|
| `name` | Campaign display name |
| `description` | What this campaign tests |
| `attack_vector` | High-level category |
| `status` | `draft` → `running` → `completed` (or `paused`) |
| `scheduled_at` | Optional future start time |
| `started_at` | When launch was triggered |
| `completed_at` | When all calls finished |

**API:**
- `GET /api/campaigns/` — List campaigns with enriched stats (total_calls, completed_calls, avg_risk_score)
- `POST /api/campaigns/` — Create campaign
- `PATCH /api/campaigns/{id}` — Update campaign
- `DELETE /api/campaigns/{id}` — Delete campaign
- `GET /api/campaigns/{id}` — Get single campaign with stats
- `GET /api/campaigns/{id}/scripts` — Get attached scripts
- `POST /api/campaigns/{id}/launch` — Launch campaign (see below)

**Frontend:** `/campaigns` — Campaign list; `/campaigns/:id` — Detail page with launch dialog, progress tracking, and call results table.

---

### Employees

**Purpose:** The people being tested — targets of the simulated vishing calls.

| Field | Description |
|-------|-------------|
| `full_name` | Employee name |
| `email` | Corporate email |
| `phone` | Phone number to call |
| `department` | Organizational department |
| `job_title` | Role within company |
| `boss_id` | Manager's employee ID (for org hierarchy) |
| `risk_level` | Computed: `low` / `medium` / `high` / `critical` |
| `is_active` | Employment status |

**API:**
- `GET /api/employees/` — List employees with test statistics (total_tests, failed_tests, last_test_date)
- `POST /api/employees/` — Create single employee
- `POST /api/employees/import` — Bulk import from CSV file

**Frontend:** `/employees` — Employee table with search/filter; `/employees/:id` — Detail page with call history and risk trends.

---

### Calls

**Purpose:** A single phone call record — the atomic unit of testing.

| Field | Description |
|-------|-------------|
| `employee_id` | Target employee |
| `caller_id` | Caller persona used |
| `campaign_id` | Parent campaign (optional) |
| `script_id` | Script used for this call |
| `status` | `pending` / `in_progress` / `completed` / `failed` |
| `duration` | Human-readable duration |
| `duration_seconds` | Numeric duration |
| `risk_score` | 0–100, how susceptible the employee was |
| `employee_compliance` | `passed` / `failed` / `partial` |
| `transcript` | Full conversation text |
| `flags` | JSON array of security indicators |
| `ai_summary` | Post-call AI analysis |

**API:**
- `POST /api/calls/start` — Initiate a single call (requires employee_id, script_id, caller_id)
- `GET /api/calls/` — List calls with optional filters
- `GET /api/calls/{id}` — Get call detail with transcript

**Frontend:** `/calls` — Call history table; `/monitoring` — Live call monitoring.

---

## System Prompt Construction

The AI agent's behavior is assembled at call time from multiple entities by `build_system_prompt()` in `app/agent/prompts.py`.

**Inputs:**
```
script (dict) + caller (dict) + employee (dict) + org (dict) + boss (dict)
```

**Prompt sections built:**

1. **Identity** — From caller: "You are {persona_name}, a {persona_role} at {persona_company}"
2. **Context** — From employee: target's name, department, title, email, manager name
3. **Scenario** — From script: attack type, difficulty, description
4. **Objectives** — From script: list of goals to achieve
5. **Escalation Steps** — From script: fallback tactics if target resists
6. **Core Instructions** — Hardcoded behavioral rules:
   - Keep responses short (5–10 words max)
   - Use contractions and filler words
   - One thought per turn, then wait
   - No markdown or stage directions
7. **Social Engineering Tactics** — Pressure, authority, consensus, reciprocity
8. **Resistance Handling** — How to respond to pushback
9. **Safety Guardrails** — Never request real credentials
10. **Conversation Naturalness** — Match pace, avoid repetition
11. **Completion Awareness** — Append `[CALL_COMPLETE]` when done

The caller provides the *who*, the script provides the *what*, and the employee/org provide the *context*.

---

## Campaign Launch Flow

**Endpoint:** `POST /api/campaigns/{id}/launch`

**Request body:**
```json
{
  "script_id": "optional — single script for all employees",
  "caller_id": "optional — auto-selects first active caller if omitted",
  "department": "optional — target all employees in this department",
  "employee_ids": ["optional — explicit list of employee IDs"]
}
```

**Flow:**
1. Validate campaign is in `draft` or `paused` status
2. Resolve script — single-script mode (provided) or multi-script mode (random from campaign's attached scripts)
3. Resolve caller — provided or auto-select first active
4. Resolve employees — by explicit IDs, by department, or all active employees
5. Create `campaign_assignments` (one per employee, status=`pending`)
6. Set campaign status → `running`
7. Start background coroutine to execute calls sequentially (5s delay between calls)
8. Return immediately: `{ campaign_id, status: "running", assignment_count }`

The background coroutine iterates through assignments, calling `start_call()` for each, updating assignment status along the way. When all complete, the campaign status is set to `completed`.

---

## Call Pipeline

```
Twilio Outbound Call
    → Employee answers
    → WebSocket established for real-time audio
    → AI greeting sent via ElevenLabs TTS (using caller's voice_profile)
    → Conversation loop:
        Employee audio → ElevenLabs STT → Mistral LLM → ElevenLabs TTS → audio response
        (barge-in detection allows employee to interrupt)
    → Agent detects conversation end → appends [CALL_COMPLETE]
    → Post-call evaluation:
        Mistral evaluates transcript → risk_score, compliance, flags, ai_summary
    → Results saved to database
    → Real-time events published to frontend listeners
```

**Voice selection:** The caller's `voice_profile.voice_id` determines which ElevenLabs voice is used for TTS during the call. The voice name (e.g. "Rachel", "Daniel") only affects the sound — the agent introduces itself using the caller's `persona_name`.

---

## Analytics

**Endpoints** (all under `/api/analytics/`):

| Endpoint | Description |
|----------|-------------|
| `GET /risk-trend` | Average risk score over time |
| `GET /department-trends` | Per-department failure rates over time |
| `GET /repeat-offenders` | Employees who fail multiple tests |
| `GET /campaign-effectiveness` | Compare campaigns by failure rate and risk |
| `GET /flag-frequency` | Most common security flags |
| `GET /attack-heatmap` | Attack type vs. department matrix |
| `GET /employee/{id}` | Individual employee deep-dive |
| `GET /dept-flag-pivot` | Department vs. flag matrix |
| `GET /hierarchy-risk` | Organizational tree with risk rollup |

**Dashboard** (`/api/dashboard/`):

| Endpoint | Description |
|----------|-------------|
| `GET /stats` | Summary cards (active campaigns, total calls, avg risk) |
| `GET /risk-distribution` | Employee count by risk level |
| `GET /risk-by-department` | Department risk breakdown |
| `GET /calls-over-time` | Call volume chart data |
| `GET /smart-widgets` | Risk hotspot, recent failures, campaign pulse |

---

## Frontend Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | Dashboard | Overview with stats, charts, smart widgets |
| `/analytics` | Analytics | Deep-dive charts and tables |
| `/campaigns` | Campaigns | Campaign list with status badges |
| `/campaigns/:id` | CampaignDetail | Launch dialog, progress, call results |
| `/callers` | Callers | Caller persona management |
| `/scripts` | Scripts | Script management |
| `/employees` | Employees | Employee directory with risk indicators |
| `/employees/:id` | EmployeeDetail | Individual test history and risk trends |
| `/calls` | Calls | Call history with filters |
| `/monitoring` | Monitoring | Live call monitoring |
| `/settings/users` | UserManagement | Org user management (admin) |

---

## Authentication

- Supabase Auth with JWT tokens
- All protected API endpoints require `Authorization: Bearer <token>` header
- Frontend uses `ProtectedRoute` wrapper that redirects to `/login` if unauthenticated
- Organization isolation: all queries are scoped by `org_id`
- Admin role required for user management and admin transfer

---

## Database

PostgreSQL via Supabase. Key tables:

| Table | Description |
|-------|-------------|
| `organizations` | Multi-tenant org container |
| `users` | Auth users linked to orgs |
| `employees` | Test targets |
| `callers` | AI agent personas |
| `scripts` | Attack scenarios |
| `campaigns` | Testing exercises |
| `campaign_scripts` | Many-to-many: campaigns ↔ scripts |
| `campaign_assignments` | Per-employee call assignments within a campaign |
| `calls` | Individual call records with results |

Migrations are in `services/api/migrations/` and run in numeric order.
