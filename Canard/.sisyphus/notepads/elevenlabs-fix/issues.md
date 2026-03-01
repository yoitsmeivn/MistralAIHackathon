## 2026-02-28 Live Call Test Results

### ElevenLabs Fixes — VERIFIED WORKING
- Bug 1 (TTS): FIXED — Rachel voice (21m00Tcm4TlvDq8ikWAM) generates audio successfully. Veda Sky requires paid plan.
- Bug 2 (Realtime STT): FIXED — model changed from scribe_v1 to scribe_v2_realtime. WebSocket connects and returns session_started.
- Bug 3 (Recording STT): FIXED — downloads with Twilio auth. But Twilio recording URLs return 404 (may need .wav suffix appended).

### NEW BLOCKERS DISCOVERED

#### Mistral API Key Invalid (401 Unauthorized)
- The MISTRAL_API_KEY in .env (321D3EDE-63DD-4F4C-B83C-AA9119A6738B) returns 401.
- This blocks the agent from generating any responses.
- Ivan needs to provide a valid Mistral API key.
- The key format looks like a UUID — Mistral keys typically start with different patterns.

#### Twilio Recording URL 404
- speech_to_text_from_url() downloads the recording but gets 404.
- Twilio recording URLs may need `.wav` or `.json` suffix appended.
- Example failing URL: https://api.twilio.com/2010-04-01/Accounts/ACe39.../Recordings/REfc357...
- Low priority — only affects post-call transcript analysis, not live conversation.

#### ElevenLabs Free Plan Limitation
- Voice "Veda Sky" (0fbdXLXuDBZXm2IHek4L) requires paid ElevenLabs plan.
- Switched to default "Rachel" (21m00Tcm4TlvDq8ikWAM) which works on free plan.
- If Ivan upgrades ElevenLabs, can switch back to Veda Sky in .env.

## 2026-02-28 TTS Sanitization Work
- No new blockers during implementation.
- `python -m pytest tests/ -v` passed (26/26) after adding sanitize + prompt constraints.
