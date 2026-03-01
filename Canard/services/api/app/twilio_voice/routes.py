# pyright: basic, reportMissingImports=false
from __future__ import annotations

import asyncio
import base64
import json
import logging
import random
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Form, Response, WebSocket, WebSocketDisconnect

from app.agent import (
    build_system_prompt,
    end_session,
    redact_pii,
    run_turn,
    start_session,
)
from app.agent.prompts import STREAM_GREETING
from app.config import settings as cfg
from app.integrations.elevenlabs import (
    realtime_stt_session,
    sanitize_for_tts,
    speech_to_text_from_url,
    text_to_speech,
)
from app.twilio_voice import twiml
from app.twilio_voice.session import (
    TurnRole,
    create_session,
    get_session,
    remove_session,
)

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/twilio", tags=["twilio"])


async def generate_agent_reply(call_id: str, transcript: str) -> str:
    """Generate the agent's text response using the Mistral LLM agent."""
    try:
        return await run_turn(call_id, transcript)
    except Exception:
        LOGGER.exception("Mistral agent reply failed for call_id=%s", call_id)
        return "I'm sorry, could you repeat that? I had trouble hearing you."


async def _init_agent_session(call_id: str) -> None:
    """Fetch script/caller from DB and initialize the Mistral agent session.

    Follows the same safe-wrapper pattern as _lookup_call_safe / _update_call_safe.
    DB failures are logged but do not prevent session creation - a fallback
    prompt is used instead.
    """
    script: dict | None = None
    caller: dict | None = None
    script_id = ""

    try:
        from app.db import queries

        call_record = queries.get_call(call_id)
        if call_record:
            sid = call_record.get("script_id")
            if sid:
                script_id = sid
                script = queries.get_script(sid)
            cid = call_record.get("caller_id")
            if cid:
                caller = queries.get_caller(cid)
    except Exception:
        LOGGER.warning(
            "DB lookup failed during agent init for call_id=%s", call_id, exc_info=True
        )

    if script:

        def _to_list(value: object) -> list:
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return parsed
                except (json.JSONDecodeError, ValueError):
                    return [value] if value.strip() else []
            return []

        all_objectives = _to_list(script.get("objectives", []))
        selected_objectives = all_objectives
        if len(all_objectives) > 1:
            num_to_pick = random.randint(1, min(2, len(all_objectives)))
            selected_objectives = random.sample(all_objectives, num_to_pick)
            LOGGER.info(
                "Randomized objectives for call_id=%s: %s (from %d total)",
                call_id,
                selected_objectives,
                len(all_objectives),
            )

        all_escalation_steps = _to_list(script.get("escalation_steps", []))
        selected_escalation_steps = all_escalation_steps
        if len(all_escalation_steps) > 2:
            shuffled = random.sample(all_escalation_steps, len(all_escalation_steps))
            num_to_pick = random.randint(2, min(3, len(shuffled)))
            selected_escalation_steps = shuffled[:num_to_pick]
            LOGGER.info(
                "Randomized escalation for call_id=%s: %s (from %d total)",
                call_id,
                selected_escalation_steps,
                len(all_escalation_steps),
            )

        script = {
            **script,
            "objectives": selected_objectives,
            "escalation_steps": selected_escalation_steps,
            "selected_objectives": selected_objectives,
            "selected_escalation_steps": selected_escalation_steps,
        }

    system_prompt = (
        build_system_prompt(script, caller=caller)
        if script
        else build_system_prompt(scenario_name="Security Training")
    )
    await start_session(call_id, script_id, system_prompt)
    LOGGER.info(
        "Agent session initialized: call_id=%s script_id=%s", call_id, script_id
    )


# ---------------------------------------------------------------------------
# Twilio HTTP webhooks
# ---------------------------------------------------------------------------


@router.post("/voice")
async def twilio_voice(
    CallSid: str = Form(""),
    CallStatus: str = Form(""),
) -> Response:
    """Entry webhook — returns TwiML to open a bidirectional Media Stream.

    No <Say> element — the greeting is delivered as ElevenLabs TTS audio
    directly over the WebSocket after the stream starts.
    """
    LOGGER.info("Twilio /voice webhook: CallSid=%s Status=%s", CallSid, CallStatus)

    # TODO(db): Reliable CallSid-based lookup requires a twilio_call_sid
    # column in the calls table.  Current get_call_by_sid() returns the most
    # recent "ringing" call, which is unreliable for concurrent calls.
    call = _lookup_call_safe(CallSid)

    if not call:
        LOGGER.error("No call record for CallSid=%s", CallSid)
        return Response(
            content=twiml.error_hangup("An error occurred. Goodbye."),
            media_type="application/xml",
        )

    call_id = call["id"]
    # TODO(db): update_call(call_id, {status: "in-progress"})
    _update_call_safe(call_id, {"status": "in-progress"})

    return Response(
        content=twiml.stream_response(call_id), media_type="application/xml"
    )


