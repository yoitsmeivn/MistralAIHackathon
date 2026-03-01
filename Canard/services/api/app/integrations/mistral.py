# pyright: basic
from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncGenerator, Callable
from typing import Any, TypeVar

from mistralai import Mistral, SDKError

from app.config import settings

try:
    import weave as _weave
    _op = _weave.op
except ImportError:
    def _op(fn):  # type: ignore[misc]
        return fn

_client_instance: Mistral | None = None

_RETRYABLE_STATUS_CODES = {429, 500, 503}
_RETRY_DELAYS = (0.5, 1.0, 2.0)
_MAX_ATTEMPTS = 3
_REQUEST_TIMEOUT_MS = 30_000

T = TypeVar("T")


def _get_client() -> Mistral:
    global _client_instance

    if _client_instance is not None:
        return _client_instance

    if not settings.mistral_api_key:
        raise ValueError("MISTRAL_API_KEY is required")

    _client_instance = Mistral(
        api_key=settings.mistral_api_key,
        server_url=settings.mistral_base_url,
        timeout_ms=_REQUEST_TIMEOUT_MS,
    )
    return _client_instance


def _extract_status_code(exc: Exception) -> int | None:
    if isinstance(exc, SDKError):
        raw_response = getattr(exc, "raw_response", None)
        status_code = getattr(raw_response, "status_code", None)
        if isinstance(status_code, int):
            return status_code

    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if isinstance(status_code, int):
        return status_code

    return None


async def _with_retry(operation: Callable[[], Any]) -> Any:
    last_error: Exception | None = None

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            result = operation()
            if asyncio.iscoroutine(result):
                return await result
            return result
        except Exception as exc:
            status_code = _extract_status_code(exc)
            retryable = status_code in _RETRYABLE_STATUS_CODES
            if not retryable or attempt >= _MAX_ATTEMPTS:
                raise

            last_error = exc
            await asyncio.sleep(_RETRY_DELAYS[attempt - 1])

    if last_error is not None:
        raise last_error

    raise RuntimeError("Retry loop exited without a result")


def _coerce_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue

            if isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str):
                    parts.append(text)
                continue

            text = getattr(item, "text", None) or getattr(item, "content", None)
            if isinstance(text, str):
                parts.append(text)

        return "".join(parts)

    return ""


def _extract_response_text(response: Any) -> str:
    choices = getattr(response, "choices", None)
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("Mistral response did not include choices")

    first_choice = choices[0]
    message = getattr(first_choice, "message", None)
    content = getattr(message, "content", "")
    text = _coerce_text_content(content)
    if not isinstance(text, str):
        raise RuntimeError("Mistral content is not a string")
    return text


def _chat_kwargs(
    messages: list[dict],
    model: str | None,
    temperature: float,
    max_tokens: int | None,
    response_format: dict[str, str] | None = None,
) -> dict[str, Any]:
    request_model = model or settings.mistral_model
    resolved_temperature = (
        settings.mistral_temperature if temperature == 0.7 else temperature
    )

    kwargs: dict[str, Any] = {
        "model": request_model,
        "messages": messages,
        "temperature": resolved_temperature,
        "timeout_ms": _REQUEST_TIMEOUT_MS,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if response_format is not None:
        kwargs["response_format"] = response_format
    return kwargs


def _extract_json_object(content: str) -> dict:
    stripped = content.strip()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", stripped)
    if not match:
        raise ValueError("Unable to parse JSON object from Mistral response")

    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Mistral response JSON is not an object")
    return parsed


@_op
async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> str:
    client = _get_client()
    kwargs = _chat_kwargs(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    response = await _with_retry(lambda: client.chat.complete_async(**kwargs))
    return _extract_response_text(response)


@_op
async def chat_completion_stream(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> AsyncGenerator[str, None]:
    client = _get_client()
    kwargs = _chat_kwargs(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    stream = await _with_retry(lambda: client.chat.stream_async(**kwargs))

    async for event in stream:
        data = getattr(event, "data", None)
        choices = getattr(data, "choices", None)
        if not isinstance(choices, list) or not choices:
            continue

        delta = getattr(choices[0], "delta", None)
        content = getattr(delta, "content", "")
        chunk = _coerce_text_content(content)
        if chunk:
            yield chunk


@_op
async def analyze_transcript(transcript: str, scenario_description: str) -> dict:
    analysis_prompt = (
        "You are a security-awareness call evaluator. Analyze the transcript and return "
        "JSON only with exact keys: risk_score (0-100 integer), flags (array of strings), "
        "summary (string), coaching (string)."
    )
    messages = [
        {"role": "system", "content": analysis_prompt},
        {
            "role": "user",
            "content": (
                f"Scenario Description:\n{scenario_description}\n\n"
                f"Transcript:\n{transcript}\n\n"
                "Output strict JSON only."
            ),
        },
    ]

    parsed: dict[str, Any]
    try:
        client = _get_client()
        kwargs = _chat_kwargs(
            messages=messages,
            model=None,
            temperature=0.1,
            max_tokens=None,
            response_format={"type": "json_object"},
        )
        response = await _with_retry(lambda: client.chat.complete_async(**kwargs))
        parsed = _extract_json_object(_extract_response_text(response))
    except Exception:
        content = await chat_completion(messages=messages, temperature=0.1)
        parsed = _extract_json_object(content)

    risk_score = int(parsed.get("risk_score", 0))
    flags_raw = parsed.get("flags", [])
    flags = [str(flag) for flag in flags_raw] if isinstance(flags_raw, list) else []

    return {
        "risk_score": max(0, min(100, risk_score)),
        "flags": flags,
        "summary": str(parsed.get("summary", "")),
        "coaching": str(parsed.get("coaching", "")),
    }
