# Canard Persistence Polish - Learnings

## Phone Conversation Realism Improvements (2026-03-01)

### Task: Tighten BEHAVIORAL_INSTRUCTIONS for Phone Realism

**Problem Identified:**
- Agent output included stage directions in asterisks: `*[pause]*`, `*[listen]*`
- Markdown formatting appeared: `**bold**`, `*italic*`
- Responses were too long (2-3 sentences when 1 would be natural)
- Agent repeated its name after every exchange
- Agent sometimes answered its own questions without waiting

**Solution Applied:**
Updated `BEHAVIORAL_INSTRUCTIONS` constant in `services/api/app/agent/prompts.py` (lines 17-36) with:

1. **Explicit Formatting Prohibitions:**
   - Added "CRITICAL: Output is spoken words ONLY" header
   - Listed forbidden patterns: asterisks, brackets, parentheses, markdown, emoji
   - Included specific examples: `*[pause]*`, `*[listen]*`, `**bold**`, `[action]`, `(aside)`
   - Added consequence: "If you write any of these, the call fails and TTS breaks"

2. **Natural Speech Patterns:**
   - Specified filler words: 'umm', 'uh', 'so', 'right', 'you know'
   - Added guidance: "like a real person on a phone call"
   - Introduced pause notation: Use '...' for brief natural pauses

3. **Turn-Taking Rules:**
   - Emphasized: "Say ONE thing. Ask ONE question. Then STOP and wait."
   - Prohibited: stacking questions, answering own questions, continuing after asking
   - Added response length constraint: "1 to 2 sentences max"

4. **Name Repetition Prevention:**
   - Explicit rule: "You already greeted them — never re-introduce yourself or repeat your name"

**Key Design Decisions:**
- Kept constant name and parenthesized string concatenation style unchanged
- Preserved existing good rules about not fabricating facts
- Made formatting rules VERY forceful with multiple restatements (LLM needs repetition)
- Used concrete examples of forbidden output to prevent model deviation
- Kept opening line "How you talk on this call:\n" unchanged

**Test Results:**
- All 26 existing tests pass ✓
- No syntax errors (LSP diagnostics clean) ✓
- No changes to other constants (STREAM_GREETING, SAFETY_GUARDRAILS, SOCIAL_ENGINEERING_TACTICS, RESISTANCE_HANDLING) ✓
- No changes to function signatures or imports ✓

**Expected Impact:**
- Reduced asterisk/bracket stage directions in agent output
- Cleaner TTS audio (no non-speakable characters)
- More natural phone conversation flow
- Better turn-taking behavior
- Fewer name repetitions mid-call

## Recording Persistence to Supabase (2026-03-01)

### Task: Persist Twilio recording audio and metadata in /twilio/recording

**What worked:**
- Keep STT first, then run storage persistence in a separate `try/except` so transcription flow stays intact even if storage fails.
- Build Twilio download URL as `RecordingUrl.rstrip("/") + ".wav"` and fetch via `httpx.AsyncClient` using HTTP Basic Auth `(twilio_account_sid, twilio_auth_token)`.
- Upload bytes to Supabase storage using `get_supabase().storage.from_("recordings").upload(...)` with a stable path format `{call_id}/{recording_sid}.wav`.
- Persist `recording_url` (Supabase public URL), `recording_sid`, and parsed `duration_seconds` in one `_update_call_safe` call.

**Implementation notes:**
- `storage.upload()` typing in this repo needed `cast(Any, upload_options)` for pyright compatibility with Supabase `FileOptions` typing.
- Use `cfg.supabase_url.rstrip("/")` before composing `/storage/v1/object/public/recordings/{path}` to avoid double slashes.
