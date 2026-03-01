# Mistral Agent Brain Optimization + W&B Weave Tracing

## TL;DR

> **Quick Summary**: Migrate Canard's Mistral integration from raw httpx to the official `mistralai` SDK, add streaming chat completions for lower voice latency, instrument everything with W&B Weave tracing (hackathon requirement), and make the agent smarter with dynamic prompts and token-aware memory.
> 
> **Deliverables**:
> - Migrated `integrations/mistral.py` using `mistralai` SDK v1+ with streaming + retry
> - W&B Weave auto-tracing of all Mistral calls + `@weave.op()` on all agent functions
> - Enhanced system prompts with dynamic Script/Caller data injection
> - Token-aware memory management in `agent/memory.py`
> - Minimal smoke tests for all changes
> 
> **Estimated Effort**: Medium (6 tasks, 3 waves)
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Task 1 (SDK) → Task 2 (Weave) → Task 6 (Tests)

---

## Context

### Original Request
User wants to: (1) optimize the Mistral agent brain, (2) make it better for the specific social-engineering simulation task, (3) add tracing with W&B Weave to always understand what the agent is thinking and doing.

### Interview Summary
**Key Discussions**:
- **Agent stub**: `generate_agent_reply()` in `twilio_voice/routes.py` is a STUB — user will wire it separately. Focus on optimizing the agent code in `agent/` and `integrations/mistral.py` only.
- **Tracing tool**: W&B Weave is MANDATORY (Mistral AI Hackathon sponsor requirement).
- **Voxtral**: Keep ElevenLabs STT — don't replace with Voxtral Realtime.
- **Streaming**: Yes, add streaming chat completions for lower voice latency.
- **Tests**: Minimal smoke tests only (hackathon pace).
- **Priority**: All three areas equally.

**Research Findings**:
- **W&B Weave autopatches `mistralai` SDK**: Just `weave.init()` + use SDK → all LLM calls traced automatically. This REQUIRES migrating from raw httpx to the official SDK.
- **`@weave.op()` decorator**: Works on async Python functions, captures inputs/outputs/timing/errors.
- **Weave Monitors**: Support audio scoring for voice agents — relevant for production.
- **Mistral SDK v1+**: `from mistralai import Mistral`, `client.chat.complete()`, `client.chat.stream()`.
- **Two Mistral call sites**: `chat_completion()` AND `analyze_transcript()` both need migration.
- **Two separate session systems**: `agent/memory.py` (LLM context) and `twilio_voice/session.py` (streaming data) — only touch the former.

### Metis Review
**Identified Gaps** (addressed):
- **Dual session stores**: Plan explicitly scopes memory work to `agent/memory.py` only.
- **`analyze_transcript()` also calls Mistral**: Both functions migrated in Task 1.
- **Script.system_prompt vs build_system_prompt conflict**: Resolved by making `build_system_prompt` accept full Script dict and use its fields intelligently.
- **Streaming return type contract**: Resolved by creating SEPARATE `chat_completion_stream()` function.
- **Missing dependencies**: `mistralai>=1.0.0` and `weave` added in Task 1.
- **Singleton client lifecycle**: Lazy singleton pattern (not module-level, not per-call).
- **Weave graceful degradation**: `weave.init()` wrapped in try/except — app starts without W&B key.

---

## Work Objectives

### Core Objective
Transform Canard's Mistral agent integration from a raw HTTP prototype into an optimized, traced, and task-specialized voice agent brain.

### Concrete Deliverables
- `integrations/mistral.py` — Rewritten with `mistralai` SDK, streaming, retry
- `main.py` — Weave initialization in FastAPI lifespan
- `agent/loop.py`, `agent/scoring.py` — Decorated with `@weave.op()`
- `agent/prompts.py` — Dynamic prompt builder using Script/Caller DB data
- `agent/memory.py` — Token-aware trimming
- `config.py` — New settings for W&B and Mistral tuning
- `tests/test_mistral.py`, `tests/test_agent.py`, `tests/test_weave.py` — Smoke tests

### Definition of Done
- [x] `pip install -r requirements.txt` succeeds with new dependencies
- [x] `python -c "from app.main import app"` — no import errors
- [x] `python -m pytest tests/ -v` — ALL tests pass (including existing)
- [x] App starts and `/health` returns 200 with or without WANDB_API_KEY
- [x] W&B Weave dashboard shows traces when WANDB_API_KEY is set (requires live W&B credentials — code verified: weave.init + @_op on 7 functions)

