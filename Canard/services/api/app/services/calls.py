# pyright: basic, reportMissingImports=false
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.agent import end_session
from app.config import settings
from app.db import queries
from app.services.analysis import run_post_call_analysis
from app.twilio_voice.client import make_outbound_call

LOGGER = logging.getLogger(__name__)


async def start_call(
    employee_id: str,
    script_id: str,
    caller_id: str | None = None,
    campaign_id: str | None = None,
    assignment_id: str | None = None,
) -> dict:
    employee = queries.get_employee(employee_id)
    if not employee:
        raise ValueError(f"Employee not found: {employee_id}")
    if not employee.get("is_active"):
        raise ValueError(f"Employee is not active: {employee_id}")

    script = queries.get_script(script_id)
    if not script:
        raise ValueError(f"Script not found: {script_id}")

    call_data: dict[str, str | None] = {
        "org_id": employee["org_id"],
        "employee_id": employee_id,
        "script_id": script_id,
        "status": "pending",
    }
    if caller_id:
        call_data["caller_id"] = caller_id
    if campaign_id:
        call_data["campaign_id"] = campaign_id
    if assignment_id:
        call_data["assignment_id"] = assignment_id

    call = queries.create_call(call_data)
    call_id = call["id"]

    webhook_url = f"{settings.public_base_url}/twilio/voice"
    status_url = f"{settings.public_base_url}/twilio/status"
    recording_url = f"{settings.public_base_url}/twilio/recording"

    try:
        twilio_sid = make_outbound_call(
            to_number=employee["phone"],
            webhook_url=webhook_url,
            status_callback_url=status_url,
            recording_callback_url=recording_url,
        )
        queries.update_call(
            call_id,
            {
                "phone_from": settings.twilio_from_number,
                "phone_to": employee["phone"],
                "twilio_call_sid": twilio_sid,
                "status": "ringing",
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    except Exception as exc:
        LOGGER.exception("Failed to initiate Twilio call for %s", call_id)
        queries.update_call(call_id, {"status": "failed"})
        raise RuntimeError(f"Failed to start call: {exc}") from exc

    updated_call = queries.get_call(call_id)
    return updated_call or call


def update_call_status(call_id: str, status: str) -> None:
    data: dict[str, str] = {"status": status}
    if status in ("completed", "failed", "no-answer", "busy"):
        data["ended_at"] = datetime.now(timezone.utc).isoformat()
    queries.update_call(call_id, data)


# TODO(db): Re-integrate when post-call analysis pipeline is complete.
# Currently the /twilio/status endpoint handles completion inline.
async def handle_call_completed(
    call_id: str,
    recording_url: str | None = None,
    recording_transcript: str | None = None,
) -> None:
    """
    Finalize a completed call: persist state, end agent session, run analysis.

    Args:
        call_id: Internal call UUID.
        recording_url: Twilio RecordingUrl if available.
        recording_transcript: Pre-transcribed text from ElevenLabs STT if available.
            When provided, analysis can use this instead of re-transcribing.
    """
    update_data: dict[str, str] = {
        "status": "completed",
        "ended_at": datetime.now(timezone.utc).isoformat(),
    }
    if recording_url:
        update_data["recording_url"] = recording_url

    queries.update_call(call_id, update_data)
    await end_session(call_id)

    try:
        await run_post_call_analysis(call_id, recording_transcript=recording_transcript)
    except Exception:
        LOGGER.exception("Post-call analysis failed for call %s", call_id)

