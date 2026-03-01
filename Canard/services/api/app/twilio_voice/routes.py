# pyright: basic, reportMissingImports=false
from __future__ import annotations

import asyncio
import base64
import json
import logging
import random
import time
import unicodedata
from datetime import datetime, timezone
from typing import Any, cast

import httpx
from fastapi import APIRouter, Form, Response, WebSocket, WebSocketDisconnect

from app.agent import (
    build_system_prompt,
    end_session,
    redact_pii,
    run_turn,
    run_turn_streaming,
    start_session,
)
from app.agent.memory import session_store
from app.agent.prompts import STREAM_GREETING, build_greeting
from app.config import settings as cfg
from app.db.client import get_supabase
from app.integrations.elevenlabs import (
    realtime_stt_session,
    sanitize_for_tts,
    speech_to_text_from_url,
    text_to_speech,
    text_to_speech_streaming,
)
from app.streaming.event_bus import CallEvent, event_bus
from app.services.email import send_test_results_email
from app.validation.scorer import EmployeeProfile, score_disclosure
from app.twilio_voice import twiml
from app.twilio_voice.session import (
    AgentState,
    TurnRole,
    create_session,
    get_session,
    remove_session,
)

# ── Barge-in constants ──
_BARGE_IN_THRESHOLD = 1000  # RMS energy — raised to prevent false triggers from ambient noise, hand movements, breathing
_BARGE_IN_FRAMES = (
    5  # 5 consecutive loud frames (~100ms) required — filters transient sounds
)

_BACKCHANNEL_WORDS = frozenset({"uh huh", "mm", "hmm", "mhm", "okay", "uh", "ah"})


def _is_latin_text(text: str) -> bool:
    for char in text:
        if not unicodedata.category(char).startswith("L"):
            continue
        if ord(char) < 0x0250:
            continue
        if "LATIN" in unicodedata.name(char, ""):
            continue
        return False
    return True


def _compute_mulaw_energy(payload: bytes) -> float:
    """Compute RMS energy of µ-law encoded audio. Works on Python 3.13+ (no audioop)."""
    if not payload:
        return 0.0
    total = 0.0
    for byte_val in payload:
        # µ-law to linear approximation
        byte_val = ~byte_val & 0xFF
        sign = -1 if (byte_val & 0x80) else 1
        exponent = (byte_val >> 4) & 0x07
        mantissa = byte_val & 0x0F
        magnitude = ((mantissa << 1) | 0x21) << (exponent + 2)
        magnitude -= 0x21
        sample = sign * magnitude
        total += sample * sample
    return (total / len(payload)) ** 0.5


LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/twilio", tags=["twilio"])


async def generate_agent_reply(call_id: str, transcript: str) -> str:
    """Generate the agent's text response using the Mistral LLM agent."""
    try:
        return await run_turn(call_id, transcript)
    except Exception:
        LOGGER.exception("Mistral agent reply failed for call_id=%s", call_id)
        return "I'm sorry, could you repeat that? I had trouble hearing you."


