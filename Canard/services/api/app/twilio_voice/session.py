# pyright: basic
"""
Structured in-memory call session data for the streaming voice pipeline.

Captures ALL data during a real-time call: turns, errors, marks, DTMF,
recording info, and timing metrics. The CallSessionData object is the
single source of truth while a call is active and provides a summary dict
for persistence once the call ends.

TODO(db): Wire to_summary_dict() output and individual TurnRecord objects
          to Supabase persistence layer in services/calls.py.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class TurnRole(str, Enum):
    USER = "user"
    AGENT = "agent"


@dataclass
class TurnRecord:
    """A single conversation turn."""

    role: TurnRole
    text: str
    redacted_text: str | None = None
    turn_index: int = 0
    timestamp_utc: str = field(default_factory=_utcnow)
    tts_duration_ms: float | None = None
    stt_duration_ms: float | None = None
    audio_bytes_sent: int | None = None


@dataclass
class ErrorRecord:
    """An error event during the call."""

    source: str  # "stt", "tts", "twilio", "agent", "websocket"
    error_type: str
    message: str
    timestamp_utc: str = field(default_factory=_utcnow)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class MarkRecord:
    """A Twilio mark acknowledgement."""

    name: str
    timestamp_utc: str = field(default_factory=_utcnow)


@dataclass
class DtmfRecord:
    """A DTMF digit received during the call."""

    digit: str
    timestamp_utc: str = field(default_factory=_utcnow)


@dataclass
class CallSessionData:
    """
    Accumulates ALL call data during a real-time voice session.

    After the call ends, to_summary_dict() returns everything needed for:
      - Turn persistence    (TODO(db): create_turn per TurnRecord)
      - Call metadata update (TODO(db): update_call with status/timing/recording)
      - Analysis input       (TODO(db): run_post_call_analysis)
      - Audit trail

    Thread-safety: accessed only from the asyncio event loop — no locking.
    """

    # ── Identity ──
    call_id: str
    twilio_call_sid: str = ""
    stream_sid: str = ""

    # ── Timing ──
    stream_started_at: str = ""
    stream_ended_at: str = ""
    greeting_sent_at: str = ""
    first_user_speech_at: str = ""

    # ── Turns ──
    turns: list[TurnRecord] = field(default_factory=list)
    next_turn_index: int = 0

    # ── Recording ──
    recording_url: str | None = None
    recording_sid: str | None = None
    recording_duration: int | None = None
    recording_transcript: str | None = None

    # ── Events ──
    errors: list[ErrorRecord] = field(default_factory=list)
    marks: list[MarkRecord] = field(default_factory=list)
    dtmf_events: list[DtmfRecord] = field(default_factory=list)

    # ── Status ──
    call_status: str = "in-progress"
    disconnect_reason: str | None = None

    # ── Metrics ──
    total_stt_ms: float = 0.0
    total_tts_ms: float = 0.0
    total_agent_ms: float = 0.0
    audio_chunks_received: int = 0
    audio_bytes_sent_total: int = 0

    # ------------------------------------------------------------------ helpers

    def add_turn(
        self,
        role: TurnRole,
        text: str,
        redacted_text: str | None = None,
        **kwargs: Any,
    ) -> TurnRecord:
        turn = TurnRecord(
            role=role,
            text=text,
            redacted_text=redacted_text,
            turn_index=self.next_turn_index,
            **kwargs,
        )
        self.turns.append(turn)
        self.next_turn_index += 1
        if role == TurnRole.USER and not self.first_user_speech_at:
            self.first_user_speech_at = turn.timestamp_utc
        return turn

    def add_error(
        self, source: str, error_type: str, message: str, **ctx: Any
    ) -> ErrorRecord:
        err = ErrorRecord(
            source=source, error_type=error_type, message=message, context=ctx
        )
        self.errors.append(err)
        return err

    def add_mark(self, name: str) -> MarkRecord:
        mark = MarkRecord(name=name)
        self.marks.append(mark)
        return mark

    def add_dtmf(self, digit: str) -> DtmfRecord:
        dtmf = DtmfRecord(digit=digit)
        self.dtmf_events.append(dtmf)
        return dtmf

    def to_summary_dict(self) -> dict[str, Any]:
        """Flat dict of ALL session data — ready for JSON or DB persistence."""
        return {
            "call_id": self.call_id,
            "twilio_call_sid": self.twilio_call_sid,
            "stream_sid": self.stream_sid,
            "stream_started_at": self.stream_started_at,
            "stream_ended_at": self.stream_ended_at,
            "greeting_sent_at": self.greeting_sent_at,
            "first_user_speech_at": self.first_user_speech_at,
            "call_status": self.call_status,
            "disconnect_reason": self.disconnect_reason,
            "total_turns": len(self.turns),
            "user_turns": sum(1 for t in self.turns if t.role == TurnRole.USER),
            "agent_turns": sum(1 for t in self.turns if t.role == TurnRole.AGENT),
            "recording_url": self.recording_url,
            "recording_sid": self.recording_sid,
            "recording_duration": self.recording_duration,
            "recording_transcript": self.recording_transcript,
            "total_errors": len(self.errors),
            "total_dtmf": len(self.dtmf_events),
            "metrics": {
                "total_stt_ms": self.total_stt_ms,
                "total_tts_ms": self.total_tts_ms,
                "total_agent_ms": self.total_agent_ms,
                "audio_chunks_received": self.audio_chunks_received,
                "audio_bytes_sent_total": self.audio_bytes_sent_total,
            },
            "turns": [
                {
                    "role": t.role.value,
                    "text": t.text,
                    "redacted_text": t.redacted_text,
                    "turn_index": t.turn_index,
                    "timestamp_utc": t.timestamp_utc,
                    "tts_duration_ms": t.tts_duration_ms,
                    "audio_bytes_sent": t.audio_bytes_sent,
                }
                for t in self.turns
            ],
            "errors": [
                {
                    "source": e.source,
                    "error_type": e.error_type,
                    "message": e.message,
                    "timestamp_utc": e.timestamp_utc,
                }
                for e in self.errors
            ],
        }


# ── Module-level session store ──

_active_sessions: dict[str, CallSessionData] = {}


def create_session(call_id: str, **kwargs: Any) -> CallSessionData:
    """Create and register a new call session."""
    session = CallSessionData(call_id=call_id, **kwargs)
    _active_sessions[call_id] = session
    return session


def get_session(call_id: str) -> CallSessionData | None:
    """Retrieve an active session by call_id."""
    return _active_sessions.get(call_id)


def remove_session(call_id: str) -> CallSessionData | None:
    """Remove and return a session (for cleanup after call ends)."""
    return _active_sessions.pop(call_id, None)
