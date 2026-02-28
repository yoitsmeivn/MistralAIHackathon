# pyright: basic, reportMissingImports=false
from __future__ import annotations

import asyncio
import base64
import json
import logging

from fastapi import APIRouter, Form, Response, WebSocket, WebSocketDisconnect

from app.agent import (
    redact_pii,
    run_turn,
    session_store,
)
from app.db import queries
from app.integrations.elevenlabs import (
    realtime_stt_session,
    speech_to_text_from_url,
    text_to_speech,
)
from app.services.calls import (
    get_or_create_call_for_webhook,
    handle_call_completed,
    update_call_status,
)
from app.services.media import get_audio_url, store_audio
from app.twilio_voice import twiml

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/twilio", tags=["twilio"])


# ---------------------------------------------------------------------------
# Agent reply stub — replace with LLM (e.g. Mistral) for real conversations
# ---------------------------------------------------------------------------


async def generate_agent_reply(_call_id: str, transcript: str) -> str:
    """Generate the agent's text response for the real-time voice loop.

    **STUB** — returns a deterministic echo for end-to-end pipeline testing.

    To connect an LLM, replace the body with::

        from app.agent import run_turn
        return await run_turn(call_id, transcript)

    The call-site in ``_agent_loop`` already awaits this function so no
    signature change is needed.
    """
    if not transcript.strip():
        return "Sorry, I didn't catch that. Could you please repeat?"
    return (
        f"I heard you say: {transcript}. Is there anything else you'd like to discuss?"
    )


# ---------------------------------------------------------------------------
# Twilio HTTP webhooks
# ---------------------------------------------------------------------------


@router.post("/voice")
async def twilio_voice(CallSid: str = Form(""), CallStatus: str = Form("")) -> Response:
    """Entry webhook — Twilio calls this when the outbound call connects."""
    LOGGER.info("Twilio /voice webhook: CallSid=%s Status=%s", CallSid, CallStatus)

    call = None
    if CallSid:
        call = get_or_create_call_for_webhook(CallSid)

    if not call:
        return Response(
            content=twiml.say_and_hangup("An error occurred. Goodbye."),
            media_type="application/xml",
        )

    call_id = call["id"]
    queries.update_call(call_id, {"consented": True, "status": "in-progress"})
    return Response(
        content=twiml.stream_response(call_id), media_type="application/xml"
    )


@router.post("/gather")
async def twilio_gather(
    CallSid: str = Form(""),
    SpeechResult: str = Form(""),
    Digits: str = Form(""),
) -> Response:
    """Gather webhook — handles conversation turns (fallback gather-based flow)."""
    LOGGER.info(
        "Twilio /gather: CallSid=%s Digits=%s Speech=%s",
        CallSid,
        Digits,
        SpeechResult,
    )

    call = queries.get_call_by_sid(CallSid)
    if not call:
        LOGGER.error("No call record for CallSid=%s", CallSid)
        return Response(
            content=twiml.say_and_hangup("An error occurred. Goodbye."),
            media_type="application/xml",
        )

    call_id = call["id"]

    # ------------------------------------------------------------------
    # Fallback gather-based turn loop (used when NOT in streaming mode)
    # ------------------------------------------------------------------
    user_text = SpeechResult.strip()
    if not user_text:
        retry_audio = await text_to_speech("I didn't catch that. Could you repeat?")
        retry_media_id = store_audio(retry_audio)
        return Response(
            content=twiml.play_audio_and_gather(get_audio_url(retry_media_id)),
            media_type="application/xml",
        )

    session = session_store.get(call_id)
    turn_index = (
        (session.turn_count * 2) if session and hasattr(session, "turn_count") else 0
    )

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
    """Status callback — handles call lifecycle events (completed etc.)."""
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
        # Transcribe recording with ElevenLabs STT for higher quality.
        recording_transcript: str | None = None
        if RecordingUrl:
            try:
                recording_transcript = await speech_to_text_from_url(RecordingUrl)
                LOGGER.info(
                    "ElevenLabs STT transcribed recording for call %s (%d chars)",
                    call_id,
                    len(recording_transcript),
                )
            except Exception:
                LOGGER.warning(
                    "ElevenLabs STT failed for RecordingUrl=%s, skipping",
                    RecordingUrl,
                    exc_info=True,
                )
        await handle_call_completed(
            call_id,
            recording_url=RecordingUrl or None,
            recording_transcript=recording_transcript,
        )
    else:
        update_call_status(call_id, CallStatus)

    return Response(content="", status_code=200)


# ---------------------------------------------------------------------------
# Twilio Media Stream WebSocket (bidirectional real-time audio)
# ---------------------------------------------------------------------------