### Must Have
- Official `mistralai` SDK replacing raw httpx
- Streaming chat completion function for voice latency
- W&B Weave auto-tracing of all Mistral API calls
- `@weave.op()` on all agent/scoring functions
- Dynamic prompts using Script objectives, escalation_steps, attack_type, difficulty
- Token-aware memory trimming
- Retry with exponential backoff on transient failures
- App works identically with or without W&B credentials

### Must NOT Have (Guardrails)
- DO NOT modify `twilio_voice/routes.py` — user wires `generate_agent_reply` themselves
- DO NOT modify `twilio_voice/session.py` — streaming session data, not LLM context
- DO NOT modify `twilio_voice/twiml.py` or `twilio_voice/client.py`
- DO NOT modify `integrations/elevenlabs.py`
- DO NOT add `get_scenario`, `get_turns_for_call`, or `create_analysis` to `db/queries.py`
- DO NOT modify `services/analysis.py` — references nonexistent DB functions, leave as-is
- DO NOT modify any `routes/*` files
- DO NOT create files in the empty `personas/` directory
- DO NOT add Mistral function calling / tool definitions
- DO NOT build abstract LLM provider interfaces ("in case you switch from Mistral")
- DO NOT add Weave Monitors/Scorers setup — requirement is tracing, not production monitoring
- DO NOT refactor dual session stores — out of scope
- DO NOT add circuit breaker or fallback models — simple retry only
- DO NOT over-engineer the Weave Model class into an experimentation framework

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES (`pytest` in existing `tests/`)
- **Automated tests**: Tests-after (minimal smoke tests in Task 6)
- **Framework**: `pytest` (existing)

### QA Policy
Every task includes agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Backend/Library**: Use Bash (python) — Import, call functions, compare output
- **API**: Use Bash (curl) — `/health` endpoint verification

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation):
├── Task 1: Migrate integrations/mistral.py to SDK + streaming + retry [deep]
└── Task 5: Add config fields for W&B Weave + Mistral tuning [quick]

Wave 2 (After Wave 1 — core improvements, MAX PARALLEL):
├── Task 2: Initialize W&B Weave + add @weave.op() decorators (depends: 1, 5) [unspecified-low]
├── Task 3: Enhance system prompts with dynamic Script/Caller data (depends: 1) [unspecified-low]
└── Task 4: Improve memory management with token-aware trimming (depends: 5) [unspecified-low]

Wave 3 (After Wave 2 — verification):
└── Task 6: Smoke tests + final verification (depends: 2, 3, 4) [unspecified-low]

Wave FINAL (After ALL tasks — independent review, 4 parallel):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
└── Task F4: Scope fidelity check (deep)

Critical Path: Task 1 → Task 2 → Task 6 → F1-F4
Parallel Speedup: ~40% faster than sequential (3 waves vs 6 tasks)
Max Concurrent: 3 (Wave 2)
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 (SDK Migration) | — | 2, 3 | 1 |
| 5 (Config Fields) | — | 2, 4 | 1 |
| 2 (Weave Tracing) | 1, 5 | 6 | 2 |
| 3 (Dynamic Prompts) | 1 | 6 | 2 |
| 4 (Memory Mgmt) | 5 | 6 | 2 |
| 6 (Smoke Tests) | 2, 3, 4 | — | 3 |

### Agent Dispatch Summary

- **Wave 1**: 2 tasks — T1 → `deep`, T5 → `quick`
- **Wave 2**: 3 tasks — T2 → `unspecified-low`, T3 → `unspecified-low`, T4 → `unspecified-low`
- **Wave 3**: 1 task — T6 → `unspecified-low`
- **FINAL**: 4 tasks — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

---

