import uuid

from app.agents.memory import create_initial_state
from app.agents.types import ConversationState

DEFAULT_SYSTEM_PROMPT = (
    "You are Canard, a helpful voice assistant. "
    "You respond concisely and helpfully. "
    "Keep responses under 3 sentences when possible."
)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, ConversationState] = {}

    def get_or_create(
        self, session_id: str | None = None
    ) -> tuple[str, ConversationState]:
        if session_id and session_id in self._sessions:
            return session_id, self._sessions[session_id]

        new_id = session_id or f"ses_{uuid.uuid4().hex[:16]}"
        state = create_initial_state(DEFAULT_SYSTEM_PROMPT)
        self._sessions[new_id] = state
        return new_id, state

    def update(self, session_id: str, state: ConversationState) -> None:
        self._sessions[session_id] = state


session_store = SessionStore()
