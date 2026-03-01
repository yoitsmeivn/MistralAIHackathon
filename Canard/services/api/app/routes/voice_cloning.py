# pyright: basic
"""
Voice cloning API routes.

POST /api/employees/{employee_id}/clone-voice
  - Triggers ElevenLabs IVC voice cloning for an employee
  - Requires a completed call recording at recordings/{employee_id}/{employee_id}.wav
  - Stores voice_id on employee record and metadata in deep-fakes bucket
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.auth.middleware import CurrentUser
from app.services.voice_cloning import clone_employee_voice

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/api/employees", tags=["voice-cloning"])


class VoiceCloneResponse(BaseModel):
    voice_id: str
    employee_id: str
    status: str
    message: str


@router.post("/{employee_id}/clone-voice", response_model=VoiceCloneResponse)
async def api_clone_employee_voice(
    employee_id: str,
    user: CurrentUser,
) -> VoiceCloneResponse:
    """
    Create an ElevenLabs Instant Voice Clone (IVC) from the employee's recorded WAV.

    Prerequisites:
    - Employee must have a completed call with a recording stored at:
      Supabase storage: recordings/{employee_id}/{employee_id}.wav
    - ELEVENLABS_API_KEY must be configured

    The cloned voice_id is:
    - Stored on the employee record (voice_id column)
    - Stored as metadata JSON in Supabase storage: deep-fakes/{employee_id}/{employee_id}.json

    This voice can then be used for future calls to simulate the employee's voice.
    """
    try:
        result = await clone_employee_voice(employee_id)
        return VoiceCloneResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        LOGGER.exception("Voice cloning failed for employee_id=%s", employee_id)
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {exc}")
