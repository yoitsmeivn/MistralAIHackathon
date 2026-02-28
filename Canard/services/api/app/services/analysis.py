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

    script = queries.get_script(call["script_id"]) if call.get("script_id") else None
    if not script:
        LOGGER.warning("Cannot analyze: script %s not found", call.get("script_id"))
        return None

    transcript_json = call.get("transcript_json") or []
    if not transcript_json:
        LOGGER.info("No transcript to analyze for call %s", call_id)
        return None

    transcript_turns = [
        {"role": turn.get("role", ""), "content": turn.get("content", "")}
        for turn in transcript_json
    ]
    transcript_text = format_transcript(transcript_turns)

    result = await score_call(transcript_text, script.get("description", ""))

    analysis_data = {
        "risk_score": result["risk_score"],
        "flags": result["flags"],
        "ai_summary": result["summary"],
        "employee_compliance": result.get("employee_compliance"),
    }
    return queries.update_call(call_id, analysis_data)