async def _init_agent_session(call_id: str) -> tuple[dict | None, dict | None]:
    """Fetch script/caller from DB and initialize the Mistral agent session.

    Follows the same safe-wrapper pattern as _lookup_call_safe / _update_call_safe.
    DB failures are logged but do not prevent session creation - a fallback
    prompt is used instead.
    """
    script: dict | None = None
    caller: dict | None = None
    employee: dict | None = None
    org: dict | None = None
    boss: dict | None = None
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
            eid = call_record.get("employee_id")
            if eid:
                employee = queries.get_employee(eid)
            if employee:
                org_id = employee.get("org_id")
                if org_id:
                    org = queries.get_organization(org_id)
                boss_id = employee.get("boss_id")
                if boss_id:
                    boss = queries.get_employee(boss_id)
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
        build_system_prompt(
            script, caller=caller, employee=employee, org=org, boss=boss
        )
        if script
        else build_system_prompt(scenario_name="Security Training")
    )
    await start_session(call_id, script_id, system_prompt)
    LOGGER.info(
        "Agent session initialized: call_id=%s script_id=%s", call_id, script_id
    )
    return caller, employee


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

        # ── Produce final summary ──
        summary = session.to_summary_dict() if session else {}
        LOGGER.info("Call completed — summary: %s", json.dumps(summary, default=str))

        # TODO(db): Persist call completion data:
        #   update_call(call_id, {status, ended_at, recording_url, duration})
        #   For each turn in session.turns:
        #       create_turn({call_id, role, text_redacted, turn_index, ...})
        update_data: dict[str, object] = {
            "status": "completed",
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "recording_url": RecordingUrl or None,
        }
        recording_transcript = (
            session.recording_transcript
            if session and getattr(session, "recording_transcript", None)
            else ""
        )

        # Duration (if provided by Twilio)
        if CallDuration:
            try:
                update_data["duration_seconds"] = int(CallDuration)
            except ValueError:
                pass

        # Transcript preference order:
        # 1) Twilio-provided recording transcript (if present)
        # 2) Session recording transcript (if present)
        # 3) Reconstructed from session turns
        if recording_transcript:
            update_data["transcript"] = recording_transcript
        elif session and getattr(session, "recording_transcript", None):
            update_data["transcript"] = session.recording_transcript
        elif session and getattr(session, "turns", None):
            transcript_lines: list[str] = []
            for t in session.turns:
                label = (
                    "Agent" if getattr(t.role, "value", t.role) == "agent" else "User"
                )
                transcript_lines.append(f"{label}: {t.text}")
            update_data["transcript"] = "\n".join(transcript_lines)

        _update_call_safe(call_id, update_data)

        # Fire post-call evaluation in the background
        transcript_for_eval = update_data.get("transcript")
        asyncio.create_task(
            _run_evaluation_safe(
                call_id,
                transcript_for_eval if isinstance(transcript_for_eval, str) else None,
            )
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

        # ── Transcribe recording with ElevenLabs batch STT ──
        if RecordingStatus == "completed" and RecordingUrl:
            download_url = RecordingUrl.rstrip("/") + ".wav"
            try:
                # Brief delay to ensure recording is propagated
                await asyncio.sleep(2)
                recording_transcript = await speech_to_text_from_url(download_url)
                LOGGER.info(
                    "ElevenLabs STT transcribed recording for call %s (%d chars)",
                    call["id"],
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

            try:
                if not RecordingSid:
                    raise ValueError("RecordingSid missing from Twilio callback")

                async with httpx.AsyncClient(
                    auth=(cfg.twilio_account_sid, cfg.twilio_auth_token),
                    timeout=30.0,
                ) as client:
                    recording_response = await client.get(download_url)
                    recording_response.raise_for_status()

                employee_id = call.get("employee_id") or ""
                storage_path = f"{employee_id}/{employee_id}.wav" if employee_id else f"{call['id']}/{RecordingSid}.wav"
                upload_options: dict[str, str] = {
                    "content-type": "audio/wav",
                    "upsert": "true",
                }
                get_supabase().storage.from_("recordings").upload(
                    storage_path,
                    recording_response.content,
                    cast(Any, upload_options),
                )

                supabase_url = f"{cfg.supabase_url.rstrip('/')}/storage/v1/object/public/recordings/{storage_path}"
                call_update: dict[str, object] = {
                    "recording_url": supabase_url,
                }
                if RecordingDuration:
                    try:
                        call_update["duration_seconds"] = int(RecordingDuration)
                    except ValueError:
                        LOGGER.warning(
                            "Invalid RecordingDuration in /recording callback: %s",
                            RecordingDuration,
                        )
                _update_call_safe(call["id"], call_update)
            except Exception:
                LOGGER.warning(
                    "Recording persistence to Supabase failed for call_id=%s RecordingSid=%s",
                    call["id"],
                    RecordingSid,
                    exc_info=True,
                )

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
    _caller: dict | None = None
    _employee: dict | None = None
    try:
        _caller, _employee = await _init_agent_session(call_id)
    except Exception:
        _caller = None
        _employee = None
        LOGGER.warning(
            "Agent session init failed for call_id=%s, agent replies will use fallback",
            call_id,
            exc_info=True,
        )

    if _caller:
        vp = _caller.get("voice_profile") or {}
        if isinstance(vp, dict) and vp.get("voice_id"):
            session.caller_voice_id = vp["voice_id"]
            LOGGER.info("Persona voice_id set: %s", session.caller_voice_id)
            await event_bus.emit(
                CallEvent(
                    call_id,
                    "persona_used",
                    {
                        "persona_name": _caller.get("persona_name", ""),
                        "voice_id": session.caller_voice_id,
                    },
                )
            )

    def _voice_id() -> str | None:
        return session.caller_voice_id

    try:
        from app.db import queries as _q

        call_record = _q.get_call(call_id)
        if call_record:
            employee = _q.get_employee(call_record.get("employee_id", ""))
            boss_record = None
            if employee and employee.get("boss_id"):
                boss_record = _q.get_employee(employee["boss_id"])
            session.employee_profile = EmployeeProfile.from_db(employee, boss_record)
    except Exception:
        LOGGER.warning("Failed to load employee profile for validation", exc_info=True)

    # ------------------------------------------------------------------
    # Phase 3 — Send ElevenLabs TTS greeting (agent speaks first)
    # ------------------------------------------------------------------
    try:
        t0 = time.monotonic()
        greeting_text = build_greeting(_caller, _employee) or STREAM_GREETING
        greeting_audio = await text_to_speech(
            sanitize_for_tts(greeting_text), voice_id=_voice_id(), call_id=call_id
        )
        tts_ms = (time.monotonic() - t0) * 1000

        if greeting_audio and stream_sid:
            session.state_transition(AgentState.SPEAKING)
            await event_bus.emit(
                CallEvent(
                    call_id,
                    "state_transition",
                    {"new_state": session.agent_state.value},
                )
            )
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
            session.audio_send_time = time.monotonic()
            session.audio_send_bytes = len(greeting_audio)
            session.barge_in_cooldown_until = time.monotonic() + 0.5
            session.greeting_sent_at = datetime.now(timezone.utc).isoformat()
            session.add_turn(
                TurnRole.AGENT,
                greeting_text,
                tts_duration_ms=tts_ms,
                audio_bytes_sent=len(greeting_audio),
            )
            session_store.add_message(call_id, "assistant", greeting_text)
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
    last_speech_time = [time.monotonic()]
    silence_state = {"nudge_sent": False}
    last_nudge_time = [0.0]
    generation_counter = [0]

    async def _receive_twilio() -> None:
        """Forward Twilio ``media`` chunks into the STT audio queue."""
        consecutive_loud = 0
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
                        decoded = base64.b64decode(payload)

                        # ── Barge-in detection ──
                        if (
                            session.agent_is_speaking
                            and time.monotonic() > session.barge_in_cooldown_until
                        ):
                            energy = _compute_mulaw_energy(decoded)
                            if energy > _BARGE_IN_THRESHOLD:
                                consecutive_loud += 1
                            else:
                                consecutive_loud = 0
                            if consecutive_loud >= _BARGE_IN_FRAMES:
                                # User is speaking over agent — clear queued audio
                                await websocket.send_text(
                                    json.dumps(
                                        {"event": "clear", "streamSid": stream_sid}
                                    )
                                )
                                await event_bus.emit(
                                    CallEvent(
                                        call_id,
                                        "clear_sent",
                                        {"stream_sid": stream_sid},
                                    )
                                )
                                session.state_transition(AgentState.LISTENING)
                                await event_bus.emit(
                                    CallEvent(
                                        call_id,
                                        "state_transition",
                                        {"new_state": session.agent_state.value},
                                    )
                                )
                                generation_counter[0] += 1
                                consecutive_loud = 0
                                last_speech_time[0] = time.monotonic()
                                silence_state["nudge_sent"] = False
                                LOGGER.info(
                                    "Barge-in detected: call_id=%s, clearing audio",
                                    call_id,
                                )
                                await event_bus.emit(
                                    CallEvent(
                                        call_id,
                                        "barge_in",
                                        {"energy": round(energy, 1)},
                                    )
                                )
                        else:
                            consecutive_loud = 0

                        if session.agent_state == AgentState.LISTENING:
                            await audio_queue.put(decoded)
                        await event_bus.emit(
                            CallEvent(
                                call_id,
                                "audio",
                                {
                                    "payload": payload,
                                    "format": "ulaw_8000",
                                },
                            )
                        )
                        session.audio_chunks_received += 1

                elif event == "stop":
                    LOGGER.info("Twilio stream stopped: call_id=%s", call_id)
                    session.disconnect_reason = "twilio_stop"
                    await audio_queue.put(None)
                    break

                elif event == "mark":
                    mark_name = msg.get("mark", {}).get("name", "")
                    session.add_mark(mark_name)
                    last_speech_time[0] = time.monotonic()
                    LOGGER.debug("Twilio mark received: %s", mark_name)

                    async def _echo_guard(mn: str = mark_name) -> None:
                        await asyncio.sleep(0.15)
                        session.state_transition(AgentState.LISTENING)
                        await event_bus.emit(
                            CallEvent(
                                call_id,
                                "state_transition",
                                {"new_state": session.agent_state.value},
                            )
                        )
                        await event_bus.emit(
                            CallEvent(
                                call_id,
                                "stt_ungated",
                                {"reason": "echo_guard_expired", "mark": mn},
                            )
                        )

                    asyncio.create_task(_echo_guard())

                elif event == "dtmf":
                    digit = msg.get("dtmf", {}).get("digit", "")
                    session.add_dtmf(digit)
                    LOGGER.info("Twilio DTMF received: digit=%s", digit)

        except WebSocketDisconnect:
            session.disconnect_reason = "websocket_disconnect"
            await audio_queue.put(None)

    async def _silence_monitor() -> None:
        """Nudge after 8s silence, goodbye after 20s."""
        while True:
            await asyncio.sleep(1.0)

            if session.disconnect_reason:
                break

            if session.call_should_end:
                if session.agent_is_speaking and session.audio_send_time > 0:
                    expected_duration = session.audio_send_bytes / 8000.0
                    if (
                        time.monotonic() - session.audio_send_time
                        < expected_duration + 1.0
                    ):
                        continue
                LOGGER.info(
                    "Graceful call end: call_id=%s reason=%s",
                    call_id,
                    session.end_reason,
                )
                session.disconnect_reason = session.end_reason or "call_complete"
                await audio_queue.put(None)
                try:
                    await websocket.close()
                except Exception:
                    LOGGER.debug("WebSocket close during graceful end failed")
                break

            if session.agent_is_speaking and session.audio_send_time > 0:
                expected_duration = session.audio_send_bytes / 8000.0
                if time.monotonic() - session.audio_send_time > expected_duration + 3.0:
                    session.state_transition(AgentState.LISTENING)
                    await event_bus.emit(
                        CallEvent(
                            call_id,
                            "state_transition",
                            {"new_state": session.agent_state.value},
                        )
                    )
                    LOGGER.warning(
                        "Mark timeout: force-clearing agent_is_speaking for call_id=%s",
                        call_id,
                    )

            if session.agent_state != AgentState.LISTENING:
                last_speech_time[0] = (
                    time.monotonic()
                )  # reset timer while not listening
                continue

            elapsed = time.monotonic() - last_speech_time[0]
            nudge_threshold = cfg.silence_nudge_ms / 1000.0
            goodbye_threshold = cfg.silence_goodbye_ms / 1000.0

            if elapsed >= goodbye_threshold:
                goodbye_phrases = [
                    "Well, seems like you're busy. I'll try again later!",
                    "Hello? Okay, I'll let you go. Have a good one!",
                    "Alright, I think we got cut off. Take care!",
                ]
                goodbye_text = random.choice(goodbye_phrases)
                try:
                    goodbye_audio = await text_to_speech(
                        sanitize_for_tts(goodbye_text),
                        voice_id=_voice_id(),
                        call_id=call_id,
                    )
                    if stream_sid and goodbye_audio:
                        session.state_transition(AgentState.SPEAKING)
                        await event_bus.emit(
                            CallEvent(
                                call_id,
                                "state_transition",
                                {"new_state": session.agent_state.value},
                            )
                        )
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {
                                        "payload": base64.b64encode(
                                            goodbye_audio
                                        ).decode()
                                    },
                                }
                            )
                        )
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "event": "mark",
                                    "streamSid": stream_sid,
                                    "mark": {"name": "silence_goodbye"},
                                }
                            )
                        )
                        session.barge_in_cooldown_until = time.monotonic() + 0.5
                    session.add_turn(TurnRole.AGENT, goodbye_text)
                    await event_bus.emit(
                        CallEvent(
                            call_id,
                            "silence_goodbye",
                            {"elapsed_s": round(elapsed, 1)},
                        )
                    )
                except Exception:
                    LOGGER.warning("Failed to send goodbye for call_id=%s", call_id)

                session.disconnect_reason = "silence_timeout"
                await audio_queue.put(None)
                try:
                    await websocket.close()
                except Exception:
                    LOGGER.debug("WebSocket close during silence timeout failed")
                break

            elif (
                elapsed >= nudge_threshold
                and not silence_state["nudge_sent"]
                and (time.monotonic() - last_nudge_time[0]) >= 15.0
            ):
                nudge_phrases = [
                    "Hello? You still there?",
                    "Hey, you there?",
                    "Sorry, did I lose you?",
                ]
                nudge_text = random.choice(nudge_phrases)
                try:
                    from app.agent.memory import session_store as _ss

                    _agent_sess = _ss.get(call_id)
                    if _agent_sess is not None:
                        _ss.add_message(
                            call_id,
                            "user",
                            "[System: The user has been silent. Continue your narrative naturally, add more detail, or ask a prompting question. Do not wait.]",
                        )
                except Exception:
                    LOGGER.debug(
                        "Failed to inject user_silent message for call_id=%s", call_id
                    )
                try:
                    nudge_audio = await text_to_speech(
                        sanitize_for_tts(nudge_text),
                        voice_id=_voice_id(),
                        call_id=call_id,
                    )
                    if stream_sid and nudge_audio:
                        session.state_transition(AgentState.SPEAKING)
                        await event_bus.emit(
                            CallEvent(
                                call_id,
                                "state_transition",
                                {"new_state": session.agent_state.value},
                            )
                        )
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {
                                        "payload": base64.b64encode(
                                            nudge_audio
                                        ).decode()
                                    },
                                }
                            )
                        )
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "event": "mark",
                                    "streamSid": stream_sid,
                                    "mark": {"name": "silence_nudge"},
                                }
                            )
                        )
                        session.barge_in_cooldown_until = time.monotonic() + 0.5
                    session.add_turn(TurnRole.AGENT, nudge_text)
                    await event_bus.emit(
                        CallEvent(
                            call_id,
                            "silence_nudge",
                            {"elapsed_s": round(elapsed, 1)},
                        )
                    )
                except Exception:
                    LOGGER.warning("Failed to send nudge for call_id=%s", call_id)
                silence_state["nudge_sent"] = True
                last_nudge_time[0] = time.monotonic()

    async def _agent_loop() -> None:
        """Core loop: ElevenLabs STT → Agent reply → ElevenLabs TTS → Twilio.

        Uses debouncing: accumulates STT transcripts and waits for 0.3s
        of silence before processing, so the user can finish their thought.
        """
        DEBOUNCE_SECONDS = 0.3
        accumulated_text: list[str] = []
        debounce_task: asyncio.Task | None = None
        processing_lock = asyncio.Lock()

        async def _process_accumulated() -> None:
            """Process all accumulated transcripts as one user turn."""
            nonlocal accumulated_text
            async with processing_lock:
                generation_counter[0] += 1
                my_generation_id = generation_counter[0]
                session.state_transition(AgentState.PROCESSING)
                await event_bus.emit(
                    CallEvent(
                        call_id,
                        "state_transition",
                        {"new_state": session.agent_state.value},
                    )
                )
                await event_bus.emit(
                    CallEvent(call_id, "stt_gated", {"reason": "processing_started"})
                )

                if not accumulated_text:
                    return

                # Join all fragments into a single user utterance
                full_transcript = " ".join(accumulated_text)
                accumulated_text = []

                if not full_transcript.strip():
                    return

                if session.agent_is_speaking:
                    await asyncio.sleep(0.3)
                    if session.agent_is_speaking:
                        try:
                            await websocket.send_text(
                                json.dumps({"event": "clear", "streamSid": stream_sid})
                            )
                            await event_bus.emit(
                                CallEvent(
                                    call_id, "clear_sent", {"stream_sid": stream_sid}
                                )
                            )
                        except Exception:
                            pass
                        session.state_transition(AgentState.LISTENING)
                        await event_bus.emit(
                            CallEvent(
                                call_id,
                                "state_transition",
                                {"new_state": session.agent_state.value},
                            )
                        )

                BRIDGE_PHRASES = [
                    "Yeah so...",
                    "Right, so the thing is...",
                    "So basically...",
                    "Okay so...",
                    "Yeah and the thing is...",
                ]
                bridge_text = random.choice(BRIDGE_PHRASES)
                try:
                    bridge_audio = await text_to_speech(
                        sanitize_for_tts(bridge_text),
                        voice_id=_voice_id(),
                        call_id=call_id,
                    )
                    if (
                        bridge_audio
                        and stream_sid
                        and my_generation_id == generation_counter[0]
                    ):
                        session.state_transition(AgentState.SPEAKING)
                        await event_bus.emit(
                            CallEvent(
                                call_id,
                                "state_transition",
                                {"new_state": session.agent_state.value},
                            )
                        )
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {
                                        "payload": base64.b64encode(
                                            bridge_audio
                                        ).decode()
                                    },
                                }
                            )
                        )
                        session.audio_send_time = time.monotonic()
                        session.audio_send_bytes += len(bridge_audio)
                        session.barge_in_cooldown_until = time.monotonic() + 0.3
                        session.audio_bytes_sent_total += len(bridge_audio)
                        await event_bus.emit(
                            CallEvent(
                                call_id, "bridge_phrase_sent", {"text": bridge_text}
                            )
                        )
                except Exception:
                    LOGGER.debug(
                        "Bridge phrase injection failed for call_id=%s, continuing",
                        call_id,
                    )

                LOGGER.info(
                    "[call=%s turn=%d] User: %r",
                    call_id,
                    session.next_turn_index,
                    full_transcript,
                )
                await event_bus.emit(
                    CallEvent(
                        call_id,
                        "user_speech",
                        {
                            "text": full_transcript,
                            "turn": session.next_turn_index,
                        },
                    )
                )

                if isinstance(session.employee_profile, EmployeeProfile):
                    matches = score_disclosure(
                        full_transcript, session.employee_profile
                    )
                    for match in matches:
                        LOGGER.info(
                            "[call=%s] SCORING: tier=%d field=%s confidence=%.2f",
                            call_id,
                            match.tier,
                            match.field_matched,
                            match.confidence,
                        )
                        await event_bus.emit(
                            CallEvent(
                                call_id,
                                "scoring",
                                {
                                    "tier": int(match.tier),
                                    "tier_label": match.tier.name.lower(),
                                    "field": match.field_matched,
                                    "disclosed": match.disclosed_value,
                                    "confidence": match.confidence,
                                    "turn": session.next_turn_index,
                                },
                            )
                        )

                # ── Persist user turn ──
                redaction = redact_pii(full_transcript)
                session.add_turn(
                    TurnRole.USER,
                    full_transcript
                    if cfg.store_raw_transcripts
                    else redaction.redacted_text,
                    redacted_text=redaction.redacted_text,
                )

                last_speech_time[0] = time.monotonic()
                t_start = time.monotonic()
                first_byte_ms = 0.0
                first_byte_sent = False
                all_sentences: list[str] = []
                tts_first_chunk_ms = 0.0
                tts_first_chunk_sent = False
                session.audio_send_bytes = 0

                # Max turns enforcement
                agent_session = session_store.get(call_id)
                if agent_session is not None and agent_session.turn_count >= 10:
                    LOGGER.info(
                        "Max turns reached for call_id=%s, sending goodbye", call_id
                    )
                    goodbye = "Alright, I think we've covered everything. Thanks for your time, take care!"
                    session.call_should_end = True
                    session.end_reason = "max_turns"
                    try:
                        goodbye_audio = await text_to_speech(
                            sanitize_for_tts(goodbye),
                            voice_id=_voice_id(),
                            call_id=call_id,
                        )
                        if stream_sid and goodbye_audio:
                            session.state_transition(AgentState.SPEAKING)
                            await event_bus.emit(
                                CallEvent(
                                    call_id,
                                    "state_transition",
                                    {"new_state": session.agent_state.value},
                                )
                            )
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "event": "media",
                                        "streamSid": stream_sid,
                                        "media": {
                                            "payload": base64.b64encode(
                                                goodbye_audio
                                            ).decode()
                                        },
                                    }
                                )
                            )
                    except Exception:
                        LOGGER.warning(
                            "Failed to send goodbye TTS for call_id=%s", call_id
                        )
                    return

                async def _tts_with_retry(text):
                    """Stream TTS chunks with single-retry fallback."""
                    try:
                        async for chunk in text_to_speech_streaming(
                            text,
                            voice_id=_voice_id(),
                            call_id=call_id,
                        ):
                            yield chunk
                    except Exception:
                        LOGGER.warning(
                            "TTS streaming failed for sentence, retrying: call_id=%s",
                            call_id,
                        )
                        try:
                            fallback_audio = await text_to_speech(
                                text,
                                voice_id=_voice_id(),
                                call_id=call_id,
                            )
                            if fallback_audio:
                                yield fallback_audio
                        except Exception:
                            LOGGER.warning(
                                "TTS retry also failed for call_id=%s, skipping sentence",
                                call_id,
                            )

                try:
                    async for sentence in run_turn_streaming(call_id, full_transcript):
                        if my_generation_id != generation_counter[0]:
                            await event_bus.emit(
                                CallEvent(
                                    call_id,
                                    "generation_cancelled",
                                    {
                                        "cancelled_id": my_generation_id,
                                        "current_id": generation_counter[0],
                                    },
                                )
                            )
                            break

                        all_sentences.append(sentence)
                        t0_tts = time.monotonic()
                        async for chunk in _tts_with_retry(sanitize_for_tts(sentence)):
                            if my_generation_id != generation_counter[0]:
                                break
                            if not isinstance(chunk, bytes) or not chunk:
                                continue
                            tts_ms = (time.monotonic() - t0_tts) * 1000
                            session.total_tts_ms += tts_ms
                            t0_tts = time.monotonic()

                            if stream_sid:
                                if not first_byte_sent:
                                    first_byte_ms = (time.monotonic() - t_start) * 1000
                                    session.state_transition(AgentState.SPEAKING)
                                    await event_bus.emit(
                                        CallEvent(
                                            call_id,
                                            "state_transition",
                                            {"new_state": session.agent_state.value},
                                        )
                                    )
                                    first_byte_sent = True
                                if not tts_first_chunk_sent:
                                    tts_first_chunk_ms = (
                                        time.monotonic() - t_start
                                    ) * 1000
                                    tts_first_chunk_sent = True
                                session.audio_send_time = time.monotonic()
                                session.audio_send_bytes += len(chunk)
                                try:
                                    await websocket.send_text(
                                        json.dumps(
                                            {
                                                "event": "media",
                                                "streamSid": stream_sid,
                                                "media": {
                                                    "payload": base64.b64encode(
                                                        chunk
                                                    ).decode(),
                                                },
                                            }
                                        )
                                    )
                                    session.barge_in_cooldown_until = (
                                        time.monotonic() + 0.5
                                    )
                                    session.audio_bytes_sent_total += len(chunk)
                                except Exception:
                                    session.add_error(
                                        "twilio",
                                        "send_failed",
                                        f"Failed to send audio for turn {session.next_turn_index - 1}",
                                    )
                                    LOGGER.warning(
                                        "Failed to send audio to Twilio call_id=%s",
                                        call_id,
                                    )

                        if my_generation_id != generation_counter[0]:
                            await event_bus.emit(
                                CallEvent(
                                    call_id,
                                    "generation_cancelled",
                                    {
                                        "cancelled_id": my_generation_id,
                                        "current_id": generation_counter[0],
                                    },
                                )
                            )
                            break
                except Exception:
                    LOGGER.exception(
                        "Mistral agent reply failed for call_id=%s", call_id
                    )
                    all_sentences = [
                        "I'm sorry, could you repeat that? I had trouble hearing you."
                    ]

                agent_text = " ".join(all_sentences).strip()
                call_complete_detected = "[CALL_COMPLETE]" in agent_text
                if call_complete_detected:
                    agent_text = agent_text.replace("[CALL_COMPLETE]", "").strip()
                    LOGGER.info("Call completion detected for call_id=%s", call_id)
                    await event_bus.emit(
                        CallEvent(
                            call_id,
                            "call_complete",
                            {
                                "reason": "objective_achieved",
                                "final_text": agent_text,
                            },
                        )
                    )
                    session.call_should_end = True
                    session.end_reason = "objective_achieved"

                if stream_sid and agent_text and not first_byte_sent:
                    t0_tts = time.monotonic()
                    audio_bytes = await text_to_speech(
                        sanitize_for_tts(agent_text),
                        voice_id=_voice_id(),
                        call_id=call_id,
                    )
                    tts_ms = (time.monotonic() - t0_tts) * 1000
                    session.total_tts_ms += tts_ms
                    if audio_bytes:
                        first_byte_ms = (time.monotonic() - t_start) * 1000
                        first_byte_sent = True
                        session.state_transition(AgentState.SPEAKING)
                        await event_bus.emit(
                            CallEvent(
                                call_id,
                                "state_transition",
                                {"new_state": session.agent_state.value},
                            )
                        )
                        session.audio_send_time = time.monotonic()
                        session.audio_send_bytes = len(audio_bytes)
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
                            session.barge_in_cooldown_until = time.monotonic() + 0.5
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
                if stream_sid and agent_text:
                    try:
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
                    except Exception:
                        pass

                agent_ms = (time.monotonic() - t_start) * 1000
                session.total_agent_ms += agent_ms

                LOGGER.info(
                    "[call=%s turn=%d] Agent: %r (%.0fms)",
                    call_id,
                    session.next_turn_index,
                    agent_text,
                    agent_ms,
                )
                await event_bus.emit(
                    CallEvent(
                        call_id,
                        "agent_reply",
                        {
                            "text": agent_text,
                            "latency_ms": round(agent_ms, 1),
                            "turn": session.next_turn_index,
                        },
                    )
                )

                await event_bus.emit(
                    CallEvent(
                        call_id,
                        "timing",
                        {
                            "first_byte_ms": round(
                                first_byte_ms if first_byte_sent else 0, 1
                            ),
                            "tts_first_chunk_ms": round(
                                tts_first_chunk_ms if tts_first_chunk_sent else 0, 1
                            ),
                            "tts_ms": round(session.total_tts_ms, 1),
                            "audio_bytes": session.audio_bytes_sent_total,
                            "turn": session.next_turn_index,
                        },
                    )
                )

                if agent_text:
                    session.add_turn(
                        TurnRole.AGENT,
                        agent_text,
                        tts_duration_ms=session.total_tts_ms,
                    )

        try:
            async for transcript in realtime_stt_session(audio_queue):
                if session.agent_state == AgentState.LISTENING:
                    last_speech_time[0] = time.monotonic()
                    silence_state["nudge_sent"] = False
                    await event_bus.emit(
                        CallEvent(
                            call_id, "silence_timer_reset", {"reason": "user_speech"}
                        )
                    )

                if not transcript.strip():
                    continue

                # Short transcript filter
                if len(transcript.strip()) < 2:
                    last_speech_time[0] = time.monotonic()
                    silence_state["nudge_sent"] = False
                    continue

                # Backchannel detection — reset timer but don't process
                if transcript.strip().lower() in _BACKCHANNEL_WORDS:
                    last_speech_time[0] = time.monotonic()
                    silence_state["nudge_sent"] = False
                    LOGGER.debug(
                        "Backchannel detected, skipping processing: %r",
                        transcript.strip(),
                    )
                    continue

                if not _is_latin_text(transcript):
                    LOGGER.info("STT filtered non-Latin text: %r", transcript)
                    await event_bus.emit(
                        CallEvent(
                            call_id,
                            "stt_filtered",
                            {"text": transcript, "reason": "non_latin"},
                        )
                    )
                    last_speech_time[0] = time.monotonic()
                    continue

                await event_bus.emit(
                    CallEvent(
                        call_id,
                        "stt_commit",
                        {
                            "text": transcript.strip(),
                            "state_at_commit": session.agent_state.value,
                            "accepted": session.agent_state == AgentState.LISTENING,
                        },
                    )
                )

                if session.agent_is_speaking:
                    try:
                        await websocket.send_text(
                            json.dumps({"event": "clear", "streamSid": stream_sid})
                        )
                        await event_bus.emit(
                            CallEvent(call_id, "clear_sent", {"stream_sid": stream_sid})
                        )
                    except Exception:
                        pass
                    session.state_transition(AgentState.LISTENING)
                    await event_bus.emit(
                        CallEvent(
                            call_id,
                            "state_transition",
                            {"new_state": session.agent_state.value},
                        )
                    )
                    generation_counter[0] += 1
                    LOGGER.info(
                        "STT barge-in: user spoke during agent audio, call_id=%s",
                        call_id,
                    )
                    await event_bus.emit(
                        CallEvent(
                            call_id,
                            "barge_in",
                            {"source": "stt", "text": transcript.strip()},
                        )
                    )

                # Accumulate transcript fragment
                accumulated_text.append(transcript.strip())

                # Cancel previous debounce timer if still waiting
                if debounce_task and not debounce_task.done():
                    debounce_task.cancel()

                # Start new debounce timer
                async def _debounce_then_process():
                    await asyncio.sleep(DEBOUNCE_SECONDS)
                    await _process_accumulated()

                debounce_task = asyncio.create_task(_debounce_then_process())

        except Exception:
            LOGGER.exception("Agent loop error for call_id=%s", call_id)
            session.add_error(
                "agent", "loop_error", "Unhandled exception in agent loop"
            )
        finally:
            # Process any remaining accumulated text
            if accumulated_text:
                try:
                    await _process_accumulated()
                except Exception:
                    LOGGER.warning("Failed to process final accumulated text")
            if debounce_task and not debounce_task.done():
                debounce_task.cancel()

    # Run both coroutines concurrently
    receive_task = asyncio.create_task(_receive_twilio())
    agent_task = asyncio.create_task(_agent_loop())
    silence_task = asyncio.create_task(_silence_monitor())

    try:
        await asyncio.gather(receive_task, agent_task, silence_task)
    except Exception:
        LOGGER.exception("Stream error for call_id=%s", call_id)
    finally:
        receive_task.cancel()
        agent_task.cancel()
        silence_task.cancel()
        try:
            await end_session(call_id)
        except Exception:
            LOGGER.warning(
                "Failed to end agent session for call_id=%s", call_id, exc_info=True
            )
        await event_bus.close_call(call_id)
        session.stream_ended_at = datetime.now(timezone.utc).isoformat()

        transcript_json = [
            {
                "role": turn.role.value,
                "text": turn.text,
                "redacted_text": turn.redacted_text,
                "turn_index": turn.turn_index,
                "timestamp_utc": turn.timestamp_utc,
            }
            for turn in session.turns
        ]
        transcript_lines: list[str] = []
        for turn in session.turns:
            role_label = "AGENT" if turn.role == TurnRole.AGENT else "USER"
            line_text = turn.redacted_text or turn.text
            transcript_lines.append(f"{role_label}: {line_text}")

        call_update: dict[str, object] = {
            "transcript": "\n".join(transcript_lines),
            "transcript_json": transcript_json,
            "ended_at": session.stream_ended_at,
            "status": "completed",
        }
        if session.stream_started_at and session.stream_ended_at:
            started_at = datetime.fromisoformat(session.stream_started_at)
            ended_at = datetime.fromisoformat(session.stream_ended_at)
            call_update["duration_seconds"] = int(
                (ended_at - started_at).total_seconds()
            )

        _update_call_safe(call_id, call_update)

        summary = session.to_summary_dict()
        LOGGER.info(
            "Twilio Media Stream closed: call_id=%s — %s",
            call_id,
            json.dumps(summary, default=str),
        )


