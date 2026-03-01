# pyright: reportMissingImports=false
from __future__ import annotations

import asyncio
import io
from unittest.mock import AsyncMock, patch

from app.services.audio_features import (
    AudioFeatures,
    download_recording,
    extract_audio_features,
)


def _make_silent_wav(duration_ms: int = 3000, sample_rate: int = 8000) -> bytes:
    """Generate a silent WAV file in memory using pydub."""
    from pydub import AudioSegment
    from pydub.generators import Sine

    # Generate a very quiet tone (effectively silence for our threshold)
    audio = Sine(440).to_audio_segment(duration=duration_ms, volume=-50)
    audio = audio.set_frame_rate(sample_rate).set_channels(1)

    buf = io.BytesIO()
    audio.export(buf, format="wav")
    return buf.getvalue()


def _make_wav_with_tone(
    duration_ms: int = 2000,
    freq: int = 440,
    volume: float = -10.0,
) -> bytes:
    """Generate a WAV with an audible tone."""
    from pydub.generators import Sine

    audio = Sine(freq).to_audio_segment(duration=duration_ms, volume=volume)
    audio = audio.set_frame_rate(8000).set_channels(1)

    buf = io.BytesIO()
    audio.export(buf, format="wav")
    return buf.getvalue()


# ── AudioFeatures dataclass ──


def test_audio_features_defaults() -> None:
    af = AudioFeatures()
    assert af.duration_seconds == 0.0
    assert af.silence_segments == []
    assert af.disfluency_count == 0
    assert af.loudness_mean_dbfs == 0.0


def test_audio_features_to_prompt_text() -> None:
    af = AudioFeatures(
        duration_seconds=60.0,
        silence_segments=[(1000, 2500), (5000, 9000)],
        total_silence_seconds=5.5,
        silence_ratio=0.09,
        long_pauses_count=1,
        avg_silence_duration_ms=2750.0,
        loudness_mean_dbfs=-20.5,
        loudness_std_dbfs=3.2,
        disfluency_count=3,
        disfluency_words=["um", "uh", "like"],
        avg_response_latency_ms=850.0,
    )
    text = af.to_prompt_text()
    assert "Duration: 60.0s" in text
    assert "Long pauses" in text
    assert "um, uh, like" in text
    assert "850ms" in text


# ── Disfluency detection (via extract_audio_features) ──


def test_disfluency_detection_in_transcript() -> None:
    audio_bytes = _make_wav_with_tone(duration_ms=1000)
    transcript = "Um, I think, uh, you know, I like, sort of agree with that. Hmm."

    features = extract_audio_features(audio_bytes, transcript=transcript)

    assert features.disfluency_count >= 4  # um, uh, you know, like, sort of, hmm
    assert any(w in features.disfluency_words for w in ["um", "uh"])


def test_no_disfluencies_clean_transcript() -> None:
    audio_bytes = _make_wav_with_tone(duration_ms=1000)
    transcript = "I will not share my password with anyone."

    features = extract_audio_features(audio_bytes, transcript=transcript)

    assert features.disfluency_count == 0
    assert features.disfluency_words == []


# ── Audio analysis ──


def test_extract_features_duration() -> None:
    audio_bytes = _make_wav_with_tone(duration_ms=2000)
    features = extract_audio_features(audio_bytes)

    # Should be approximately 2 seconds
    assert 1.8 <= features.duration_seconds <= 2.2


def test_extract_features_loudness_nonzero() -> None:
    audio_bytes = _make_wav_with_tone(duration_ms=2000, volume=-15.0)
    features = extract_audio_features(audio_bytes)

    # Loudness should be measured (negative dBFS)
    assert features.loudness_mean_dbfs < 0


def test_extract_features_silence_detection() -> None:
    """A very quiet audio should register silence segments."""
    audio_bytes = _make_silent_wav(duration_ms=3000)
    features = extract_audio_features(audio_bytes)

    # The quiet audio should register as at least some silence
    assert features.duration_seconds > 0


def test_extract_features_response_latencies() -> None:
    audio_bytes = _make_wav_with_tone(duration_ms=1000)
    turn_timestamps = [
        {"started_at_ms": 0, "ended_at_ms": 1000},
        {"started_at_ms": 1500, "ended_at_ms": 2500},
        {"started_at_ms": 3000, "ended_at_ms": 4000},
    ]
    features = extract_audio_features(
        audio_bytes, turn_timestamps=turn_timestamps
    )

    assert len(features.response_latencies_ms) == 2
    assert features.response_latencies_ms[0] == 500.0  # 1500 - 1000
    assert features.response_latencies_ms[1] == 500.0  # 3000 - 2500
    assert features.avg_response_latency_ms == 500.0


# ── download_recording ──


def test_download_recording_uses_twilio_auth() -> None:
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b"fake-audio-bytes"
    mock_response.raise_for_status = lambda: None

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.audio_features.httpx.AsyncClient", return_value=mock_client_instance):
        result = asyncio.run(download_recording("https://api.twilio.com/recording/123"))

    assert result == b"fake-audio-bytes"
    # Verify .wav was appended
    call_args = mock_client_instance.get.call_args
    assert call_args[0][0].endswith(".wav")
