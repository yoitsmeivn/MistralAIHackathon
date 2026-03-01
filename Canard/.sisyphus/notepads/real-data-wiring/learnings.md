## 2026-02-28 Initial Analysis

### Database State
- 38 employees across 8 departments, all active, all have phone numbers (mostly +1555...)
- Sarah Johnson (employee 0101) has Ivan's real phone: +14158252791
- 2 scripts: IT Helpdesk Password Reset (medium), Urgent CEO Wire Transfer (hard)
- 4 callers: John Mitchell (IT Support), Robert Chen (CEO), Amanda Stevens (Security), David Wilson (HR, inactive)
- Callers have is_active=None (not False), except David Wilson who is False
- All data in org_id: 00000000-0000-0000-0000-000000000001

### Call Flow (fully wired to Supabase)
- POST /api/calls/start → services/calls.py → fetches employee + script → creates call → Twilio outbound
- Twilio webhook → _lookup_call_safe(CallSid) → WebSocket stream
- _init_agent_session() fetches script + caller from call record BUT NOT employee
- build_system_prompt(script, caller) — no employee data passed

### Key Gap
- Agent has NO knowledge of target employee (name, department, job_title)
- For realistic social engineering, agent needs to know who it's calling

### Model Benchmarks (3-run avg, max_tokens=150)
- ministral-3b-latest: 376ms — FASTEST, quality good for phone
- ministral-8b-latest: 423ms — current model
- open-mistral-nemo: 517ms
- mistral-tiny-latest: 633ms

### Constraints
- DO NOT modify db/queries.py
- DO NOT modify services/analysis.py

## 2026-02-28 Employee Target Prompt Wiring

- `_init_agent_session()` now initializes `employee = None`, fetches `employee_id` from the call record, and resolves it with `queries.get_employee(eid)` inside the existing protected DB lookup block.
- Agent prompt construction now passes employee context via `build_system_prompt(script, caller=caller, employee=employee)` while preserving fallback behavior when script lookup fails.
- `build_system_prompt()` and `_build_from_dict()` accept optional `employee` to maintain backward compatibility for call sites/tests that only pass script/caller.
- Prompt assembly now injects `Target Information (the person you are calling):` between persona and scenario metadata, including `Target Name`, `Target Department`, and `Target Job Title` only when values exist.


## 2026-03-01 Real Data Prompt Grounding Refresh

- Behavioral instructions were tightened for phone realism: hard 1-2 sentence cap, explicit stop-and-wait turn-taking, no repeated self-introduction, and no repeated prior facts.
- Prompt safety now explicitly forbids fabricating names/codes/reference numbers and restricts references to Scenario + Target/Organization context.
- `_build_from_dict()` now emits a richer context section with company name/industry, target name/department/job title/email, and manager name/title when present.
- `build_system_prompt()` now accepts `org` and `boss` and forwards them to dict-based prompt building while keeping legacy scenario mode intact.
- `_init_agent_session()` now resolves both `org` (via `org_id`) and `boss` (via `boss_id`) from the employee record in the existing DB safety wrapper.
- Agent generation token cap was reduced to 80 to keep utterances short and reduce monologues.
