# pyright: basic
from __future__ import annotations

import uuid

from app.config import settings

_audio_store: dict[str, bytes] = {}


def store_audio(audio_bytes: bytes) -> str:
    media_id = str(uuid.uuid4())
    _audio_store[media_id] = audio_bytes
    return media_id


def get_audio(media_id: str) -> bytes | None:
    return _audio_store.get(media_id)


def remove_audio(media_id: str) -> None:
    _audio_store.pop(media_id, None)


def get_audio_url(media_id: str) -> str:
    base = settings.public_base_url.rstrip("/")
    return f"{base}/media/{media_id}"
