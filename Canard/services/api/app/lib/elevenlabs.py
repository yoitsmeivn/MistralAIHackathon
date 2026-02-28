# pyright: basic, reportMissingImports=false

import httpx

from app.config import settings


async def text_to_speech(text: str, voice_id: str | None = None) -> bytes:
    api_key = settings.elevenlabs_api_key
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY is required")

    voice = voice_id or settings.elevenlabs_voice_id
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            headers={
                "Content-Type": "application/json",
                "xi-api-key": api_key,
            },
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
            timeout=30.0,
        )

    if resp.status_code != 200:
        raise RuntimeError(f"ElevenLabs TTS failed ({resp.status_code}): {resp.text}")

    return resp.content
