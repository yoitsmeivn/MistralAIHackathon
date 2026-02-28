# pyright: basic
from __future__ import annotations

import logging

from app.agent.scoring import format_transcript, score_call
from app.db import queries

LOGGER = logging.getLogger(__name__)


async def run_post_call_analysis(
    call_id: str,
    recording_transcript: str | None = None,
) -> dict | None:
    """
    Run Mistral-based risk analysis on a completed call.

    Args:
        call_id: Internal call UUID.
        recording_transcript: Optional pre-transcribed text from ElevenLabs STT.
            If provided, this is appended to the turn-based transcript for richer
            analysis (e.g. captures audio that wasn't processed turn-by-turn).
    """
    call = queries.get_call(call_id)
    if not call:
        LOGGER.warning("Cannot analyze: call %s not found", call_id)
        return None

    scenario = queries.get_scenario(call["scenario_id"])
    if not scenario:
        LOGGER.warning("Cannot analyze: scenario %s not found", call["scenario_id"])
        return None

    turns = queries.get_turns_for_call(call_id)
    if not turns and not recording_transcript:
        LOGGER.info("No turns or recording transcript to analyze for call %s", call_id)
        return None

    transcript_text = ""
    if turns:
        transcript_turns = [
            {"role": turn.get("role", ""), "content": turn.get("text_redacted", "")}
            for turn in turns
        ]
        transcript_text = format_transcript(transcript_turns)

    # If ElevenLabs STT produced a recording transcript, append it.
    # This captures any audio that wasn't processed through the turn loop
    # (e.g. the very end of the call, or if Twilio STT was used mid-call).
    if recording_transcript:
        if transcript_text:
            transcript_text += f"\n\n[Recording Transcript]\n{recording_transcript}"
        else:
            transcript_text = recording_transcript

    result = await score_call(transcript_text, scenario.get("description", ""))

    analysis_data = {
        "call_id": call_id,
        "risk_score": result["risk_score"],
        "flags": result["flags"],
        "summary": result["summary"],
        "coaching": result["coaching"],
    }
    return queries.create_analysis(analysis_data)