@router.post("/status")
async def twilio_status(
    CallSid: str = Form(""),
    CallStatus: str = Form(""),
    CallDuration: str = Form(""),
    RecordingUrl: str = Form(""),
    RecordingSid: str = Form(""),
    RecordingDuration: str = Form(""),
) -> Response:
    """Status callback — handles call lifecycle and recording events."""
    LOGGER.info(
        "Twilio /status: CallSid=%s Status=%s Duration=%s RecUrl=%s",
        CallSid,
        CallStatus,
        CallDuration,
        RecordingUrl,
    )

    call = _lookup_call_safe(CallSid)
    if not call:
        LOGGER.warning("No call for CallSid=%s in /status", CallSid)
        return Response(content="", status_code=200)

    call_id = call["id"]
    session = get_session(call_id)

    if CallStatus == "completed":
        # ── Update session with recording info ──
        if session:
            if RecordingUrl:
                session.recording_url = RecordingUrl
            if RecordingSid:
                session.recording_sid = RecordingSid
            if RecordingDuration:
                try:
                    session.recording_duration = int(RecordingDuration)
                except ValueError:
                    pass

        # ── Transcribe recording with ElevenLabs batch STT ──
        recording_transcript: str | None = None
        if RecordingUrl:
            try:
                recording_transcript = await speech_to_text_from_url(RecordingUrl)
                LOGGER.info(
                    "ElevenLabs STT transcribed recording for call %s (%d chars)",
                    call_id,
                    len(recording_transcript),
                )
                if session:
                    session.recording_transcript = recording_transcript
            except Exception:
                LOGGER.warning(
                    "ElevenLabs STT failed for RecordingUrl=%s, skipping",
                    RecordingUrl,
                    exc_info=True,
                )
                if session:
                    session.add_error(
                        "stt",
                        "recording_transcription_failed",
                        f"RecordingUrl: {RecordingUrl}",
                    )

        # ── Produce final summary ──
        summary = session.to_summary_dict() if session else {}
        LOGGER.info("Call completed — summary: %s", json.dumps(summary, default=str))

        # TODO(db): Persist call completion data:
        #   update_call(call_id, {status, ended_at, recording_url, duration})
        #   For each turn in session.turns:
        #       create_turn({call_id, role, text_redacted, turn_index, ...})
        _update_call_safe(
            call_id,
            {
                "status": "completed",
                "ended_at": datetime.now(timezone.utc).isoformat(),
                "recording_url": RecordingUrl or None,
            },
        )

        # Clean up in-memory session
        remove_session(call_id)
    else:
        # Non-terminal status update
        _update_call_safe(call_id, {"status": CallStatus})

    return Response(content="", status_code=200)


@router.post("/recording")
async def twilio_recording(
    CallSid: str = Form(""),
    RecordingSid: str = Form(""),
    RecordingUrl: str = Form(""),
    RecordingStatus: str = Form(""),
    RecordingDuration: str = Form(""),
) -> Response:
    """Recording status callback — dedicated endpoint for recording events.

    Reliability complement to RecordingUrl in /status.
    Twilio posts here when a recording completes.

    TODO(db): Persist recording_url, recording_sid, recording_duration
              to the calls table.
    """
    LOGGER.info(
        "Twilio /recording: CallSid=%s RecSid=%s Status=%s Dur=%s URL=%s",
        CallSid,
        RecordingSid,
        RecordingStatus,
        RecordingDuration,
        RecordingUrl,
    )

    call = _lookup_call_safe(CallSid)
    if call:
        session = get_session(call["id"])
        if session:
            session.recording_url = RecordingUrl or session.recording_url
            session.recording_sid = RecordingSid or session.recording_sid
            if RecordingDuration:
                try:
                    session.recording_duration = int(RecordingDuration)
                except ValueError:
                    pass

        # TODO(db): update_call(call["id"], {recording_url, recording_sid, ...})

    return Response(content="", status_code=200)


# ---------------------------------------------------------------------------
# Twilio Media Stream WebSocket (bidirectional real-time audio)
# ---------------------------------------------------------------------------


