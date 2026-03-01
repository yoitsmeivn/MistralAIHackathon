# Decisions — agent-optimization-tracing

## Session: ses_358eff8f8ffebYyXD6HWlJMrS0 (2026-03-01)

### Wave Structure
- Wave 1: Task 1 (SDK migration) + Task 5 (config fields) — PARALLEL
- Wave 2: Task 2 (Weave decorators) + Task 3 (dynamic prompts) + Task 4 (memory) — PARALLEL, after Wave 1
- Wave 3: Task 6 (smoke tests) — SEQUENTIAL, after Wave 2
- Final Wave: F1-F4 reviews — PARALLEL, after all tasks

### SDK Choice
- Migrating from raw httpx to official `mistralai` SDK v1+
- Must use async API (client.chat.complete_async() or AsyncMistral)
- Lazy singleton pattern for client — one instance, lazy init

### Retry Strategy
- 3 retries with exponential backoff: 0.5s, 1.0s, 2.0s delays
- Only on HTTP 429/500/503 errors
- Use tenacity OR manual retry loop

### Streaming
- New separate function chat_completion_stream() — AsyncGenerator[str, None]
- Does NOT replace chat_completion() (preserves str return contract)
- Yields text delta chunks from client.chat.stream()

### Weave
- Added in Task 2 (NOT Task 1), but package installed in Task 1
- Graceful degradation: weave.init() in try/except, app works without WANDB_API_KEY

### Temperature
- chat_completion(): 0.8 (social engineering benefits from creativity)
- analyze_transcript(): 0.1 (deterministic scoring)
