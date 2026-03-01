# pyright: basic
from __future__ import annotations

import io
import logging
import re
import statistics
from dataclasses import dataclass, field

import httpx

from app.config import settings

LOGGER = logging.getLogger(__name__)

# Disfluency patterns — common filler words / hesitation markers
_DISFLUENCY_PATTERN = re.compile(
    r"\b(um|uh|uhh|umm|er|err|hmm|hm|ah|ahh|like,|you know,|I mean,|sort of|kind of)\b",
    re.IGNORECASE,
)

# Behavioral / tone markers — parenthetical annotations from rich transcripts
# e.g. "(long pause)", "(nervous laugh)", "(speaking quickly)", "(whispering)"
_TONE_MARKER_PATTERN = re.compile(
    r"\(([^)]{2,60})\)",  # capture content inside parens, 2-60 chars
)

# Categorize tone markers into behavioral signals
_STRESS_KEYWORDS = {"nervous", "anxious", "hesitant", "stuttering", "trembling", "shaky", "worried", "panicked", "uneasy"}
_COMPLIANCE_KEYWORDS = {"agreeing", "compliant", "cooperative", "willing", "obliging", "yielding"}
_RESISTANCE_KEYWORDS = {"firm", "assertive", "refusing", "skeptical", "suspicious", "confident", "defiant", "questioning"}
_PAUSE_KEYWORDS = {"pause", "silence", "hesitation", "long pause", "thinking", "delayed"}
_EMOTION_KEYWORDS = {"angry", "frustrated", "sad", "crying", "laughing", "nervous laugh", "sighing", "confused", "surprised", "relieved"}

# Silence detection defaults
_SILENCE_THRESH_DBFS = -35
_MIN_SILENCE_MS = 700
_LONG_PAUSE_THRESHOLD_MS = 3000


@dataclass
class AudioFeatures:
    """Audio & behavioral features extracted from a call recording."""

    duration_seconds: float = 0.0

    # Silence / pause analysis
    silence_segments: list[tuple[int, int]] = field(default_factory=list)
    total_silence_seconds: float = 0.0
    silence_ratio: float = 0.0
    long_pauses_count: int = 0
    avg_silence_duration_ms: float = 0.0

    # Loudness
    loudness_mean_dbfs: float = 0.0
    loudness_std_dbfs: float = 0.0

    # Disfluencies (from transcript text)
    disfluency_count: int = 0
    disfluency_words: list[str] = field(default_factory=list)

    # Behavioral / tone markers (from transcript annotations)
    tone_markers: list[str] = field(default_factory=list)
    stress_indicators: list[str] = field(default_factory=list)
    compliance_signals: list[str] = field(default_factory=list)
    resistance_signals: list[str] = field(default_factory=list)
    pause_markers: list[str] = field(default_factory=list)
    emotion_markers: list[str] = field(default_factory=list)

    # Response latencies (from turn timestamps)
    response_latencies_ms: list[float] = field(default_factory=list)
    avg_response_latency_ms: float = 0.0

    def to_prompt_text(self) -> str:
        """Format features as a markdown block for the evaluation LLM."""
        lines = [
            f"- Duration: {self.duration_seconds:.1f}s",
            f"- Silence segments: {len(self.silence_segments)} "
            f"(total {self.total_silence_seconds:.1f}s, ratio {self.silence_ratio:.2f})",
            f"- Long pauses (>3s): {self.long_pauses_count}",
            f"- Avg silence duration: {self.avg_silence_duration_ms:.0f}ms",
            f"- Loudness: mean {self.loudness_mean_dbfs:.1f} dBFS, "
            f"std {self.loudness_std_dbfs:.1f} dBFS",
            f"- Disfluencies: {self.disfluency_count} ({', '.join(self.disfluency_words[:10]) or 'none'})",
            f"- Avg response latency: {self.avg_response_latency_ms:.0f}ms",
        ]

        if self.stress_indicators:
            lines.append(f"- Stress indicators: {', '.join(self.stress_indicators)}")
        if self.compliance_signals:
            lines.append(f"- Compliance signals: {', '.join(self.compliance_signals)}")
        if self.resistance_signals:
            lines.append(f"- Resistance signals: {', '.join(self.resistance_signals)}")
        if self.pause_markers:
            lines.append(f"- Annotated pauses/hesitations: {', '.join(self.pause_markers)}")
        if self.emotion_markers:
            lines.append(f"- Emotional markers: {', '.join(self.emotion_markers)}")
        if self.tone_markers:
            uncategorized = [
                m for m in self.tone_markers
                if m not in self.stress_indicators
                and m not in self.compliance_signals
                and m not in self.resistance_signals
                and m not in self.pause_markers
                and m not in self.emotion_markers
            ]
            if uncategorized:
                lines.append(f"- Other behavioral notes: {', '.join(uncategorized)}")

        return "\n".join(lines)