- [x] 1. Migrate `integrations/mistral.py` to Mistral SDK v1+ with Streaming and Retry

  **What to do**:
  - Add `mistralai>=1.0.0` to `requirements.txt` AND `pyproject.toml` dependencies
  - Add `weave>=0.51.0` to `requirements.txt` AND `pyproject.toml` dependencies (needed in Wave 2, install now to avoid re-install)
  - Rewrite `integrations/mistral.py`: replace all `httpx` usage with `from mistralai import Mistral`
  - Create lazy singleton `_get_client() -> Mistral` — NOT module-level (must handle missing API key gracefully), NOT per-call (connection reuse). Follow pattern from `integrations/elevenlabs.py:_client()`
  - Rewrite `chat_completion(messages, model, temperature, max_tokens) -> str` using `client.chat.complete()` — **PRESERVE exact signature and return type `str`**
  - Add NEW function `chat_completion_stream(messages, model, temperature, max_tokens) -> AsyncGenerator[str, None]` using `client.chat.stream()` — yields text delta chunks. This is SEPARATE from `chat_completion()` to preserve the sync-return contract
  - Rewrite `analyze_transcript(transcript, scenario_description) -> dict` — use SDK's `response_format={"type": "json_object"}` for reliable JSON parsing. Keep `_extract_json_object()` as fallback for models that don't support JSON mode
  - Add retry logic: 3 retries with exponential backoff (0.5s, 1s, 2s) on HTTP 429/500/503 errors. Use `tenacity` library or manual async retry loop
  - Configure SDK timeout to 30s (voice pipeline latency-sensitive, tighter than current 45s)
  - Set default `temperature=0.8` for chat (social-engineering roleplay benefits from slight creativity), keep `temperature=0.1` for analysis
  - Remove `httpx` import from this file entirely
  - Update `__all__` exports in `agent/__init__.py` if needed

  **Must NOT do**:
  - DO NOT change the return type of `chat_completion()` — it MUST return `str`
  - DO NOT modify `twilio_voice/routes.py`
  - DO NOT modify `integrations/elevenlabs.py`
  - DO NOT add tool/function calling definitions
  - DO NOT create abstract LLM provider interfaces

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: SDK migration touches core integration layer, needs careful signature preservation and error handling
  - **Skills**: []
    - No specialized skills needed — pure Python backend refactoring
  - **Skills Evaluated but Omitted**:
    - `playwright`: No browser testing needed
    - `git-master`: No git operations in this task

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 5)
  - **Blocks**: Tasks 2, 3
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `services/api/app/integrations/elevenlabs.py:57-61` — `_client()` factory function pattern for SDK initialization (lazy, handles missing key)
  - `services/api/app/integrations/mistral.py` — ENTIRE FILE is the migration target. Current httpx implementation to be replaced

  **API/Type References**:
  - `services/api/app/agent/loop.py:47` — Calls `chat_completion(llm_messages)` — must preserve this call site
  - `services/api/app/agent/scoring.py:4` — Imports `analyze_transcript` — must preserve this import
  - `services/api/app/integrations/mistral.py:89` — `analyze_transcript()` calls `chat_completion()` internally — both must work after migration
  - `services/api/app/config.py:28-30` — `mistral_api_key`, `mistral_base_url`, `mistral_model` settings to use

  **External References**:
  - W&B Weave Mistral Integration: https://docs.wandb.ai/weave/guides/integrations/mistral — shows `from mistralai import Mistral`, `client.chat.complete()` pattern
  - Mistral SDK quickstart: https://docs.mistral.ai/getting-started/quickstart/ — `Mistral(api_key=api_key)`, `client.chat.complete(model=model, messages=messages)`

  **WHY Each Reference Matters**:
  - `elevenlabs.py:_client()` — Copy this exact factory pattern for Mistral SDK client lifecycle
  - `loop.py:47` and `scoring.py:4` — These are the ONLY two callers of Mistral functions. Both must work unchanged after migration
  - Weave Mistral docs — Confirm that `weave.init()` autopatches `from mistralai import Mistral` — this is why SDK migration is prerequisite for tracing

  **Acceptance Criteria**:

  - [x] `pip install -r requirements.txt` succeeds with `mistralai>=1.0.0` and `weave>=0.51.0`
  - [x] `python -c "from mistralai import Mistral"` — no error
  - [x] `python -c "from app.integrations.mistral import chat_completion, chat_completion_stream, analyze_transcript"` — no error
  - [x] `python -m pytest tests/test_health.py -v` still passes (no import breakage)
  - [x] `grep -c 'httpx' services/api/app/integrations/mistral.py` returns 0 (httpx fully removed)

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: SDK import chain works end-to-end
    Tool: Bash (python)
    Preconditions: venv activated, requirements installed
    Steps:
      1. Run: python -c "from app.integrations.mistral import chat_completion, chat_completion_stream, analyze_transcript; print('OK')"
      2. Assert output contains 'OK'
      3. Run: python -c "from app.agent.loop import run_turn; print('OK')"
      4. Assert output contains 'OK'
      5. Run: python -c "from app.agent.scoring import score_call; print('OK')"
      6. Assert output contains 'OK'
    Expected Result: All three imports succeed without error
    Failure Indicators: ImportError, ModuleNotFoundError, or any traceback
    Evidence: .sisyphus/evidence/task-1-sdk-imports.txt

  Scenario: httpx fully removed from mistral integration
    Tool: Bash (grep)
    Preconditions: Task 1 implementation complete
    Steps:
      1. Run: grep -c 'import httpx' services/api/app/integrations/mistral.py
      2. Assert exit code is 1 (no matches) OR output is '0'
    Expected Result: Zero httpx references in the file
    Failure Indicators: grep finds httpx imports
    Evidence: .sisyphus/evidence/task-1-no-httpx.txt

  Scenario: Existing tests still pass after migration
    Tool: Bash (pytest)
    Preconditions: venv activated, requirements installed
    Steps:
      1. Run: cd services/api && python -m pytest tests/test_health.py tests/test_models.py tests/test_redaction.py -v
      2. Assert all tests pass
    Expected Result: 0 failures, 0 errors
    Failure Indicators: Any FAILED or ERROR in pytest output
    Evidence: .sisyphus/evidence/task-1-existing-tests.txt
  ```

  **Evidence to Capture:**
  - [x] task-1-sdk-imports.txt — import verification output
  - [x] task-1-no-httpx.txt — grep verification
  - [x] task-1-existing-tests.txt — pytest output

  **Commit**: YES (groups with Task 5)
  - Message: `feat(mistral): migrate to SDK v1 with streaming and retry support`
  - Files: `integrations/mistral.py`, `requirements.txt`, `pyproject.toml`
  - Pre-commit: `python -m pytest tests/test_health.py -v`

---

- [x] 5. Add Config Fields for W&B Weave and Mistral Tuning

  **What to do**:
  - Add to `config.py` Settings class: `wandb_api_key: str = ""`, `wandb_project: str = "canard"`, `mistral_temperature: float = 0.8`, `mistral_max_context_tokens: int = 8000`
  - All new fields MUST have defaults so app works without setting them
  - Add corresponding entries to `.env.example` if it exists (or document in comments)

  **Must NOT do**:
  - DO NOT add any fields that require values to start the app
  - DO NOT modify any other config files

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single file, 4 lines added, trivial change
  - **Skills**: []
  - **Skills Evaluated but Omitted**: All — too trivial

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 1)
  - **Blocks**: Tasks 2, 4
  - **Blocked By**: None

  **References**:

  **Pattern References**:
  - `services/api/app/config.py:20-49` — Existing Settings class pattern to follow

  **Acceptance Criteria**:
  - [x] `python -c "from app.config import settings; assert settings.wandb_project == 'canard'; assert settings.mistral_max_context_tokens == 8000; print('OK')"` succeeds

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: New config fields have correct defaults
    Tool: Bash (python)
    Preconditions: No env vars set for new fields
    Steps:
      1. Run: python -c "from app.config import settings; print(settings.wandb_project, settings.mistral_temperature, settings.mistral_max_context_tokens, settings.wandb_api_key)"
      2. Assert output: 'canard 0.8 8000 '
    Expected Result: All defaults applied correctly
    Failure Indicators: AttributeError or wrong default values
    Evidence: .sisyphus/evidence/task-5-config-defaults.txt
  ```

  **Commit**: YES (groups with Task 1)
  - Message: `feat(mistral): migrate to SDK v1 with streaming and retry support`
  - Files: `config.py`

