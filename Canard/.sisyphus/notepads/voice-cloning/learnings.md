# Voice Cloning Feature — Learnings

## 2026-03-01 — Initial Analysis

### Codebase Patterns
- Python FastAPI backend in `services/api/app/`
- ElevenLabs SDK: `elevenlabs>=1.0.0`, uses `AsyncElevenLabs` client
- Supabase storage: `get_supabase().storage.from_("recordings").upload(path, bytes, options)`
- Recording storage path currently: `{call_id}/{RecordingSid}.wav` in `recordings` bucket
- Employee model has `id` (UUID), `org_id`, `full_name`, `email`, `phone`
- DB queries via `app.db.queries` module using Supabase Python SDK
- Config via `app.config.settings` (pydantic-settings)
- Routes follow pattern: `APIRouter(prefix="/api/...", tags=[...])`

### Recording Storage Change Required
- Current path: `{call_id}/{RecordingSid}.wav`
- Required path: `{employee_id}/{employee_id}.wav`
- The employee_id is available in the call record: `call_record.get("employee_id")`
- The recording callback is in `twilio_voice/routes.py` at `@router.post("/recording")`
- Need to fetch employee_id from call record before uploading

### ElevenLabs Voice Cloning (IVC)
- ElevenLabs SDK: `AsyncElevenLabs` has `voices.add()` for IVC
- IVC API: POST to `https://api.elevenlabs.io/v1/voices/add`
  - multipart form: `name`, `files[]` (audio files), `description`, `labels`
  - Returns: `{ "voice_id": "..." }`
- The SDK method: `client.voices.add(name=..., files=[...], description=...)`
- Voice ID should be stored on the employee record (need `voice_id` column in employees table)
- Deep fakes bucket: `deep-fakes` in Supabase storage
- Store a JSON metadata file: `{employee_id}/{employee_id}.json` with voice_id, created_at, etc.

### Key Files
- `services/api/app/twilio_voice/routes.py` — recording upload (line ~414)
- `services/api/app/integrations/elevenlabs.py` — ElevenLabs client
- `services/api/app/db/queries.py` — DB queries
- `services/api/app/routes/employees.py` — employee routes
- `services/api/app/config.py` — settings
- `services/api/app/main.py` — router registration

### ElevenLabs SDK Voice Add
```python
from elevenlabs.client import AsyncElevenLabs
client = AsyncElevenLabs(api_key=...)
# IVC: pass audio bytes as file-like objects
result = await client.voices.add(
    name="Employee Name",
    files=[audio_bytes_io],  # list of file-like objects
    description="Voice clone for employee {id}"
)
voice_id = result.voice_id
```

### Supabase Storage for Deep Fakes
- New bucket: `deep-fakes` (must be created in Supabase dashboard or via API)
- Path: `{employee_id}/{employee_id}.json` — metadata JSON
- The bucket creation can be done programmatically via `get_supabase().storage.create_bucket("deep-fakes", options={"public": False})`

# Voice Cloning Feature - Learnings

## Patterns Observed
- Services use `from app.db import queries` for DB access, `from app.db.client import get_supabase` for storage
- Routes follow `APIRouter(prefix="/api/<resource>", tags=["<tag>"])` pattern
- Auth uses `CurrentUser` type annotation from `app.auth.middleware`
- All files start with `# pyright: basic` and `from __future__ import annotations`
- Supabase storage upload uses `cast(Any, {...})` for options dict
- Router registration in main.py: import as `<name>_router`, then `app.include_router(<name>_router)`
- DB queries use `_execute()` + `_first_or_none()` helpers consistently
- Error handling: services raise `ValueError`, routes catch and convert to `HTTPException`

## ElevenLabs IVC SDK
- `AsyncElevenLabs(api_key=...).voices.ivc.create()` for instant voice cloning
- Files param: list of tuples `(filename, bytes, content_type)`
- Returns object with `.voice_id` attribute
- `remove_background_noise=True` recommended for call recordings

## Supabase Storage
- `get_supabase().storage.from_(bucket).download(path)` returns bytes
- `get_supabase().storage.create_bucket(name, options={"public": False})` — idempotent with try/except
- Upload with upsert: `cast(Any, {"content-type": "...", "upsert": "true"})`

## Verification
- All 3 Python imports pass: service, routes, queries
- Route registered in FastAPI app (clone-voice path confirmed)
- LSP clean on all 4 files (queries.py has pre-existing error in get_subordinates, unrelated)
