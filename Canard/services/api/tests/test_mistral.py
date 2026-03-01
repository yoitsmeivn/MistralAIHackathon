# pyright: reportMissingImports=false
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from mistralai import SDKError

from app.integrations.mistral import (
    analyze_transcript,
    chat_completion,
    chat_completion_json,
    chat_completion_stream,
)


def make_mock_response(text: str) -> MagicMock:
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = text
    return response


async def _mock_stream(chunks: list[str]):
    for chunk in chunks:
        event = MagicMock()
        event.data.choices = [MagicMock()]
        event.data.choices[0].delta.content = chunk
        yield event


def test_chat_completion_returns_string() -> None:
    mock_client = MagicMock()
    mock_client.chat.complete_async = AsyncMock(
        return_value=make_mock_response("Hello from Mistral!")
    )

    with patch("app.integrations.mistral._get_client", return_value=mock_client):
        result = asyncio.run(
            chat_completion(messages=[{"role": "user", "content": "Hi"}])
        )

    assert isinstance(result, str)
    assert result == "Hello from Mistral!"


def test_chat_completion_stream_yields_chunks() -> None:
    chunks = ["Hello", " from", " stream"]
    mock_client = MagicMock()
    mock_client.chat.stream_async = AsyncMock(return_value=_mock_stream(chunks))

    with patch("app.integrations.mistral._get_client", return_value=mock_client):

        async def collect():
            results = []
            async for chunk in chat_completion_stream(
                messages=[{"role": "user", "content": "Hi"}]
            ):
                results.append(chunk)
            return results

        collected = asyncio.run(collect())

    assert all(isinstance(c, str) for c in collected)
    assert collected == chunks


def test_analyze_transcript_returns_dict() -> None:
    analysis_json = json.dumps(
        {
            "risk_score": 75,
            "flags": ["credential_disclosure", "urgency_pressure"],
            "summary": "Participant disclosed credentials under pressure.",
            "coaching": "Always verify caller identity before sharing any information.",
        }
    )
    mock_client = MagicMock()
    mock_client.chat.complete_async = AsyncMock(
        return_value=make_mock_response(analysis_json)
    )

    with patch("app.integrations.mistral._get_client", return_value=mock_client):
        result = asyncio.run(
            analyze_transcript(
                transcript="User: Sure, my password is abc123.",
                scenario_description="CEO wire transfer phishing scenario.",
            )
        )

    assert isinstance(result, dict)
    assert "risk_score" in result
    assert "flags" in result
    assert "summary" in result
    assert "coaching" in result
    assert isinstance(result["risk_score"], int)
    assert 0 <= result["risk_score"] <= 100


def test_chat_completion_json_returns_dict() -> None:
    payload = {"risk_score": 42, "flags": ["test"]}
    mock_client = MagicMock()
    mock_client.chat.complete_async = AsyncMock(
        return_value=make_mock_response(json.dumps(payload))
    )

    with patch("app.integrations.mistral._get_client", return_value=mock_client):
        result = asyncio.run(
            chat_completion_json(messages=[{"role": "user", "content": "analyze"}])
        )

    assert isinstance(result, dict)
    assert result["risk_score"] == 42
    assert result["flags"] == ["test"]


def test_chat_completion_json_falls_back_on_json_mode_failure() -> None:
    """When JSON mode raises, should fall back to plain completion + extraction."""
    payload = {"risk_score": 10, "summary": "ok"}
    call_count = 0

    async def failing_complete(**kwargs):
        nonlocal call_count
        call_count += 1
        if kwargs.get("response_format"):
            raise RuntimeError("JSON mode not supported")
        return make_mock_response(json.dumps(payload))

    mock_client = MagicMock()
    mock_client.chat.complete_async = failing_complete

    with patch("app.integrations.mistral._get_client", return_value=mock_client):
        result = asyncio.run(
            chat_completion_json(messages=[{"role": "user", "content": "test"}])
        )

    assert isinstance(result, dict)
    assert result["risk_score"] == 10
    assert call_count == 2  # first attempt (JSON mode) + fallback


def test_retry_on_429() -> None:
    # Build a real SDKError with a real httpx.Response carrying status 429
    raw_response = httpx.Response(429)
    sdk_error = SDKError(
        message="Rate limited",
        raw_response=raw_response,
        body="Too Many Requests",
    )

    success_response = make_mock_response("Retry succeeded!")
    call_count = 0

    async def flaky_complete(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise sdk_error
        return success_response

    mock_client = MagicMock()
    mock_client.chat.complete_async = flaky_complete

    with patch("app.integrations.mistral._get_client", return_value=mock_client):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = asyncio.run(
                chat_completion(messages=[{"role": "user", "content": "Hi"}])
            )

    assert isinstance(result, str)
    assert result == "Retry succeeded!"
    assert call_count == 2
