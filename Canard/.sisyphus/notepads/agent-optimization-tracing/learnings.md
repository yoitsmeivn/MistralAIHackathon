# Learnings — agent-optimization-tracing

## Session: ses_358eff8f8ffebYyXD6HWlJMrS0 (2026-03-01)

### Target Files
- `services/api/app/integrations/mistral.py` — 101 lines, raw httpx, chat_completion() + analyze_transcript() + _extract_json_object()
- `services/api/app/config.py` — 52 lines, Pydantic Settings with _find_env_file() helper
- `services/api/app/agent/memory.py` — 65 lines, SessionStore with trim_messages(keep=20)
- `services/api/app/agent/prompts.py` — 24 lines, build_system_prompt(scenario_name, script_guidelines)
- `services/api/app/agent/loop.py` — 53 lines, start_session() / run_turn() / end_session()
- `services/api/app/agent/scoring.py` — 26 lines, format_transcript() / score_call()
- `services/api/app/main.py` — 54 lines, lifespan() is just `yield` currently
- `services/api/requirements.txt` — 11 lines, has httpx>=0.28.0, no mistralai/weave
- `services/api/pyproject.toml` — 23 lines, has httpx>=0.28.0, no mistralai/weave

### ElevenLabs _client() Pattern (replicate for Mistral)
```python
def _client() -> AsyncElevenLabs:
    if not settings.elevenlabs_api_key:
        raise ValueError("ELEVENLABS_API_KEY is required for ElevenLabs TTS/STT")
    return AsyncElevenLabs(api_key=settings.elevenlabs_api_key)
```
Note: ElevenLabs creates new client per-call. Mistral needs singleton (reuse connection).

### Key Call Sites (must not break)
- loop.py:47: `response = await chat_completion(llm_messages)` — returns str
- loop.py:51: `session_store.trim_messages(call_id)` — uses default keep=20
- scoring.py:4: `from app.integrations.mistral import analyze_transcript`
- scoring.py:26: `return await analyze_transcript(cleaned_transcript, scenario_description)`

