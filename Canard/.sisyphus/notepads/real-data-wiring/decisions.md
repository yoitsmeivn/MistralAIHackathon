## 2026-02-28 Decisions

### Model: Switch to ministral-3b-latest
- 376ms avg vs 423ms for 8b — ~12% faster
- Quality is sufficient for phone conversations (1-2 sentence responses)
- User explicitly asked for faster model

### Employee data in prompt
- _init_agent_session() will also fetch employee from call record
- build_system_prompt() will accept optional employee dict
- Prompt will include: target name, department, job_title
- This makes social engineering realistic (agent knows who it's calling)


## 2026-03-01 Decisions

### Model: Switch back to ministral-8b-latest
- Quality and grounding were prioritized over a small latency delta.
- Kept latency constrained by pairing 8b with `max_tokens=80` in the turn loop.

### Context wiring scope
- No query-layer changes were made; existing `get_employee()` and `get_organization()` were reused.
- Context enrichment is isolated to session init + prompt builder to avoid touching analysis/transcript pipelines.
