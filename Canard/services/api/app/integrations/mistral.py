# pyright: basic
from __future__ import annotations

import json
import re

import httpx

from app.config import settings


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


async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> str:
    if not settings.mistral_api_key:
        raise ValueError("MISTRAL_API_KEY is required")

    url = f"{settings.mistral_base_url.rstrip('/')}/v1/chat/completions"
    payload: dict[str, object] = {
        "model": model or settings.mistral_model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    headers = {
        "Authorization": f"Bearer {settings.mistral_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        body = response.json()

    choices = body.get("choices", [])
    if not choices:
        raise RuntimeError("Mistral response did not include choices")

    message = choices[0].get("message", {})
    content = message.get("content", "")
    if not isinstance(content, str):
        raise RuntimeError("Mistral content is not a string")

    return content


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
