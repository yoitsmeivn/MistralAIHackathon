## 2026-02-28 ElevenLabs SDK v2.37.0 API Research

### TTS — AsyncTextToSpeechClient.convert()
- **Return type**: `typing.AsyncIterator[bytes]` (line 614 of SDK source)
- It is an **async generator** — uses `yield` internally via `async for _chunk in r.data: yield _chunk`
- **CANNOT be awaited** — must iterate with `async for`
- Correct usage: `async for chunk in client.text_to_speech.convert(...): ...`
- Parameters: voice_id, text, model_id, output_format, voice_settings, optimize_streaming_latency — ALL VALID
- `voice_settings` type is `VoiceSettings` (from elevenlabs.types)
- `optimize_streaming_latency` is still valid (int 0-4)

### Batch STT — AsyncSpeechToTextClient.convert()
- **Return type**: `SpeechToTextConvertResponse` (awaitable, NOT a generator)
- `cloud_storage_url` IS a valid parameter (line 217/267 of SDK source)
- `file` parameter type is `core.File` — accepts tuple `(filename, bytes, mime_type)`
- Response has `.text` attribute for transcript
- The 401 error on Twilio recording URLs is because Twilio requires auth — NOT an SDK bug
- Fix: download recording with Twilio auth, then pass bytes via `file` param

### Realtime STT WebSocket
- URL: `wss://api.elevenlabs.io/v1/speech-to-text/realtime`
- Valid query params (from AsyncAPI spec):
  - `model_id` (string) — e.g. "scribe_v1"
  - `token` (string) — alternative auth
  - `include_timestamps` (boolean, default false) — VALID
  - `include_language_detection` (boolean, default false) — VALID
  - `audio_format` (enum: pcm_8000, pcm_16000, pcm_22050, pcm_24000, pcm_44100, pcm_48000, ulaw_8000) — default pcm_16000
  - `language_code` (string)
  - `commit_strategy` (enum: manual, vad) — default manual
  - `vad_silence_threshold_secs` (float, default 1.5)
  - `vad_threshold` (float, default 0.4)
  - `min_speech_duration_ms` (int, default 100)
  - `min_silence_duration_ms` (int, default 100)
  - `enable_logging` (boolean, default true)
- Auth: `xi-api-key` header OR `token` query param
- Client sends: `InputAudioChunkPayload` with message_type, audio_base_64, commit, sample_rate (ALL REQUIRED)
- Server sends: session_started, partial_transcript, committed_transcript, various error types
- **The current code's WebSocket params look correct** — the 1008 error may be from boolean params being strings

### Key Insight: Boolean Query Params
The WebSocket URL is built with string params like `include_timestamps=false` but the API expects boolean values.
In a WebSocket URL query string, `false` is a string, not a boolean. The API may be rejecting this.
**Fix**: Either remove these params (they default to false anyway) or use proper encoding.

## 2026-02-28 Implementation Notes
- Converted `_PHONE_VOICE_SETTINGS` to `VoiceSettings(...)` so `text_to_speech.convert()` receives the SDK-typed object.
- Fixed TTS generation by iterating `async for chunk in client.text_to_speech.convert(...)` and concatenating chunks.
- Realtime STT ws query now uses only `model_id`, `audio_format`, and `commit_strategy` (+ optional `language_code`) to avoid `1008 invalid_request`.
- Extended realtime STT error handling for `commit_throttled`, `unaccepted_terms`, `queue_overflow`, `chunk_size_exceeded`, and `insufficient_audio_activity`.
- Replaced URL-based STT `cloud_storage_url` flow with authenticated download (Twilio Basic Auth when needed) and byte upload via `speech_to_text(...)`.

## 2026-02-28 TTS Sanitization Follow-up
- Added `sanitize_for_tts(text: str) -> str` in `app/integrations/elevenlabs.py` before `text_to_speech()`.
- Regex sanitization now strips parenthesized/bracketed stage directions, short `*action*` markers, `.period`/`.dot`, common textual laugh tokens, markdown emphasis, and emoji.
- Sanitization is now applied at both Twilio TTS call sites: initial greeting and every agent turn.
- Prompt constraints were tightened in `BEHAVIORAL_INSTRUCTIONS` to explicitly forbid stage directions, markdown, and emoji in model output.

## 2026-02-28 Randomized Attack Vectors Implementation
- `_init_agent_session()` now normalizes JSON/list fields safely from either list or JSON string before random selection.
- Objective selection strategy: random `1..2` objectives per call (when >1 objective exists), providing variation for repeated calls to the same employee.
- Escalation strategy variation: random shuffle + random `2..3` subset (when >2 tactics exist), preserving progressive pressure while varying approach.
- Prompt builder remains API-compatible: `build_system_prompt()` signature unchanged, while `_build_from_dict()` can consume `selected_objectives` and `selected_escalation_steps` override fields.
- `run_turn()` response cap of `max_tokens=150` keeps LLM output phone-length and lowers response generation latency.