@router.websocket("/stream")
async def twilio_stream(websocket: WebSocket) -> None:
    """Bidirectional Twilio Media Stream — the real-time voice agent loop.

    Flow:
      1. Twilio connects → handshake (connected, start events)
      2. Backend sends ElevenLabs TTS greeting via WebSocket immediately
      3. Caller speaks → Twilio media → ElevenLabs Realtime STT
      4. STT yields committed_transcript (VAD-based)
      5. generate_agent_reply() produces text (Mistral LLM agent)
      6. ElevenLabs TTS converts text → ulaw_8000 bytes
      7. Audio sent to Twilio via WebSocket → caller hears agent
      8. Repeat until stop/disconnect

    Refs:
        https://www.twilio.com/docs/voice/media-streams/websocket-messages
        https://www.twilio.com/docs/voice/twiml/stream#custom-parameters
    """
    await websocket.accept()
    LOGGER.info("Twilio Media Stream WebSocket accepted")

    stream_sid: str = ""
    call_id: str = ""
    twilio_call_sid: str = ""

    # ------------------------------------------------------------------
    # Phase 1 — Handshake: consume ``connected`` and ``start`` messages
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
                twilio_call_sid = start_data.get("callSid", "")
                LOGGER.info(
                    "Twilio stream started: streamSid=%s call_id=%s callSid=%s",
                    stream_sid,
                    call_id,
                    twilio_call_sid,
                )
                break

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

    # ------------------------------------------------------------------
    # Phase 2 — Initialize session data object
    # ------------------------------------------------------------------
    session = create_session(
        call_id=call_id,
        twilio_call_sid=twilio_call_sid,
        stream_sid=stream_sid,
        stream_started_at=datetime.now(timezone.utc).isoformat(),
    )

    # ------------------------------------------------------------------
    # Phase 2.5 - Initialize Mistral agent session
    # ------------------------------------------------------------------
    try:
        await _init_agent_session(call_id)
    except Exception:
        LOGGER.warning(
            "Agent session init failed for call_id=%s, agent replies will use fallback",
            call_id,
            exc_info=True,
        )

    # ------------------------------------------------------------------
    # Phase 3 — Send ElevenLabs TTS greeting (agent speaks first)
    # ------------------------------------------------------------------
    try:
        t0 = time.monotonic()
        greeting_audio = await text_to_speech(sanitize_for_tts(STREAM_GREETING))
        tts_ms = (time.monotonic() - t0) * 1000

        if greeting_audio and stream_sid:
            await websocket.send_text(
                json.dumps(
                    {
                        "event": "media",
                        "streamSid": stream_sid,
                        "media": {
                            "payload": base64.b64encode(greeting_audio).decode(),
                        },
                    }
                )
            )
            await websocket.send_text(
                json.dumps(
                    {
                        "event": "mark",
                        "streamSid": stream_sid,
                        "mark": {"name": "greeting"},
                    }
                )
            )
            session.greeting_sent_at = datetime.now(timezone.utc).isoformat()
            session.add_turn(
                TurnRole.AGENT,
                STREAM_GREETING,
                tts_duration_ms=tts_ms,
                audio_bytes_sent=len(greeting_audio),
            )
            session.total_tts_ms += tts_ms
            session.audio_bytes_sent_total += len(greeting_audio)
            LOGGER.info(
                "Greeting sent: %d bytes, %.0fms TTS", len(greeting_audio), tts_ms
            )
    except Exception:
        LOGGER.exception("Failed to send greeting for call_id=%s", call_id)
        session.add_error("tts", "greeting_failed", "Failed to generate/send greeting")

    # ------------------------------------------------------------------
    # Phase 4 — Concurrent receive + agent loop
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
                        session.audio_chunks_received += 1

                elif event == "stop":
                    LOGGER.info("Twilio stream stopped: call_id=%s", call_id)
                    session.disconnect_reason = "twilio_stop"
                    await audio_queue.put(None)
                    break

                elif event == "mark":
                    mark_name = msg.get("mark", {}).get("name", "")
                    session.add_mark(mark_name)
                    LOGGER.debug("Twilio mark received: %s", mark_name)

                elif event == "dtmf":
                    digit = msg.get("dtmf", {}).get("digit", "")
                    session.add_dtmf(digit)
                    LOGGER.info("Twilio DTMF received: digit=%s", digit)

        except WebSocketDisconnect:
            session.disconnect_reason = "websocket_disconnect"
            await audio_queue.put(None)

    async def _agent_loop() -> None:
        """Core loop: ElevenLabs STT → Agent reply → ElevenLabs TTS → Twilio."""
        try:
            async for transcript in realtime_stt_session(audio_queue):
                if not transcript.strip():
                    continue

                LOGGER.info(
                    "[call=%s turn=%d] User: %r",
                    call_id,
                    session.next_turn_index,
                    transcript,
                )

                # ── Persist user turn ──
                redaction = redact_pii(transcript)
                session.add_turn(
                    TurnRole.USER,
                    transcript
                    if cfg.store_raw_transcripts
                    else redaction.redacted_text,
                    redacted_text=redaction.redacted_text,
                )
                # TODO(db): create_turn({call_id, role="user", text_redacted, ...})

                # ── Agent reply (Mistral LLM agent) ──
                t0 = time.monotonic()
                agent_text = await generate_agent_reply(call_id, transcript)
                agent_ms = (time.monotonic() - t0) * 1000
                session.total_agent_ms += agent_ms

                LOGGER.info(
                    "[call=%s turn=%d] Agent: %r (%.0fms)",
                    call_id,
                    session.next_turn_index,
                    agent_text,
                    agent_ms,
                )

                # ── ElevenLabs TTS → ulaw_8000 bytes ──
                t0 = time.monotonic()
                audio_bytes = await text_to_speech(sanitize_for_tts(agent_text))
                tts_ms = (time.monotonic() - t0) * 1000
                session.total_tts_ms += tts_ms

                # Record agent turn
                session.add_turn(
                    TurnRole.AGENT,
                    agent_text,
                    tts_duration_ms=tts_ms,
                    audio_bytes_sent=len(audio_bytes) if audio_bytes else 0,
                )
                # TODO(db): create_turn({call_id, role="agent", text, ...})

                # ── Send audio back to Twilio ──
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
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "event": "mark",
                                    "streamSid": stream_sid,
                                    "mark": {
                                        "name": f"agent_turn_{session.next_turn_index - 1}",
                                    },
                                }
                            )
                        )
                        session.audio_bytes_sent_total += len(audio_bytes)
                    except Exception:
                        session.add_error(
                            "twilio",
                            "send_failed",
                            f"Failed to send audio for turn {session.next_turn_index - 1}",
                        )
                        LOGGER.warning(
                            "Failed to send audio to Twilio call_id=%s", call_id
                        )
                        break

        except Exception:
            LOGGER.exception("Agent loop error for call_id=%s", call_id)
            session.add_error(
                "agent", "loop_error", "Unhandled exception in agent loop"
            )

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
        try:
            await end_session(call_id)
        except Exception:
            LOGGER.warning(
                "Failed to end agent session for call_id=%s", call_id, exc_info=True
            )
        session.stream_ended_at = datetime.now(timezone.utc).isoformat()

        # ── TODO(db): Persist ALL accumulated session data ──
        # This is the primary DB integration point after the stream ends.
        #   for turn in session.turns:
        #       create_turn(turn.__dict__)
        #   update_call(call_id, {
        #       stream_sid, ended_at, recording_url,
        #       disconnect_reason, metrics, ...
        #   })
        summary = session.to_summary_dict()
        LOGGER.info(
            "Twilio Media Stream closed: call_id=%s — %s",
            call_id,
            json.dumps(summary, default=str),
        )


# ---------------------------------------------------------------------------
# DB-safe wrappers — never block streaming on DB failures
# ---------------------------------------------------------------------------


def _lookup_call_safe(twilio_call_sid: str) -> dict | None:
    """Look up a call by Twilio CallSid.  Returns None on failure.

    TODO(db): Requires a ``twilio_call_sid`` column in the calls table
    for reliable matching.  Current get_call_by_sid() returns the most
    recent "ringing" call — unreliable for concurrent calls.
    """
    try:
        from app.db import queries

        return queries.get_call_by_sid(twilio_call_sid)
    except Exception:
        LOGGER.warning(
            "DB lookup failed for CallSid=%s", twilio_call_sid, exc_info=True
        )
        return None


def _update_call_safe(call_id: str, data: dict) -> None:
    """Update call record.  Silently logs failure — never blocks streaming.

    TODO(db): Use async DB client or asyncio.to_thread() to avoid blocking
    the event loop with synchronous Supabase calls.
    """
    try:
        from app.db import queries

        queries.update_call(call_id, data)
    except Exception:
        LOGGER.warning(
            "DB update failed for call_id=%s: %s", call_id, data, exc_info=True
        )
