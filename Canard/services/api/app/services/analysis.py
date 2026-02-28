# pyright: basic
from __future__ import annotations

import logging

from app.agent.scoring import format_transcript, score_call
from app.db import queries

LOGGER = logging.getLogger(__name__)


async def run_post_call_analysis(call_id: str) -> dict | None:
    call = queries.get_call(call_id)
    if not call:
        LOGGER.warning("Cannot analyze: call %s not found", call_id)
        return None

    scenario = queries.get_scenario(call["scenario_id"])
    if not scenario:
        LOGGER.warning("Cannot analyze: scenario %s not found", call["scenario_id"])
        return None

    turns = queries.get_turns_for_call(call_id)
    if not turns:
        LOGGER.info("No turns to analyze for call %s", call_id)
        return None

    transcript_turns = [
        {"role": turn.get("role", ""), "content": turn.get("text_redacted", "")}
        for turn in turns
    ]
    transcript_text = format_transcript(transcript_turns)

    result = await score_call(transcript_text, scenario.get("description", ""))

    analysis_data = {
        "call_id": call_id,
        "risk_score": result["risk_score"],
        "flags": result["flags"],
        "summary": result["summary"],
        "coaching": result["coaching"],
    }
    return queries.create_analysis(analysis_data)