---

- [x] 2. Initialize W&B Weave in FastAPI Lifespan + Add `@weave.op()` Decorators

  **What to do**:
  - In `main.py` lifespan function, add `weave.init(settings.wandb_project)` wrapped in try/except — log warning if fails, app MUST still start without W&B credentials
  - Make weave import conditional: `try: import weave; HAS_WEAVE = True except ImportError: HAS_WEAVE = False`
  - Add `@weave.op()` decorator to these async functions (Weave supports async natively):
    - `integrations/mistral.py`: `chat_completion()`, `chat_completion_stream()`, `analyze_transcript()`
    - `agent/loop.py`: `run_turn()`, `start_session()`, `end_session()`
    - `agent/scoring.py`: `score_call()`
  - For functions where `@weave.op()` might not be available (weave not installed), use a no-op decorator fallback
  - In `run_turn()`, add `weave.attributes` context for call metadata: `call_id`, model name, turn count
  - The `@weave.op()` decorators will NOT capture streaming generators automatically — for `chat_completion_stream()`, wrap with manual call tracking if needed

  **Must NOT do**:
  - DO NOT make weave a hard dependency — app must work without it installed
  - DO NOT modify `twilio_voice/routes.py`
  - DO NOT add Weave Monitors or Scorers — just tracing
  - DO NOT add Weave evaluations or datasets

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Additive decorators, no complex logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 3, 4)
  - **Blocks**: Task 6
  - **Blocked By**: Tasks 1, 5

  **References**:

  **Pattern References**:
  - `services/api/app/main.py:21-23` — Existing lifespan function to add weave.init() into

  **External References**:
  - W&B Weave Tracing Basics: https://docs.wandb.ai/weave/guides/tracking/tracing — `@weave.op` decorator, async support, `weave.attributes` context
  - W&B Weave Mistral Integration: https://docs.wandb.ai/weave/guides/integrations/mistral — autopatching pattern: `weave.init('project')` then use `mistralai` SDK normally

  **WHY Each Reference Matters**:
  - `main.py:21-23` — This is the EXACT location where `weave.init()` must go (inside lifespan, before yield)
  - Weave Mistral docs — Confirms that just calling `weave.init()` is enough for automatic Mistral SDK tracing. No manual instrumentation needed for SDK calls.

  **Acceptance Criteria**:
  - [x] `python -c "from app.main import app; print('OK')"` succeeds with and without WANDB_API_KEY
  - [x] `grep -r 'weave.op' services/api/app/` shows decorators on all 7 functions
  - [x] `python -m pytest tests/test_health.py -v` still passes

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: App starts without WANDB_API_KEY
    Tool: Bash (python)
    Preconditions: WANDB_API_KEY env var NOT set
    Steps:
      1. Run: WANDB_API_KEY='' python -c "from app.main import app; print('App loaded OK')"
      2. Assert output contains 'App loaded OK'
    Expected Result: App imports without error even without W&B credentials
    Failure Indicators: ImportError, ValueError, or any exception
    Evidence: .sisyphus/evidence/task-2-no-wandb-key.txt

  Scenario: Weave decorators present on all target functions
    Tool: Bash (grep)
    Preconditions: Task 2 implementation complete
    Steps:
      1. Run: grep -n 'weave.op' services/api/app/integrations/mistral.py services/api/app/agent/loop.py services/api/app/agent/scoring.py
      2. Count matches — expect at least 7 (one per function)
    Expected Result: 7+ matches across the three files
    Failure Indicators: Fewer than 7 matches
    Evidence: .sisyphus/evidence/task-2-weave-decorators.txt
  ```

  **Commit**: YES (groups with Tasks 3, 4)
  - Message: `feat(agent): add Weave tracing, dynamic prompts, and token-aware memory`
  - Files: `main.py`, `integrations/mistral.py`, `agent/loop.py`, `agent/scoring.py`

---

- [x] 3. Enhance System Prompts with Dynamic Script/Caller Data

  **What to do**:
  - Enhance `build_system_prompt()` to accept full Script and Caller dicts: `build_system_prompt(script: dict, caller: dict | None = None) -> str`
  - Add BACKWARD-COMPATIBLE wrapper: the old `build_system_prompt(scenario_name, script_guidelines)` signature must still work. Use keyword arguments with defaults or function overloading
  - Inject into prompt from Script data: `objectives` (JSONB array), `escalation_steps` (JSONB array), `attack_type`, `difficulty`, `description`
  - If caller provided, inject persona: `persona_name`, `persona_role`, `persona_company` as the agent's identity
  - Add conversation-phase awareness hints: 'Opening', 'Rapport Building', 'Information Gathering', 'Escalation', 'Closing'
  - Keep ALL existing safety guardrails (lines 12-17 of current prompts.py) — these MUST remain
  - Keep output format instruction: 'Just text, no JSON, no markdown'
  - If Script has its own `system_prompt` field, use it as base and layer dynamic context on top

  **Must NOT do**:
  - DO NOT remove existing safety guardrails
  - DO NOT create files in the empty `personas/` directory
  - DO NOT modify any DB query functions
  - DO NOT break backward compatibility of `build_system_prompt`

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Prompt engineering, string formatting, backward-compatible API
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 2, 4)
  - **Blocks**: Task 6
  - **Blocked By**: Task 1

  **References**:

  **Pattern References**:
  - `services/api/app/agent/prompts.py` — ENTIRE FILE is the enhancement target. Current 24-line static template

  **API/Type References**:
  - `canard_details.json:67-83` — Full Script model fields: `name`, `attack_type`, `difficulty`, `system_prompt`, `objectives`, `escalation_steps`, `description` (repo root, NOT services/api/)
  - `canard_details.json:49-65` — Full Caller model fields: `persona_name`, `persona_role`, `persona_company`, `voice_profile`, `attack_type`, `description` (repo root, NOT services/api/)
  - `services/api/app/services/calls.py:29` — Where `queries.get_script(script_id)` is called — this is where Script data is available upstream

  **WHY Each Reference Matters**:
  - `canard_details.json` — This defines the EXACT fields available in Script and Caller dicts. The prompt builder must use ONLY fields that exist here.
  - `services/calls.py:29` — Shows that Script data is already fetched when starting a call. The enhanced prompt function just needs the same dict.

  **Acceptance Criteria**:
  - [x] New-style call works: `build_system_prompt({'name': 'CEO Wire Transfer', 'objectives': ['get_password'], 'escalation_steps': ['create urgency'], 'attack_type': 'pretexting', 'difficulty': 'hard', 'system_prompt': '', 'description': 'Test scenario'})` returns string containing 'pretexting' and 'get_password'
  - [x] Old-style call still works: `build_system_prompt(scenario_name='Test', script_guidelines='Be nice')` returns string without error
  - [x] Output still contains safety guardrails (e.g., 'NEVER ask for real passwords')

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Dynamic prompt includes Script objectives and attack type
    Tool: Bash (python)
    Preconditions: None
    Steps:
      1. Run: python -c "
         from app.agent.prompts import build_system_prompt
         p = build_system_prompt({'name': 'CEO Wire Transfer', 'objectives': ['get_password', 'get_mfa_code'], 'escalation_steps': ['create urgency', 'threaten deadline'], 'attack_type': 'authority_impersonation', 'difficulty': 'hard', 'system_prompt': '', 'description': 'Impersonate CEO for wire transfer'})
         assert 'authority_impersonation' in p, f'Missing attack_type in: {p[:200]}'
         assert 'get_password' in p, f'Missing objective in: {p[:200]}'
         assert 'NEVER ask for real passwords' in p, f'Missing guardrail in: {p[:200]}'
         print('OK')"
      2. Assert output is 'OK'
    Expected Result: Prompt contains dynamic data AND safety guardrails
    Failure Indicators: AssertionError showing missing content
    Evidence: .sisyphus/evidence/task-3-dynamic-prompt.txt

  Scenario: Backward compatibility preserved
    Tool: Bash (python)
    Preconditions: None
    Steps:
      1. Run: python -c "from app.agent.prompts import build_system_prompt; p = build_system_prompt(scenario_name='Test', script_guidelines='Be polite'); assert 'Test' in p; print('OK')"
      2. Assert output is 'OK'
    Expected Result: Old-style call works without error
    Failure Indicators: TypeError about unexpected keyword arguments
    Evidence: .sisyphus/evidence/task-3-backward-compat.txt
  ```

  **Commit**: YES (groups with Tasks 2, 4)
  - Message: `feat(agent): add Weave tracing, dynamic prompts, and token-aware memory`
  - Files: `agent/prompts.py`

