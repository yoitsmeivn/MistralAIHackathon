# pyright: basic
from __future__ import annotations

import httpx

from app.config import settings


async def text_to_speech(text: str, voice_id: str | None = None) -> bytes:
    if not settings.elevenlabs_api_key:
        raise ValueError("ELEVENLABS_API_KEY is required")

    selected_voice_id = voice_id or settings.elevenlabs_voice_id
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{selected_voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": settings.elevenlabs_api_key,
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.content