@router.websocket("/stream")
async def twilio_stream(websocket: WebSocket) -> None:
    """Bidirectional Twilio Media Stream — the real-time voice agent loop.

    Twilio connects to this endpoint after the ``<Connect><Stream>`` TwiML
    returned by :func:`twiml.stream_response` is executed.  The ``call_id``
    is **not** passed as a query parameter (Twilio ``<Stream>`` url does not
    support query strings); instead it arrives in the WebSocket ``start``
    message under ``start.customParameters.call_id``.

    Message sequence from Twilio::

        connected → start (customParameters, streamSid) → media… → stop

    Agent loop per turn:

    1. Twilio streams caller audio (``audio/x-mulaw`` 8 kHz, base64) as
       ``media`` messages.
    2. Audio is forwarded to ElevenLabs Realtime STT WebSocket.
    3. STT yields ``committed_transcript`` when the caller pauses (VAD).
    4. ``generate_agent_reply()`` produces a text response (stub — replace
       with LLM later).
    5. ElevenLabs TTS converts text → ``ulaw_8000`` audio bytes.
    6. Audio is sent back to Twilio as a ``media`` message, followed by a
       ``mark`` message for playback tracking.
    7. Caller hears the agent.  Repeat.

    Refs:
        https://www.twilio.com/docs/voice/media-streams/websocket-messages
        https://www.twilio.com/docs/voice/twiml/stream#custom-parameters
    """
    await websocket.accept()
    LOGGER.info("Twilio Media Stream WebSocket accepted")

    stream_sid: str = ""
    call_id: str = ""

    # ------------------------------------------------------------------
    # Phase 1 — Handshake: consume ``connected`` and ``start`` messages
    # to extract metadata before entering the streaming loop.
    # Twilio guarantees: connected → start → media…
    # ------------------------------------------------------------------
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            event = msg.get("event", "")

            if event == "connected":
                LOGGER.info(
                    "Twilio stream connected: protocol=%s v%s",
                    msg.get("protocol"),
                    msg.get("version"),
                )

            elif event == "start":
                start_data = msg.get("start", {})
                stream_sid = start_data.get("streamSid", "")
                custom_params = start_data.get("customParameters", {})
                call_id = custom_params.get("call_id", "")
                LOGGER.info(
                    "Twilio stream started: streamSid=%s call_id=%s callSid=%s",
                    stream_sid,
                    call_id,
                    start_data.get("callSid", ""),
                )
                break  # metadata acquired — proceed to streaming phase

            elif event == "stop":
                LOGGER.warning("Twilio stream stopped before start message")
                return

    except WebSocketDisconnect:
        LOGGER.warning("Twilio stream disconnected during handshake")
        return

    if not call_id:
        LOGGER.error("No call_id in stream customParameters, closing")
        await websocket.close()
        return

    call = queries.get_call(call_id)
    if not call:
        LOGGER.error("No call record for call_id=%s, closing stream", call_id)
        await websocket.close()
        return

    # ------------------------------------------------------------------
    # Phase 2 — Concurrent receive + agent loop
    # ------------------------------------------------------------------
    audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()

    async def _receive_twilio() -> None:
        """Forward Twilio ``media`` chunks into the STT audio queue."""
        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                event = msg.get("event", "")

                if event == "media":
                    payload = msg.get("media", {}).get("payload", "")
                    if payload:
                        await audio_queue.put(base64.b64decode(payload))

                elif event == "stop":
                    LOGGER.info("Twilio stream stopped: call_id=%s", call_id)
                    await audio_queue.put(None)  # signal end of audio
                    break

                elif event == "mark":
                    LOGGER.debug(
                        "Twilio mark received: %s",
                        msg.get("mark", {}).get("name"),
                    )

                elif event == "dtmf":
                    LOGGER.info(
                        "Twilio DTMF received: digit=%s",
                        msg.get("dtmf", {}).get("digit"),
                    )

        except WebSocketDisconnect:
            await audio_queue.put(None)

    async def _agent_loop() -> None:
        """Core loop: ElevenLabs STT → Agent reply → ElevenLabs TTS → Twilio."""
        turn_index = 0
        try:
            async for transcript in realtime_stt_session(audio_queue):
                if not transcript.strip():
                    continue

                LOGGER.info(
                    "[call=%s turn=%d] User: %r", call_id, turn_index, transcript
                )

                # Persist user turn
                redaction = redact_pii(transcript)
                _save_turn(
                    call_id,
                    "user",
                    transcript,
                    turn_index=turn_index,
                    redacted_text=redaction.redacted_text,
                )
                turn_index += 1

                # Agent reply (stub — no LLM dependency)
                agent_text = await generate_agent_reply(call_id, transcript)
                LOGGER.info(
                    "[call=%s turn=%d] Agent: %r", call_id, turn_index, agent_text
                )

                # Persist agent turn
                _save_turn(call_id, "agent", agent_text, turn_index=turn_index)
                turn_index += 1

                # ElevenLabs TTS → ulaw_8000 bytes
                audio_bytes = await text_to_speech(agent_text)

                # Send audio back to Twilio over the Media Stream WebSocket.
                # Twilio expects: {event: "media", streamSid, media: {payload}}
                # where payload is base64-encoded raw audio/x-mulaw @ 8 kHz.
                # NO file-type headers in the payload (per Twilio docs).
                # After sending media, send a mark so Twilio notifies us when
                # playback completes.
                if stream_sid and audio_bytes:
                    try:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {
                                        "payload": base64.b64encode(
                                            audio_bytes
                                        ).decode(),
                                    },
                                }
                            )
                        )
                        # Mark message — Twilio echoes this back when playback
                        # of the preceding media completes (or is cleared).
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "event": "mark",
                                    "streamSid": stream_sid,
                                    "mark": {
                                        "name": f"agent_turn_{turn_index}",
                                    },
                                }
                            )
                        )
                    except Exception:
                        LOGGER.warning(
                            "Failed to send audio to Twilio call_id=%s", call_id
                        )
                        break

        except Exception:
            LOGGER.exception("Agent loop error for call_id=%s", call_id)

    # Run both coroutines concurrently
    receive_task = asyncio.create_task(_receive_twilio())
    agent_task = asyncio.create_task(_agent_loop())

    try:
        await asyncio.gather(receive_task, agent_task)
    except Exception:
        LOGGER.exception("Stream error for call_id=%s", call_id)
    finally:
        receive_task.cancel()
        agent_task.cancel()
        LOGGER.info("Twilio Media Stream closed: call_id=%s", call_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