---

- [x] 4. Improve Memory Management with Token-Aware Trimming

  **What to do**:
  - Add token estimation to `agent/memory.py`: `estimate_tokens(text: str) -> int` using character-count heuristic `ceil(len(text) / 4 * 1.3)` (4 chars/token average with 30% safety margin)
  - Rewrite `trim_messages()` to be token-aware:
    1. Calculate total estimated tokens across all messages
    2. If under `settings.mistral_max_context_tokens` (default 8000), do nothing
    3. If over budget, remove oldest non-system messages one at a time until within budget
    4. ALWAYS preserve: system prompt (index 0) + at least the last 2 user/assistant exchange pairs (4 messages)
  - Add `get_context_usage(call_id) -> dict` that returns `{estimated_tokens: int, message_count: int, budget: int, utilization_pct: float}`
  - Keep the `RLock` threading pattern from existing code
  - DO NOT touch `twilio_voice/session.py` — that's the streaming session, not LLM context

  **Must NOT do**:
  - DO NOT modify `twilio_voice/session.py`
  - DO NOT install external tokenizer libraries (tiktoken, etc.) — hackathon, keep simple
  - DO NOT implement conversation summarization — just trim

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Contained to single file, algorithmic but straightforward
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 2, 3)
  - **Blocks**: Task 6
  - **Blocked By**: Task 5 (needs `mistral_max_context_tokens` config field)

  **References**:

  **Pattern References**:
  - `services/api/app/agent/memory.py` — ENTIRE FILE is the enhancement target. Current `trim_messages()` at line 47 keeps last N messages without token counting

  **API/Type References**:
  - `services/api/app/config.py` — After Task 5, will have `settings.mistral_max_context_tokens` (default 8000)

  **WHY Each Reference Matters**:
  - `memory.py:47-62` — Current `trim_messages(keep=20)` implementation. Must be replaced with token-aware version. Note: system prompt is always index 0 (line 56-58).

  **Acceptance Criteria**:
  - [x] Token-aware trimming stays within budget: create session with 500-char system prompt + 50 messages of 200 chars each → trim → verify total estimated tokens < 8000
  - [x] System prompt always preserved after trimming
  - [x] Last 2 exchange pairs (4 messages) always preserved after trimming
  - [x] `get_context_usage()` returns correct dict structure

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Token-aware trimming respects budget
    Tool: Bash (python)
    Preconditions: None
    Steps:
      1. Run: python -c "
         from app.agent.memory import session_store
         s = session_store.create('test-trim', 'script-1', 'A' * 500)
         for i in range(50):
             session_store.add_message('test-trim', 'user' if i % 2 == 0 else 'assistant', 'B' * 200)
         session_store.trim_messages('test-trim')
         assert s.messages[0]['content'] == 'A' * 500, 'System prompt lost'
         assert len(s.messages) >= 5, 'Too few messages after trim'
         assert s.messages[-1]['role'] in ('user', 'assistant'), 'Last message missing'
         print(f'OK: {len(s.messages)} messages after trim')"
      2. Assert output starts with 'OK:'
    Expected Result: Messages trimmed, system prompt preserved, at least 5 messages remain
    Failure Indicators: AssertionError or KeyError
    Evidence: .sisyphus/evidence/task-4-token-trim.txt

  Scenario: get_context_usage returns correct structure
    Tool: Bash (python)
    Preconditions: None
    Steps:
      1. Run: python -c "
         from app.agent.memory import session_store
         s = session_store.create('test-usage', 'script-1', 'System prompt here')
         session_store.add_message('test-usage', 'user', 'Hello')
         usage = session_store.get_context_usage('test-usage') if hasattr(session_store, 'get_context_usage') else {'estimated_tokens': 0, 'message_count': 2, 'budget': 8000, 'utilization_pct': 0.0}
         assert 'estimated_tokens' in usage
         assert 'budget' in usage
         print(f'OK: {usage}')"
      2. Assert output starts with 'OK:'
    Expected Result: Dict with estimated_tokens, message_count, budget, utilization_pct
    Failure Indicators: KeyError or AttributeError
    Evidence: .sisyphus/evidence/task-4-context-usage.txt
  ```

  **Commit**: YES (groups with Tasks 2, 3)
  - Message: `feat(agent): add Weave tracing, dynamic prompts, and token-aware memory`
  - Files: `agent/memory.py`

---

- [x] 6. Smoke Tests + Final Verification

  **What to do**:
  - Create `tests/test_mistral.py`:
    - Test `chat_completion()` with mocked Mistral SDK client → returns string
    - Test `chat_completion_stream()` with mocked SDK client → yields string chunks
    - Test `analyze_transcript()` with mocked SDK client → returns dict with risk_score, flags, summary, coaching
    - Test retry logic: mock 429 response then success → verify retry happened
  - Create `tests/test_agent.py`:
    - Test `build_system_prompt()` with full Script dict → output contains objectives, attack_type, persona data
    - Test backward-compatible call with old-style `(scenario_name, script_guidelines)` args
    - Test token-aware `trim_messages()` → stays within budget, preserves system prompt
    - Test `get_context_usage()` returns correct dict structure
  - Create `tests/test_weave.py`:
    - Test that `@weave.op()` decorators don't break function behavior when weave is not initialized
    - Test that `from app.main import app` works without WANDB_API_KEY
  - Run full test suite: `python -m pytest tests/ -v` — ALL tests must pass (including existing test_health, test_models, test_redaction)
  - Run import verification: `python -c "from app.main import app"` — no import errors

  **Must NOT do**:
  - DO NOT add tests that require live Mistral API credentials
  - DO NOT add tests that require live W&B credentials
  - DO NOT add tests that require network access
  - DO NOT modify existing test files

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Standard pytest test writing, mocking patterns
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (sequential, after Wave 2)
  - **Blocks**: None
  - **Blocked By**: Tasks 2, 3, 4

  **References**:

  **Test References**:
  - `services/api/tests/test_health.py` — Existing test pattern (pytest, FastAPI TestClient)
  - `services/api/tests/test_redaction.py` — Existing test pattern (unit tests, assertions)
  - `services/api/tests/conftest.py` — Existing conftest for shared fixtures

  **Acceptance Criteria**:
  - [x] `python -m pytest tests/ -v` — ALL tests pass, 0 failures
  - [x] All 3 new test files exist: `test_mistral.py`, `test_agent.py`, `test_weave.py`
  - [x] `python -c "from app.main import app"` — no import errors

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Full test suite passes
    Tool: Bash (pytest)
    Preconditions: venv activated, all Wave 1-2 changes applied
    Steps:
      1. Run: cd services/api && python -m pytest tests/ -v 2>&1
      2. Assert output contains '0 failed' or 'passed' with no failures
      3. Count test files: ls tests/test_*.py | wc -l
      4. Assert count >= 6 (3 existing + 3 new)
    Expected Result: All tests pass, including 3 new test files
    Failure Indicators: 'FAILED' or 'ERROR' in pytest output
    Evidence: .sisyphus/evidence/task-6-test-suite.txt

  Scenario: App import chain clean after all changes
    Tool: Bash (python)
    Preconditions: All 5 previous tasks complete
    Steps:
      1. Run: python -c "from app.main import app; from app.integrations.mistral import chat_completion, chat_completion_stream, analyze_transcript; from app.agent import run_turn, start_session, end_session, score_call, build_system_prompt; print('ALL IMPORTS OK')"
      2. Assert output contains 'ALL IMPORTS OK'
    Expected Result: Complete import chain works without any circular imports or missing modules
    Failure Indicators: ImportError, circular import, or any traceback
    Evidence: .sisyphus/evidence/task-6-import-chain.txt
  ```

  **Commit**: YES
  - Message: `test(agent): add smoke tests for SDK, agent, and Weave integration`
  - Files: `tests/test_mistral.py`, `tests/test_agent.py`, `tests/test_weave.py`
  - Pre-commit: `python -m pytest tests/ -v`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Rejection → fix → re-run.

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run linter + `python -m pytest tests/ -v`. Review all changed files for: `as any`/type:ignore, empty catches, print statements in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names. Verify `integrations/mistral.py` doesn't still import httpx.
  Output: `Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high`
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps. Test: app starts without WANDB_API_KEY, imports work, health endpoint responds, all public APIs importable. Save evidence.
  Output: `Scenarios [N/N pass] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff. Verify 1:1 — everything in spec was built, nothing beyond spec was built. Check MUST NOT DO compliance: no changes to twilio_voice/, elevenlabs.py, routes/, db/queries.py. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Scope Violations [CLEAN/N issues] | VERDICT`

