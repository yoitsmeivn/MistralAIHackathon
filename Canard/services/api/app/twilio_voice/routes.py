# pyright: basic, reportMissingImports=false
from __future__ import annotations

import logging

from fastapi import APIRouter, Form, Response

from app.agent import (
    build_system_prompt,
    redact_pii,
    run_turn,
    session_store,
    start_session,
)
from app.db import queries
from app.integrations.elevenlabs import text_to_speech
from app.services.calls import (
    get_or_create_call_for_webhook,
    handle_call_completed,
    update_call_status,
)
from app.services.media import get_audio_url, store_audio
from app.twilio_voice import twiml

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/twilio", tags=["twilio"])


@router.post("/voice")
async def twilio_voice(CallSid: str = Form(""), CallStatus: str = Form("")) -> Response:
    LOGGER.info("Twilio /voice webhook: CallSid=%s Status=%s", CallSid, CallStatus)
    if CallSid:
        get_or_create_call_for_webhook(CallSid)
    twiml_response = twiml.consent_gather_response()
    return Response(content=twiml_response, media_type="application/xml")


@router.post("/gather")
async def twilio_gather(
    CallSid: str = Form(""),
    SpeechResult: str = Form(""),
    Digits: str = Form(""),
) -> Response:
    LOGGER.info(
        "Twilio /gather: CallSid=%s Digits=%s Speech=%s", CallSid, Digits, SpeechResult
    )

    call = queries.get_call_by_sid(CallSid)
    if not call:
        LOGGER.error("No call record for CallSid=%s", CallSid)
        return Response(
            content=twiml.say_and_hangup("An error occurred. Goodbye."),
            media_type="application/xml",
        )

    call_id = call["id"]
    consented = call.get("consented", False)

    if not consented:
        user_consents = Digits == "1" or "yes" in SpeechResult.lower()
        if not user_consents:
            queries.update_call(call_id, {"status": "no-consent", "consented": False})
            return Response(
                content=twiml.say_and_hangup(
                    "No problem. Thank you for your time. Goodbye."
                ),
                media_type="application/xml",
            )

        queries.update_call(call_id, {"consented": True, "status": "in-progress"})

        scenario = queries.get_scenario(call["scenario_id"])
        if not scenario:
            return Response(
                content=twiml.say_and_hangup("Configuration error. Goodbye."),
                media_type="application/xml",
            )

        system_prompt = build_system_prompt(
            scenario["name"], scenario["script_guidelines"]
        )
        await start_session(call_id, call["scenario_id"], system_prompt)
        session_store.set_consented(call_id)

        first_response = await run_turn(
            call_id,
            "The participant has consented to the training exercise. Begin the scenario.",
        )

        audio_bytes = await text_to_speech(first_response)
        media_id = store_audio(audio_bytes)
        audio_url = get_audio_url(media_id)

        _save_turn(call_id, "agent", first_response, turn_index=0)

        return Response(
            content=twiml.consent_confirmed_and_first_turn(audio_url),
            media_type="application/xml",
        )

    user_text = SpeechResult.strip()
    if not user_text:
        retry_audio = await text_to_speech("I didn't catch that. Could you repeat?")
        retry_media_id = store_audio(retry_audio)
        return Response(
            content=twiml.play_audio_and_gather(get_audio_url(retry_media_id)),
            media_type="application/xml",
        )

    session = session_store.get(call_id)
    turn_index = session.turn_count * 2 if session else 0

    redaction_result = redact_pii(user_text)
    _save_turn(
        call_id,
        "user",
        user_text,
        turn_index=turn_index,
        redacted_text=redaction_result.redacted_text,
    )

    agent_response = await run_turn(call_id, user_text)

    audio_bytes = await text_to_speech(agent_response)
    media_id = store_audio(audio_bytes)
    audio_url = get_audio_url(media_id)

    _save_turn(call_id, "agent", agent_response, turn_index=turn_index + 1)

    return Response(
        content=twiml.play_audio_and_gather(audio_url), media_type="application/xml"
    )


@router.post("/status")
async def twilio_status(
    CallSid: str = Form(""),
    CallStatus: str = Form(""),
    CallDuration: str = Form(""),
    RecordingUrl: str = Form(""),
) -> Response:
    LOGGER.info(
        "Twilio /status: CallSid=%s Status=%s Duration=%s",
        CallSid,
        CallStatus,
        CallDuration,
    )

    call = queries.get_call_by_sid(CallSid)
    if not call:
        return Response(content="", status_code=200)

    call_id = call["id"]

    if CallStatus == "completed":
        await handle_call_completed(call_id, recording_url=RecordingUrl or None)
    else:
        update_call_status(call_id, CallStatus)

    return Response(content="", status_code=200)


def _save_turn(
    call_id: str,
    role: str,
    text: str,
    turn_index: int,
    redacted_text: str | None = None,
) -> None:
    from app.config import settings as cfg

    redaction = redact_pii(text) if redacted_text is None else None
    final_redacted = redacted_text or (redaction.redacted_text if redaction else text)

    data: dict = {
        "call_id": call_id,
        "role": role,
        "text_redacted": final_redacted,
        "turn_index": turn_index,
    }
    if cfg.store_raw_transcripts:
        data["text_raw"] = text

    try:
        queries.create_turn(data)
    except Exception:
        LOGGER.exception("Failed to save turn for call %s", call_id)
