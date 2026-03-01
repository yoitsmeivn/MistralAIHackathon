- Added manual µ-law RMS energy detection and three-frame threshold gating for Twilio barge-in, with [3J[H[2J emitted only while agent speech is active and after cooldown.
- Added shared silence state across stream tasks: speech timestamp + nudge flag reset on new STT transcript, nudge at ~5s and goodbye at ~15s.
- Silence timeout now closes websocket and signals queue shutdown after goodbye to avoid hanging  with a completed silence task.
- Correction: Twilio clear event is emitted as JSON event `clear` with streamSid when barge-in threshold is met while agent_is_speaking.
- Added silence timeout shutdown path that sets disconnect_reason, pushes None to audio queue, and closes websocket to terminate stream tasks cleanly.

- Silence monitor must treat Twilio playback as non-response time by resetting  while  is true.
- Twilio  and barge-in [3J[H[2J events now both reset silence timer and clear nudge state so the user gets a full response window after agent playback/interruption.
- Added / session state to support mark-timeout safety clearing () when a mark acknowledgement is missing.

- Silence monitor must treat Twilio playback as non-response time by resetting `last_speech_time` while `agent_is_speaking` is true.
- Twilio `mark` and barge-in `clear` events now both reset silence timer and clear nudge state so the user gets a full response window after agent playback/interruption.
- Added `audio_send_time` and `audio_send_bytes` session state to support mark-timeout safety clearing (expected_duration + 5s) when a mark acknowledgement is missing.

## Voice Agent Brevity Optimization (2026-03-01)

### Changes Made
1. **max_tokens reduction**: Changed from 50 to 30 tokens in `loop.py:65`
   - 30 tokens ≈ 120 characters ≈ ~5 seconds of audio
   - Enforces single-sentence responses for phone naturalness

2. **BEHAVIORAL_INSTRUCTIONS rewrite**: Tightened prompt in `prompts.py:51-73`
   - Added explicit "ONE short sentence" rule with "10 words max when possible"
   - Included concrete examples of target response length
   - Added "I never re-explain why I'm calling" to prevent re-introduction
   - Removed filler word instructions ("um", "uh") — ElevenLabs renders these as distinct words
   - Kept conversation awareness and natural speech patterns

### Key Insight
The model was ignoring brevity instructions in the old prompt. The new version:
- Leads with the constraint ("PHONE CALL RULE: I say ONE short sentence")
- Provides concrete examples showing exact target length
- Uses aggressive language ("shut up and wait", "I say my piece and STOP")
- Removes competing instructions that encouraged longer responses

### Test Results
- All 26 tests pass
- LSP diagnostics clean on both modified files
- No breaking changes to function signatures or other constants

### Expected Outcome
Agent responses should now be ~1 sentence, ~5 seconds of audio, matching natural phone conversation patterns instead of the previous ~10-second speeches.

## Voice Loop Debounce + Barge-In Retune (2026-03-01)

- Replaced `_agent_loop()` in `services/api/app/twilio_voice/routes.py` with a debounced turn builder: committed STT fragments are accumulated and only processed after 1.5s without new commits.
- Added `agent_is_speaking` wait gate before response generation in `_process_accumulated()` so user turns are never processed while outbound agent audio is still active.
- Debounce behavior uses cancellable timer tasks per new STT commit and final-drain handling in `finally` to avoid dropping the last partial utterance on disconnect.
- Lowered Twilio barge-in trigger constants in `services/api/app/twilio_voice/routes.py` to `_BARGE_IN_THRESHOLD = 300` and `_BARGE_IN_FRAMES = 2` for faster/softer interruption capture.
- Raised `chat_completion(..., max_tokens=50)` in `services/api/app/agent/loop.py` to avoid clipped mid-sentence replies; tone/turn control now comes from behavioral prompt instead of hard truncation.
- Rewrote `BEHAVIORAL_INSTRUCTIONS` in `services/api/app/agent/prompts.py` for spoken-first dialogue pacing: one thought per turn, acknowledgement-first continuity, explicit wait-after-turn behavior, and natural close/clarification handling.

## Voice Parameter Retune Pass (2026-03-01)

- Raised barge-in gating in `services/api/app/twilio_voice/routes.py`: `_BARGE_IN_THRESHOLD` 300 -> 1000 and `_BARGE_IN_FRAMES` 2 -> 5 to suppress ambient/noise interruptions.
- Reduced debounce delay in `services/api/app/twilio_voice/routes.py` from `1.5` to `0.4` seconds to remove avoidable post-STT response lag.
- Relaxed silence monitor timing in `services/api/app/twilio_voice/routes.py`: nudge `5.0` -> `8.0`, goodbye `15.0` -> `20.0` to reduce premature "you there" and hangup behavior.
- Tightened agent response length in `services/api/app/agent/loop.py` by changing `chat_completion(..., max_tokens=50)` to `max_tokens=35` for single-short-turn outputs.
- Replaced `BEHAVIORAL_INSTRUCTIONS` in `services/api/app/agent/prompts.py` with explicit ultra-short phone-turn constraints (5-12 words, one thought then wait).
- Validation: LSP diagnostics clean on changed files; `python -m pytest tests/ -v` passed with 26/26 tests green.

## STT Barge-In + Dialogue Flow Stabilization (2026-03-01)

- Added STT-confirmed barge-in handling in `services/api/app/twilio_voice/routes.py`: when a committed transcript arrives during `agent_is_speaking`, emit Twilio `clear`, force `agent_is_speaking=False`, and publish a `barge_in` event with `source="stt"`.
- Removed hard blocking wait behavior in `_process_accumulated()` and replaced it with short grace + forced clear fallback, preventing 3-10s stalls from delayed/missing `mark` events.
- Reduced mark timeout fallback in silence monitor from `expected_duration + 10.0` to `+ 3.0` for faster recovery from playback-state desync.
- Reduced debounce from `0.4s` to `0.3s` to tighten turn-taking latency while still coalescing rapid STT commits.
- Updated `last_speech_time` right before LLM generation to suppress false silence nudges during model/TTS processing windows.
- Replaced `BEHAVIORAL_INSTRUCTIONS` with explicit phased flow (`greet -> confirm -> explain -> extract`) and hard ban on "are you there/can you hear me" spam.
- Reduced LLM output cap from `max_tokens=35` to `25` and retuned ElevenLabs voice settings to `stability=0.45`, `similarity_boost=0.75`, `speed=1.05` for shorter, more human responses.
- Validation: LSP diagnostics clean on all modified files and `python -m pytest tests/ -v` passed (26/26).