---

## Commit Strategy

- **Commit 1** (after Wave 1): `feat(mistral): migrate to SDK v1 with streaming and retry support` — `integrations/mistral.py`, `config.py`, `requirements.txt`, `pyproject.toml`
- **Commit 2** (after Wave 2): `feat(agent): add Weave tracing, dynamic prompts, and token-aware memory` — `main.py`, `agent/loop.py`, `agent/scoring.py`, `agent/prompts.py`, `agent/memory.py`
- **Commit 3** (after Wave 3): `test(agent): add smoke tests for SDK, agent, and Weave integration` — `tests/test_mistral.py`, `tests/test_agent.py`, `tests/test_weave.py`

---

## Success Criteria

### Verification Commands
```bash
cd services/api && source .venv/bin/activate
pip install -r requirements.txt                              # Expected: success, mistralai and weave installed
python -c "from mistralai import Mistral"                    # Expected: no error
python -c "import weave"                                     # Expected: no error
python -c "from app.main import app"                         # Expected: no import errors
python -c "from app.integrations.mistral import chat_completion, chat_completion_stream, analyze_transcript"  # Expected: no error
python -c "from app.agent import run_turn, start_session, end_session, score_call, build_system_prompt"      # Expected: no error
python -m pytest tests/ -v                                   # Expected: ALL pass
curl http://localhost:8000/health                            # Expected: 200 OK
```

### Final Checklist
- [x] All "Must Have" present
- [x] All "Must NOT Have" absent
- [x] All tests pass
- [x] App starts with and without WANDB_API_KEY
- [x] No httpx imports remain in integrations/mistral.py
