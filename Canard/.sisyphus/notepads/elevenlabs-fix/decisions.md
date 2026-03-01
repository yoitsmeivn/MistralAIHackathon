## 2026-03-01 Research Findings for Three Improvements

### 1. TTS Artifact Stripping
- ZERO text sanitization exists between Mistral output and ElevenLabs TTS
- The prompt says "Output format: Just text, no JSON, no markdown" but doesn't forbid stage directions
- ElevenLabs does NOT natively interpret (laughs), [pause], etc. — reads them literally
- Need: regex-based sanitize_for_tts() function + stronger prompt instructions
- Patterns to strip: (laughs), (chuckles), *laughs*, [pause], .period, emoji, markdown

### 2. Mistral Model Speed Benchmarks (3-run averages)
- ministral-3b-latest:  365ms avg — fastest but quality may suffer for social engineering
- ministral-8b-latest:  354ms avg — BEST balance of speed + quality
- mistral-tiny-latest:  421ms avg
- mistral-small-latest: 477ms avg
- mistral-medium-2508:  539ms avg (current) — slowest

DECISION: Switch to ministral-8b-latest (35% faster than medium, good quality)
- Also reduce max_tokens from default to 100 (phone responses are short)
- Keep temperature at 0.8

### 3. Randomized Attack Vectors
- scripts table has: objectives (JSONB array), escalation_steps (JSONB array)
- Currently only 2 scripts: "IT Helpdesk Password Reset" and "Urgent CEO Wire Transfer"
- 38 employees across 8 departments
- The system always uses the same script objectives — no randomization
- Need: pick a random subset of objectives per call, or rotate which objective to focus on
- Better approach: add more scripts with different info targets, and randomly assign per call
- The prompt already supports objectives and escalation_steps from the script dict
- Key insight: the randomization should happen at CALL INITIATION time, not in the prompt builder

### 4. Stage Direction Defense-in-Depth
- Keep both layers: prompt-level prohibition and runtime sanitization before TTS.
- Apply sanitization directly at Twilio route call sites so all spoken content is filtered regardless of agent output quality.
- Implement regex patterns as module-level compiled constants to avoid recompiling on each turn.

## 2026-02-28 Randomized Objective Selection + Response Cap

- Randomization is applied in `twilio_voice/routes.py:_init_agent_session()` immediately after loading script data and before `build_system_prompt()`.
- Per call, objectives now select a random 1-2 subset when multiple objectives exist; escalation tactics select a random ordered 2-3 subset when more than two exist.
- Script data is copied (`script = {**script, ...}`) so persisted DB script content remains unchanged.
- Prompt generation accepts optional `selected_objectives` / `selected_escalation_steps` fields, while preserving backward compatibility with existing `objectives` / `escalation_steps`.
- `agent/loop.py:run_turn()` now calls `chat_completion(..., max_tokens=150)` to keep phone replies short and reduce latency.
