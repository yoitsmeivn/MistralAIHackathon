# pyright: basic
"""
ElevenLabs Instant Voice Cloning (IVC) service.

Flow:
1. Fetch the employee's WAV recording from Supabase storage bucket "recordings"
   Path: {employee_id}/{employee_id}.wav
2. Use ElevenLabs SDK to create an IVC voice clone from the audio
3. Store the voice_id on the employee record in the DB
4. Store metadata JSON in Supabase storage bucket "deep-fakes"
   Path: {employee_id}/{employee_id}.json
5. Return the voice_id
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, cast

from elevenlabs.client import AsyncElevenLabs

from app.config import settings
from app.db import queries
from app.db.client import get_supabase

LOGGER = logging.getLogger(__name__)

_DEEP_FAKES_BUCKET = "deep-fakes"


def _ensure_deep_fakes_bucket() -> None:
    """Create the deep-fakes bucket if it doesn't exist."""
    try:
        get_supabase().storage.create_bucket(
            _DEEP_FAKES_BUCKET,
            options={"public": False},
        )
        LOGGER.info("Created Supabase storage bucket: %s", _DEEP_FAKES_BUCKET)
    except Exception:
        # Bucket likely already exists — ignore
        pass


async def clone_employee_voice(employee_id: str) -> dict:
    """
    Clone an employee's voice using ElevenLabs Instant Voice Cloning (IVC).

    Prerequisites:
    - Employee must exist in the DB
    - A WAV recording must exist in Supabase storage at:
      recordings/{employee_id}/{employee_id}.wav

    Returns:
        dict with keys: voice_id, employee_id, status, message

    Raises:
        ValueError: if employee not found, recording not available, or cloning fails
    """
    if not settings.elevenlabs_api_key:
        raise ValueError("ELEVENLABS_API_KEY is not configured")

    # 1. Fetch employee
    employee = queries.get_employee(employee_id)
    if not employee:
        raise ValueError(f"Employee not found: {employee_id}")

    employee_name = employee.get("full_name") or f"Employee {employee_id}"
    LOGGER.info(
        "Starting voice clone for employee: %s (%s)", employee_name, employee_id
    )

    # 2. Download WAV recording from Supabase storage
    recording_path = f"{employee_id}/{employee_id}.wav"
    try:
        audio_bytes: bytes = (
            get_supabase().storage.from_("recordings").download(recording_path)
        )
        LOGGER.info(
            "Downloaded recording for employee %s: %d bytes",
            employee_id,
            len(audio_bytes),
        )
    except Exception as exc:
        raise ValueError(
            f"No recording found for employee {employee_id}. "
            f"Expected at recordings/{recording_path}. "
            f"Make sure a call has been completed for this employee first. "
            f"Error: {exc}"
        ) from exc

    if not audio_bytes:
        raise ValueError(
            f"Recording for employee {employee_id} is empty. "
            "A valid WAV recording is required for voice cloning."
        )

    # 3. Create ElevenLabs IVC voice clone
    try:
        client = AsyncElevenLabs(api_key=settings.elevenlabs_api_key)
        result = await client.voices.ivc.create(
            name=employee_name,
            files=[(f"{employee_id}.wav", audio_bytes, "audio/wav")],
            description=f"Voice clone for employee {employee_id} ({employee_name})",
            remove_background_noise=True,
        )
        voice_id: str = result.voice_id
        LOGGER.info(
            "ElevenLabs IVC created voice_id=%s for employee %s", voice_id, employee_id
        )
    except Exception as exc:
        LOGGER.exception("ElevenLabs IVC failed for employee %s", employee_id)
        raise ValueError(f"Voice cloning failed: {exc}") from exc

    # 4. Persist voice_id on employee record
    try:
        queries.update_employee(employee_id, {"voice_id": voice_id})
        LOGGER.info("Updated employee %s with voice_id=%s", employee_id, voice_id)
    except Exception as exc:
        LOGGER.warning(
            "Failed to persist voice_id on employee %s: %s", employee_id, exc
        )
        # Non-fatal — voice was cloned, just couldn't save to DB

    # 5. Store metadata in deep-fakes bucket
    metadata = {
        "employee_id": employee_id,
        "employee_name": employee_name,
        "voice_id": voice_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "active",
        "source_recording": f"recordings/{recording_path}",
        "clone_type": "ivc",
    }
    metadata_path = f"{employee_id}/{employee_id}.json"
    try:
        _ensure_deep_fakes_bucket()
        get_supabase().storage.from_(_DEEP_FAKES_BUCKET).upload(
            metadata_path,
            json.dumps(metadata, indent=2).encode("utf-8"),
            cast(Any, {"content-type": "application/json", "upsert": "true"}),
        )
        LOGGER.info(
            "Stored voice clone metadata in %s/%s", _DEEP_FAKES_BUCKET, metadata_path
        )
    except Exception as exc:
        LOGGER.warning(
            "Failed to store voice clone metadata for employee %s: %s", employee_id, exc
        )
        # Non-fatal — voice was cloned, metadata storage is best-effort

    return {
        "voice_id": voice_id,
        "employee_id": employee_id,
        "status": "success",
        "message": f"Voice clone created for {employee_name}",
    }