def _categorize_marker(marker: str) -> str:
    """Return the category for a tone marker, or 'other'.

    Checks emotion keywords first since they include compound phrases
    (e.g. 'nervous laugh') that would otherwise be caught by stress
    ('nervous').  Within each category, longer keywords are checked
    first so that 'nervous laugh' matches before 'nervous'.
    """
    lower = marker.lower()
    # Check in order: emotion first (compound phrases), then pause, resistance,
    # compliance, stress — most-specific → least-specific
    for keywords, category in [
        (_EMOTION_KEYWORDS, "emotion"),
        (_PAUSE_KEYWORDS, "pause"),
        (_RESISTANCE_KEYWORDS, "resistance"),
        (_COMPLIANCE_KEYWORDS, "compliance"),
        (_STRESS_KEYWORDS, "stress"),
    ]:
        # Sort by length descending so longer phrases match first
        for kw in sorted(keywords, key=len, reverse=True):
            if kw in lower:
                return category
    return "other"


def extract_tone_markers(transcript: str) -> dict[str, list[str]]:
    """Parse parenthetical tone/behavioral annotations from a transcript.

    Returns a dict with keys: tone_markers, stress, compliance, resistance,
    pause, emotion — each a list of matched marker strings.
    """
    raw_matches = _TONE_MARKER_PATTERN.findall(transcript)
    result: dict[str, list[str]] = {
        "tone_markers": [],
        "stress": [],
        "compliance": [],
        "resistance": [],
        "pause": [],
        "emotion": [],
    }
    for marker in raw_matches:
        marker = marker.strip()
        if not marker:
            continue
        result["tone_markers"].append(marker)
        category = _categorize_marker(marker)
        if category != "other":
            result[category].append(marker)
    return result


async def download_recording(url: str) -> bytes:
    """Download a Twilio recording using basic auth."""
    # Twilio recordings require AccountSid:AuthToken basic auth
    auth = (settings.twilio_account_sid, settings.twilio_auth_token)

    # Ensure we request the audio file (append .wav if no extension)
    download_url = url
    if not url.endswith((".wav", ".mp3")):
        download_url = f"{url}.wav"

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(download_url, auth=auth, follow_redirects=True)
        response.raise_for_status()
        return response.content


def extract_audio_features(
    audio_bytes: bytes,
    transcript: str = "",
    turn_timestamps: list[dict] | None = None,
) -> AudioFeatures:
    """Extract audio features from raw audio bytes + transcript text.

    Args:
        audio_bytes: WAV or MP3 audio data.
        transcript: Full transcript text for disfluency analysis.
        turn_timestamps: List of dicts with ``started_at_ms`` and ``ended_at_ms``
            for response latency calculation.
    """
    from pydub import AudioSegment
    from pydub.silence import detect_silence

    features = AudioFeatures()

    # ── Load audio ──
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    features.duration_seconds = len(audio) / 1000.0

    # ── Silence detection ──
    silence_ranges = detect_silence(
        audio,
        min_silence_len=_MIN_SILENCE_MS,
        silence_thresh=_SILENCE_THRESH_DBFS,
    )
    features.silence_segments = silence_ranges
    total_silence_ms = sum(end - start for start, end in silence_ranges)
    features.total_silence_seconds = total_silence_ms / 1000.0
    features.silence_ratio = (
        features.total_silence_seconds / features.duration_seconds
        if features.duration_seconds > 0
        else 0.0
    )
    features.long_pauses_count = sum(
        1 for start, end in silence_ranges if (end - start) >= _LONG_PAUSE_THRESHOLD_MS
    )
    features.avg_silence_duration_ms = (
        total_silence_ms / len(silence_ranges) if silence_ranges else 0.0
    )

    # ── Loudness (per-second chunks) ──
    chunk_ms = 1000
    loudness_values: list[float] = []
    for i in range(0, len(audio), chunk_ms):
        chunk = audio[i : i + chunk_ms]
        if len(chunk) > 100:  # skip very short trailing chunks
            loudness_values.append(chunk.dBFS)

    if loudness_values:
        features.loudness_mean_dbfs = statistics.mean(loudness_values)
        features.loudness_std_dbfs = (
            statistics.stdev(loudness_values) if len(loudness_values) > 1 else 0.0
        )

    # ── Disfluency detection (from transcript) ──
    if transcript:
        matches = _DISFLUENCY_PATTERN.findall(transcript)
        features.disfluency_count = len(matches)
        features.disfluency_words = [m.lower().rstrip(",") for m in matches]

    # ── Behavioral / tone marker extraction (from transcript annotations) ──
    if transcript:
        markers = extract_tone_markers(transcript)
        features.tone_markers = markers["tone_markers"]
        features.stress_indicators = markers["stress"]
        features.compliance_signals = markers["compliance"]
        features.resistance_signals = markers["resistance"]
        features.pause_markers = markers["pause"]
        features.emotion_markers = markers["emotion"]

    # ── Response latencies (from turn timestamps) ──
    if turn_timestamps and len(turn_timestamps) >= 2:
        latencies: list[float] = []
        for i in range(1, len(turn_timestamps)):
            prev = turn_timestamps[i - 1]
            curr = turn_timestamps[i]
            prev_end = prev.get("ended_at_ms")
            curr_start = curr.get("started_at_ms")
            if prev_end is not None and curr_start is not None:
                latency = curr_start - prev_end
                if latency >= 0:
                    latencies.append(latency)
        features.response_latencies_ms = latencies
        features.avg_response_latency_ms = (
            statistics.mean(latencies) if latencies else 0.0
        )

    return features