### GUARDRAILS
- DO NOT touch: twilio_voice/routes.py, twilio_voice/session.py, integrations/elevenlabs.py, routes/*, db/queries.py, services/analysis.py
- chat_completion() MUST return str (not change signature)
- analyze_transcript() MUST return dict (not change signature)

## Session: task-1-sdk-migration (2026-02-28)

### Mistral SDK v1 Integration Notes
- `mistralai` v1 client exposes chat APIs on `client.chat`, not `Mistral.chat` class attribute.
- Async calls are `client.chat.complete_async(...)` and `client.chat.stream_async(...)`.
- Streaming events arrive as `CompletionEvent` with `event.data.choices[0].delta.content`.
- Timeout can be set at client construction with `timeout_ms=30000` and also passed per request.

### Retry/Resilience Pattern Used
- Manual retry loop with 3 attempts and delays `(0.5, 1.0, 2.0)`.
- Retries are limited to HTTP status codes `429`, `500`, `503` by extracting `SDKError.raw_response.status_code`.
- Lazy singleton `_get_client()` is used for connection reuse and centralized API key validation.

### Transcript Analysis Behavior
- `analyze_transcript()` first attempts JSON mode using `response_format={"type": "json_object"}`.
- Fallback preserves `_extract_json_object()` parsing path when JSON mode fails or returns non-JSON text.

## Task 5: Config Fields for W&B Weave and Mistral Tuning

### Completed
- Added 4 new fields to `services/api/app/config.py` Settings class:
  - `mistral_temperature: float = 0.8` (after Mistral section)
  - `mistral_max_context_tokens: int = 8000` (after Mistral section)
  - `wandb_api_key: str = ""` (new W&B Weave section)
  - `wandb_project: str = "canard"` (new W&B Weave section)

### Key Patterns
- All new fields have defaults so app works without env vars set
- Pydantic BaseSettings automatically reads from env vars if set
- W&B Weave section added after Safety section as per plan
- Mistral tuning fields added after mistral_model field

### Verification
- QA command passed: all 4 fields have correct defaults
- Evidence saved to `.sisyphus/evidence/task-5-config-defaults.txt`
- No linting errors (lsp_diagnostics clean)

### Notes
- Plan file NOT modified per Work_Context directive (Orchestrator manages plan state)
- File is 58 lines total (was 52 before)

## Task 3: Dynamic Prompt — build_system_prompt() Dual Signature (2026-02-28)

### Completed
- Rewrote `services/api/app/agent/prompts.py` (24 → 153 lines)
- `build_system_prompt()` now accepts both dict-based (new) and string-based (old) API
- Added `_parse_list_field()` helper for JSONB list/string handling
- Added `_build_legacy()` and `_build_from_dict()` internal helpers
- Extracted `SAFETY_GUARDRAILS` and `BEHAVIORAL_INSTRUCTIONS` as module-level constants

### Dual Signature Pattern
```python
def build_system_prompt(
    script_or_scenario: dict | str = "",
    script_guidelines: str = "",
    caller: dict | None = None,
    scenario_name: str = "",  # backward-compat kwarg
) -> str:
```
- `isinstance(script_or_scenario, dict)` → new API path
- `str` or `scenario_name` kwarg → legacy path

### Key Design Decisions
- Safety guardrails are ALWAYS appended (even when custom `system_prompt` base is used)
- `custom_base` from `script.get('system_prompt')` is used as base text, then dynamic sections layered on top
- `objectives` and `escalation_steps` handle both Python list and JSON string (JSONB from DB)
- Caller persona fields are optional; only rendered if non-empty
- `attack_type` falls back to caller dict if not set in script dict

### Verification
- New API test passed: 'authority_impersonation', 'get_password', 'NEVER ask for real passwords' all in output
- Old API test passed: `build_system_prompt(scenario_name='Test', script_guidelines='Be polite')` returns string with 'Test'
- Evidence saved to `.sisyphus/evidence/task-3-dynamic-prompt.txt` and `.sisyphus/evidence/task-3-backward-compat.txt`

## Task 4: Token-Aware Memory Trimming (2026-02-28)

### Completed
- Enhanced `services/api/app/agent/memory.py` (65 → 115 lines)
- Added module-level `estimate_tokens(text)` using `math.ceil(len(text) / 4 * 1.3)` (4 chars/token + 30% safety margin)
- Replaced naive `trim_messages(keep=20)` with token-budget-aware version
- Added `get_context_usage(call_id)` method returning `{estimated_tokens, message_count, budget, utilization_pct}`

### Token Trim Algorithm
- System message (index 0) always preserved
- Non-system messages trimmed from oldest first until within `settings.mistral_max_context_tokens` budget
- Minimum 4 messages (2 exchange pairs) always preserved after trim
- Falls back to `keep` limit as safety net when already within budget
- Circular import avoided by importing `from app.config import settings` inside method body

### Verification
- Token-trim test: 500-char system + 50×200-char messages → 21 messages after trim (within 8000 token budget)
- Context usage test: `{'estimated_tokens': 8, 'message_count': 2, 'budget': 8000, 'utilization_pct': 0.1}` returned correctly
- Evidence saved to `.sisyphus/evidence/task-4-token-trim.txt` and `.sisyphus/evidence/task-4-context-usage.txt`
- `session_store = SessionStore()` singleton at module level unchanged
- `RLock` pattern unchanged

## Task 2: W&B Weave Initialization and @weave.op() Decorators (2026-02-28)

### Completed
- Added conditional weave import + `_HAS_WEAVE` flag to `main.py`
- Added `weave.init(settings.wandb_project)` in lifespan with try/except (warning only on failure)
- Added `_op` fallback pattern to 3 files: `integrations/mistral.py`, `agent/loop.py`, `agent/scoring.py`
- Applied `@_op` decorator to 7 functions total:
  - mistral.py: `chat_completion`, `chat_completion_stream`, `analyze_transcript`
  - loop.py: `start_session`, `end_session`, `run_turn`
  - scoring.py: `score_call`

### Key Patterns
- `_op = _weave.op` alias pattern allows graceful fallback when weave not installed
- `try/except ImportError` at module level — no runtime cost if weave absent
- `weave.init()` wrapped in try/except Exception — logs warning, never raises
- App loads cleanly with `WANDB_API_KEY=''` (weave init fails gracefully)
- weave 0.52.29 installed in venv

### Verification
- `WANDB_API_KEY='' python -c "from app.main import app; print('App loaded OK')"` → OK
- `grep -n '@_op'` shows 7 decorator occurrences across 3 files
- All 14 existing tests pass (14 passed, 2 warnings in 1.54s)
- Evidence saved to `.sisyphus/evidence/task-2-no-wandb-key.txt` and `.sisyphus/evidence/task-2-weave-decorators.txt`

### Notes
- `main.py` imports reorganized: `logging` added after `asynccontextmanager`, weave try/except block before `from app.config import settings`
- The `_op` fallback `def _op(fn): return fn` is a no-op identity function — zero overhead when weave absent
