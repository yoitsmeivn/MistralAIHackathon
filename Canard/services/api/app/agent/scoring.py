# pyright: basic
from __future__ import annotations

from app.integrations.mistral import analyze_transcript


def format_transcript(turns: list[dict]) -> str:
    lines: list[str] = []
    for turn in turns:
        role = str(turn.get("role", "")).strip().lower()
        content = str(turn.get("content", "")).strip()
        if not content:
            continue
        if role == "user":
            speaker = "User"
        elif role == "assistant":
            speaker = "Agent"
        else:
            speaker = role.title() or "Unknown"
        lines.append(f"{speaker}: {content}")
    return "\n".join(lines)


async def score_call(transcript_text: str, scenario_description: str) -> dict:
    cleaned_transcript = transcript_text.strip()
    return await analyze_transcript(cleaned_transcript, scenario_description)
