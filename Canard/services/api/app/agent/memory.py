# pyright: basic
from __future__ import annotations

import math
from dataclasses import dataclass, field
from threading import RLock


def estimate_tokens(text: str) -> int:
    """Estimate token count using 4 chars/token with 30% safety margin."""
    return math.ceil(len(text) / 4 * 1.3)


@dataclass
class CallSession:
    call_id: str
    script_id: str
    messages: list[dict] = field(default_factory=list)
    turn_count: int = 0
    max_turns: int = 10


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, CallSession] = {}
        self._lock = RLock()

    def create(self, call_id: str, script_id: str, system_prompt: str) -> CallSession:
        session = CallSession(
            call_id=call_id,
            script_id=script_id,
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

            # Import here to avoid circular imports
            from app.config import settings

            budget = settings.mistral_max_context_tokens

            system_message = session.messages[0]
            non_system = session.messages[1:]

            # Calculate total tokens
            total = estimate_tokens(system_message.get("content", ""))
            total += sum(estimate_tokens(m.get("content", "")) for m in non_system)

            # If within budget, no trimming needed
            if total <= budget:
                # But still apply the keep limit as a safety net
                if len(non_system) > keep:
                    session.messages = [system_message, *non_system[-keep:]]
                return

            # Remove oldest non-system messages one at a time until within budget
            # Always preserve last 4 messages (2 exchange pairs)
            MIN_KEEP = 4
            while len(non_system) > MIN_KEEP:
                # Remove the oldest (index 0 of non_system)
                removed = non_system.pop(0)
                total -= estimate_tokens(removed.get("content", ""))
                if total <= budget:
                    break

            session.messages = [system_message, *non_system]

    def get_context_usage(self, call_id: str) -> dict:
        with self._lock:
            session = self._sessions.get(call_id)
            if session is None:
                raise KeyError(f"Session not found: {call_id}")
            from app.config import settings

            budget = settings.mistral_max_context_tokens
            estimated = sum(
                estimate_tokens(m.get("content", "")) for m in session.messages
            )
            return {
                "estimated_tokens": estimated,
                "message_count": len(session.messages),
                "budget": budget,
                "utilization_pct": round(estimated / budget * 100, 1)
                if budget > 0
                else 0.0,
            }


session_store = SessionStore()