# ---------------------------------------------------------------------------
# Post-call evaluation (fire-and-forget background task)
# ---------------------------------------------------------------------------


async def _run_evaluation_safe(call_id: str, recording_transcript: str | None) -> None:
    """Run post-call evaluation, catching all exceptions."""
    try:
        from app.services.evaluation import evaluate_call

        result = await evaluate_call(call_id, recording_transcript)
        if result:
            LOGGER.info(
                "Post-call evaluation succeeded for call %s: risk_score=%s",
                call_id,
                result.get("risk_score"),
            )
            await _send_audit_email_safe(call_id, result)
        else:
            LOGGER.info("Post-call evaluation returned no result for call %s", call_id)
    except Exception:
        LOGGER.warning(
            "Post-call evaluation failed for call %s", call_id, exc_info=True
        )


async def _send_audit_email_safe(call_id: str, eval_result: dict) -> None:
    """Send audit email after evaluation — best-effort, never raises."""
    try:
        from app.db import queries

        call = queries.get_call(call_id)
        if not call:
            LOGGER.warning("Audit email skipped — call %s not found in DB", call_id)
            return

        employee = queries.get_employee(call.get("employee_id", ""))
        if not employee:
            LOGGER.warning("Audit email skipped — employee not found for call %s", call_id)
            return

        to_email = employee.get("email")
        if not to_email:
            LOGGER.warning("Audit email skipped — no email for employee (call %s)", call_id)
            return

        campaign = queries.get_campaign(call["campaign_id"]) if call.get("campaign_id") else None

        flags = call.get("flags") or []
        if isinstance(flags, str):
            flags = [flags]

        email_id = send_test_results_email(
            to_email=to_email,
            employee_name=employee.get("full_name", ""),
            risk_score=call.get("risk_score") or 0,
            compliance=call.get("employee_compliance") or "",
            ai_summary=call.get("ai_summary") or "",
            flags=flags,
            transcript=call.get("transcript") or "",
            campaign_name=campaign.get("name", "") if campaign else "",
        )

        if email_id:
            LOGGER.info("Audit email sent for call %s to %s (id=%s)", call_id, to_email, email_id)
        else:
            LOGGER.warning("Audit email returned no id for call %s", call_id)
    except Exception:
        LOGGER.warning("Audit email failed for call %s", call_id, exc_info=True)


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
