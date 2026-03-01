# pyright: basic
# pyright: reportMissingImports=false
from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

from app.agent.memory import session_store
from app.agent.redaction import redact_pii
from app.integrations.mistral import chat_completion, chat_completion_stream


def _noop_op(fn):  # type: ignore[misc]
    return fn


_op: Any = _noop_op
try:
    import weave as _weave

    _op = _weave.op
except ImportError:
    pass


LOGGER = logging.getLogger(__name__)


@_op
async def start_session(call_id: str, script_id: str, system_prompt: str) -> None:
    session_store.create(
        call_id=call_id, script_id=script_id, system_prompt=system_prompt
    )


@_op
async def end_session(call_id: str) -> list[dict]:
    session = session_store.get(call_id)
    if session is None:
        return []
    history = [dict(message) for message in session.messages]
    session_store.remove(call_id)
    return history


@_op
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

    response = await chat_completion(llm_messages, max_tokens=150)

    session_store.add_message(call_id, "assistant", response)
    session.turn_count += 1
    session_store.trim_messages(call_id)

    return response


@_op
async def run_turn_streaming(
    call_id: str, user_speech: str
) -> AsyncGenerator[str, None]:
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

    buffer = ""
    full_text = ""
    sentence_endings = {". ", "? ", "! ", "\n"}

    async for chunk in chat_completion_stream(llm_messages, max_tokens=150):
        buffer += chunk
        full_text += chunk

        while True:
            found = -1
            for ending in sentence_endings:
                idx = buffer.find(ending)
                if idx != -1 and (found == -1 or idx < found):
                    found = idx + len(ending)
            if found == -1:
                break
            sentence = buffer[:found].strip()
            buffer = buffer[found:]
            if sentence:
                yield sentence

    remaining = buffer.strip()
    if remaining:
        yield remaining

    if full_text.strip():
        session_store.add_message(call_id, "assistant", full_text.strip())
        session.turn_count += 1
        session_store.trim_messages(call_id)
