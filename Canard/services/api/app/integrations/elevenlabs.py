# pyright: basic
"""
ElevenLabs integration — TTS, batch STT, and Realtime STT.

Architecture: Mistral is the agent brain. ElevenLabs is "just voice":
  - TTS: convert Mistral text responses → audio bytes → Twilio plays
  - Realtime STT: stream Twilio Media Stream audio → ElevenLabs WS → text → Mistral
  - Batch STT: transcribe Twilio RecordingUrl post-call for analysis

Realtime STT WebSocket: wss://api.elevenlabs.io/v1/speech-to-text/realtime
  - audio_format=ulaw_8000  (Twilio Media Streams native format)
  - commit_strategy=vad     (auto-commit on silence, no manual chunking needed)
  - yields committed_transcript text strings as caller speaks

Docs: https://elevenlabs.io/docs/api-reference/speech-to-text/v-1-speech-to-text-realtime
      https://elevenlabs.io/docs/api-reference/text-to-speech/convert
      https://elevenlabs.io/docs/api-reference/speech-to-text/convert
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
from collections.abc import AsyncIterator
from typing import Any, cast

import websockets

from elevenlabs.client import AsyncElevenLabs
from elevenlabs.types import VoiceSettings

from app.config import settings

LOGGER = logging.getLogger(__name__)

# ulaw_8000 = mu-law 8kHz — Twilio's native audio format.
# Avoids re-encoding on Twilio's side, reduces latency.
# Docs: output_format enum in /v1/text-to-speech/{voice_id}
_TWILIO_OUTPUT_FORMAT = "ulaw_8000"

# Voice settings tuned for phone calls:
# stability=0.75  → consistent delivery, not erratic
# similarity_boost=0.85 → stays close to the chosen voice
# style=0.0       → no style exaggeration (saves latency)
# use_speaker_boost=False → adds latency, not needed for phone
# speed=1.0       → natural pace
_PHONE_VOICE_SETTINGS = VoiceSettings(
    stability=0.75,
    similarity_boost=0.85,
    style=0.0,
    use_speaker_boost=False,
    speed=1.0,
)


_STAGE_DIRECTION_PATTERNS = [
    re.compile(
        r"\((?:laughs?|chuckles?|sighs?|pauses?|clears?\s+throat|coughs?|nervous(?:ly)?|whispers?|softly|loudly|excitedly|hesitant(?:ly)?|firmly|gently|sarcastically|smiles?|grins?|nods?|shakes?\s+head|gasps?|groans?|mumbles?|stutters?|trails?\s+off|thinking|beat)[^)]*\)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\[(?:laughs?|chuckles?|sighs?|pauses?|clears?\s+throat|coughs?|nervous(?:ly)?|whispers?|softly|loudly|beat)[^\]]*\]",
        re.IGNORECASE,
    ),
    re.compile(r"\*[^*]{1,40}\*"),
    re.compile(r"(?<!\w)\.(?:period|dot)\b", re.IGNORECASE),
    re.compile(r"(?:^|\s)(?:lol|haha|hehe|rofl|lmao)(?:\s|$)", re.IGNORECASE),
]

_MARKDOWN_PATTERNS = [
    re.compile(r"\*\*([^*]+)\*\*"),
    re.compile(r"__([^_]+)__"),
    re.compile(r"(?<!\w)\*([^*]+)\*(?!\w)"),
    re.compile(r"(?<!\w)_([^_]+)_(?!\w)"),
]


def sanitize_for_tts(text: str) -> str:
    if not text:
        return text

    for pattern in _STAGE_DIRECTION_PATTERNS:
        text = pattern.sub("", text)

    for pattern in _MARKDOWN_PATTERNS:
        text = pattern.sub(r"\1", text)

    text = re.sub(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002600-\U000026FF]",
        "",
        text,
    )

    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)

    return text.strip()


def _client() -> AsyncElevenLabs:
    """Create an authenticated AsyncElevenLabs client from settings."""
    if not settings.elevenlabs_api_key:
        raise ValueError("ELEVENLABS_API_KEY is required for ElevenLabs TTS/STT")
    return AsyncElevenLabs(api_key=settings.elevenlabs_api_key)


async def text_to_speech(
    text: str,
    voice_id: str | None = None,
    output_format: str = _TWILIO_OUTPUT_FORMAT,
) -> bytes:
    """
    Convert text to speech audio bytes using the ElevenLabs SDK.

    Uses AsyncElevenLabs.text_to_speech.convert() which returns an
    Iterator[bytes]. We collect all chunks into a single bytes object.

    Default output_format is ulaw_8000 — the mu-law format Twilio
    plays natively without re-encoding.

    Args:
        text: The text to synthesize.
        voice_id: Override the configured voice. Defaults to settings.elevenlabs_voice_id.
        output_format: ElevenLabs output format string. Default: ulaw_8000.

    Returns:
        Raw audio bytes.
    """
    selected_voice_id = voice_id or settings.elevenlabs_voice_id

    LOGGER.debug(
        "ElevenLabs TTS: voice=%s format=%s text_len=%d",
        selected_voice_id,
        output_format,
        len(text),
    )

    client = _client()

    chunks: list[bytes] = []
    async for chunk in client.text_to_speech.convert(
        voice_id=selected_voice_id,
        text=text,
        model_id="eleven_multilingual_v2",
        output_format=output_format,
        voice_settings=_PHONE_VOICE_SETTINGS,
        optimize_streaming_latency=3,
    ):
        if isinstance(chunk, bytes):
            chunks.append(chunk)

    audio_bytes = b"".join(chunks)

    LOGGER.debug("ElevenLabs TTS: got %d bytes", len(audio_bytes))
    return audio_bytes


async def speech_to_text(
    audio_bytes: bytes,
    filename: str = "recording.wav",
    language_code: str | None = None,
) -> str:
    """
    Transcribe audio bytes using ElevenLabs STT (Scribe v1).

    Uses AsyncElevenLabs.speech_to_text.convert() which accepts a
    file tuple and returns a SpeechToTextChunkResponseModel with a
    .text attribute containing the transcript.

    Args:
        audio_bytes: Raw audio file bytes (wav, mp3, ogg, etc.)
        filename: Filename hint for the upload.
        language_code: ISO-639-1 code (e.g. "en"). None = auto-detect.

    Returns:
        Transcribed text string.
    """
    LOGGER.debug("ElevenLabs STT: filename=%s bytes=%d", filename, len(audio_bytes))

    client = _client()

    # SDK: speech_to_text.convert() accepts file as a tuple (name, bytes, mime)
    # Returns SpeechToTextChunkResponseModel with .text attribute.
    kwargs: dict = {
        "model_id": "scribe_v1",
        "file": (filename, audio_bytes, "application/octet-stream"),
        "tag_audio_events": False,
        "timestamps_granularity": "none",
    }
    if language_code:
        kwargs["language_code"] = language_code

    result = await client.speech_to_text.convert(**kwargs)

    result_any = cast(Any, result)
    transcript = getattr(result_any, "text", "") or ""
    LOGGER.debug(
        "ElevenLabs STT: lang=%s text_len=%d",
        getattr(result_any, "language_code", "?"),
        len(transcript),
    )
    return transcript


async def speech_to_text_from_url(
    audio_url: str,
    language_code: str | None = None,
) -> str:
    """
    Transcribe audio from a URL (e.g. Twilio RecordingUrl).

    Downloads the audio first (with Twilio auth if needed), then
    passes bytes to speech_to_text() for transcription.

    Args:
        audio_url: Public HTTPS URL (e.g. Twilio RecordingUrl).
        language_code: ISO-639-1 code. None = auto-detect.

    Returns:
        Transcribed text string.
    """
    LOGGER.debug("ElevenLabs STT from URL: %s", audio_url)

    import httpx

    auth = None
    if "api.twilio.com" in audio_url or "twilio" in audio_url.lower():
        if settings.twilio_account_sid and settings.twilio_auth_token:
            auth = httpx.BasicAuth(
                settings.twilio_account_sid, settings.twilio_auth_token
            )

    async with httpx.AsyncClient() as http_client:
        resp = await http_client.get(audio_url, auth=auth, follow_redirects=True)
        resp.raise_for_status()
        audio_bytes = resp.content

    LOGGER.debug("Downloaded %d bytes from %s", len(audio_bytes), audio_url)

    filename = audio_url.split("/")[-1].split("?")[0] or "recording.wav"
    if not filename.endswith((".wav", ".mp3", ".ogg", ".flac", ".m4a")):
        filename = "recording.wav"

    return await speech_to_text(
        audio_bytes, filename=filename, language_code=language_code
    )


async def realtime_stt_session(
    audio_queue: asyncio.Queue[bytes | None],
    language_code: str | None = None,
) -> AsyncIterator[str]:
    """
    Stream audio bytes to ElevenLabs Realtime STT and yield committed transcripts.

    This is the core of the Twilio Media Stream → ElevenLabs → Mistral loop.
    Caller audio arrives as ulaw_8000 chunks from Twilio's Media Stream WebSocket.
    We forward them to ElevenLabs Realtime STT and yield committed transcript
    strings whenever the caller finishes a sentence (VAD-based auto-commit).

    Protocol (per docs):
      wss://api.elevenlabs.io/v1/speech-to-text/realtime
        ?model_id=scribe_v2_realtime
        &audio_format=ulaw_8000
        &commit_strategy=vad
        &language_code=en  (optional)

      Client sends: {message_type: input_audio_chunk, audio_base_64: ...,
                     commit: false, sample_rate: 8000}
      Server sends: {message_type: session_started | partial_transcript |
                     committed_transcript | error | ...}

    Args:
        audio_queue: Queue of raw ulaw_8000 audio bytes from Twilio.
                     Put None to signal end of stream.
        language_code: ISO-639-1 code. None = auto-detect.

    Yields:
        Committed transcript strings (one per sentence/utterance).
    """
    if not settings.elevenlabs_api_key:
        raise ValueError("ELEVENLABS_API_KEY is required for ElevenLabs Realtime STT")

    # Build WebSocket URL with query params per the AsyncAPI spec
    params = [
        "model_id=scribe_v2_realtime",
        "audio_format=ulaw_8000",  # Twilio Media Streams native format
        "commit_strategy=vad",  # auto-commit on silence — no manual chunking
    ]
    if language_code:
        params.append(f"language_code={language_code}")

    ws_url = "wss://api.elevenlabs.io/v1/speech-to-text/realtime?" + "&".join(params)

    # Auth via xi-api-key header (per spec: header OR token query param)
    extra_headers = {"xi-api-key": settings.elevenlabs_api_key}

    LOGGER.debug("ElevenLabs Realtime STT: connecting to %s", ws_url)

    async with websockets.connect(ws_url, additional_headers=extra_headers) as ws:
        LOGGER.debug("ElevenLabs Realtime STT: connected")

        async def _send_audio() -> None:
            """Read from audio_queue and forward chunks to ElevenLabs WS."""
            while True:
                chunk = await audio_queue.get()
                if chunk is None:
                    # Signal end — close the send side
                    LOGGER.debug("ElevenLabs Realtime STT: audio stream ended")
                    break
                msg = json.dumps(
                    {
                        "message_type": "input_audio_chunk",
                        "audio_base_64": base64.b64encode(chunk).decode(),
                        "commit": False,  # VAD handles committing
                        "sample_rate": 8000,  # ulaw_8000 = 8kHz
                    }
                )
                await ws.send(msg)

        async def _receive_transcripts() -> AsyncIterator[str]:
            """Receive messages from ElevenLabs WS and yield committed transcripts."""
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    LOGGER.warning("ElevenLabs Realtime STT: non-JSON message: %r", raw)
                    continue

                msg_type = msg.get("message_type", "")

                if msg_type == "session_started":
                    LOGGER.debug(
                        "ElevenLabs Realtime STT: session started: %s",
                        msg.get("session_id"),
                    )

                elif msg_type == "partial_transcript":
                    # Partial — caller still speaking, don't act yet
                    LOGGER.debug("ElevenLabs Realtime STT partial: %r", msg.get("text"))

                elif msg_type == "committed_transcript":
                    # Committed — caller finished a sentence, yield to agent
                    text = msg.get("text", "").strip()
                    if text:
                        LOGGER.info("ElevenLabs Realtime STT committed: %r", text)
                        yield text

                elif msg_type in (
                    "error",
                    "auth_error",
                    "quota_exceeded",
                    "rate_limited",
                    "resource_exhausted",
                    "session_time_limit_exceeded",
                    "transcriber_error",
                    "input_error",
                    "commit_throttled",
                    "unaccepted_terms",
                    "queue_overflow",
                    "chunk_size_exceeded",
                    "insufficient_audio_activity",
                ):
                    LOGGER.error(
                        "ElevenLabs Realtime STT error [%s]: %s",
                        msg_type,
                        msg.get("error", ""),
                    )
                    break

        # Run sender and receiver concurrently
        send_task = asyncio.create_task(_send_audio())
        try:
            async for transcript in _receive_transcripts():
                yield transcript
        finally:
            send_task.cancel()
            try:
                await send_task
            except asyncio.CancelledError:
                pass
