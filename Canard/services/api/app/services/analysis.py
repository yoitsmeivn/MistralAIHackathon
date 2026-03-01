# pyright: basic
from __future__ import annotations

import logging

from app.services.evaluation import evaluate_call

LOGGER = logging.getLogger(__name__)


async def run_post_call_analysis(
    call_id: str,
    recording_transcript: str | None = None,
) -> dict | None:
    """Run post-call analysis — delegates to the evaluation agent."""
    return await evaluate_call(call_id, recording_transcript)
