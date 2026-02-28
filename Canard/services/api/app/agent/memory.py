# pyright: basic
from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock


@dataclass
class CallSession:
    call_id: str
    scenario_id: str
    messages: list[dict] = field(default_factory=list)
    turn_count: int = 0
    consented: bool = False
    max_turns: int = 10


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, CallSession] = {}
        self._lock = RLock()

    def create(self, call_id: str, scenario_id: str, system_prompt: str) -> CallSession:
        session = CallSession(
            call_id=call_id,
            scenario_id=scenario_id,
            messages=[{"role": "system", "content": system_prompt}],
        )
        with self._lock:
            self._sessions[call_id] = session
        return session

    def get(self, call_id: str) -> CallSession | None:
        with self._lock:
            return self._sessions.get(call_id)

    def add_message(self, call_id: str, role: str, content: str) -> None:
        with self._lock:
            session = self._sessions.get(call_id)
            if session is None:
                raise KeyError(f"Session not found: {call_id}")
            session.messages.append({"role": role, "content": content})

    def set_consented(self, call_id: str) -> None:
        with self._lock:
            session = self._sessions.get(call_id)
            if session is None:
                raise KeyError(f"Session not found: {call_id}")
            session.consented = True

    def remove(self, call_id: str) -> None:
        with self._lock:
            self._sessions.pop(call_id, None)

    def trim_messages(self, call_id: str, keep: int = 20) -> None:
        with self._lock:
            session = self._sessions.get(call_id)
            if session is None:
                raise KeyError(f"Session not found: {call_id}")

            if not session.messages:
                return

            system_message = session.messages[0]
            if keep <= 0:
                session.messages = [system_message]
                return

            tail = session.messages[1:]
            session.messages = [system_message, *tail[-keep:]]


session_store = SessionStore()
