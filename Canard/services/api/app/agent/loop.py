# pyright: basic
# pyright: reportMissingImports=false
from __future__ import annotations

import logging

from app.agent.memory import session_store
from app.agent.redaction import redact_pii
from app.integrations.mistral import chat_completion

LOGGER = logging.getLogger(__name__)


async def start_session(call_id: str, scenario_id: str, system_prompt: str) -> None:
    session_store.create(
        call_id=call_id, scenario_id=scenario_id, system_prompt=system_prompt
    )


async def end_session(call_id: str) -> list[dict]:
    session = session_store.get(call_id)
    if session is None:
        return []
    history = [dict(message) for message in session.messages]
    session_store.remove(call_id)
    return history


async def run_turn(call_id: str, user_speech: str) -> str:
    session = session_store.get(call_id)
    if session is None:
        raise ValueError(f"Session not found for call_id={call_id}")

    redaction = redact_pii(user_speech)
    if redaction.has_sensitive_content:
        LOGGER.info(
            "Redacted user speech for call",
            extra={"call_id": call_id, "redactions": redaction.redactions},
        )

    session_store.add_message(call_id, "user", redaction.redacted_text)

    llm_messages = [dict(message) for message in session.messages]
    if llm_messages and llm_messages[-1].get("role") == "user":
        llm_messages[-1]["content"] = user_speech

    response = await chat_completion(llm_messages)

    session_store.add_message(call_id, "assistant", response)
    session.turn_count += 1
    session_store.trim_messages(call_id)

    return response
