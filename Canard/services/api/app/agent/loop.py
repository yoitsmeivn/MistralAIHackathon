# pyright: basic
# pyright: reportMissingImports=false
from __future__ import annotations

import logging
import random as _random
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


_FILLER_ONLY_PATTERNS = frozenset(
    {
        "right.",
        "right right.",
        "right right",
        "right",
        "yea.",
        "yea yea.",
        "yea yea",
        "yea",
        "yeah.",
        "yeah",
        "uh huh.",
        "uh huh",
        "mm-hmm.",
        "mm-hmm",
        "mmm-hmm",
        "okay.",
        "okay",
        "ok.",
        "ok",
        "sure.",
        "sure",
        "got it.",
        "got it",
        "i see.",
        "i see",
        "alright.",
        "alright",
        "sounds good.",
        "sounds good",
    }
)

_FILLER_EXPANSIONS = [
    "Got it, okay so let me just make sure I have this right -",
    "Right, that makes sense - so what I'll do is...",
    "Okay yeah, I hear you - so here's what I need from you:",
    "Got it - so the thing is, I still need to verify a couple things on my end.",
    "Yeah totally, I understand - so let me just pull this up real quick.",
    "Okay so I appreciate that - and I just need one more thing from you to wrap this up.",
    "Right, and I totally get that - so what I'm gonna do is...",
]


def _expand_filler_response(response: str) -> str:
    stripped = response.strip().lower().rstrip(".")
    if (
        stripped in _FILLER_ONLY_PATTERNS
        or response.strip().lower() in _FILLER_ONLY_PATTERNS
    ):
        expansion = _random.choice(_FILLER_EXPANSIONS)
        LOGGER.info("Anti-filler: expanded %r -> %r", response.strip(), expansion)
        return expansion
    return response


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
    response = _expand_filler_response(response)

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
    first_sentence = True

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
                if first_sentence:
                    sentence = _expand_filler_response(sentence)
                    first_sentence = False
                yield sentence

    remaining = buffer.strip()
    if remaining:
        if first_sentence:
            remaining = _expand_filler_response(remaining)
        yield remaining

    if full_text.strip():
        session_store.add_message(call_id, "assistant", full_text.strip())
        session.turn_count += 1
        session_store.trim_messages(call_id)
