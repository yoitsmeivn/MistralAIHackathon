# pyright: basic, reportMissingImports=false
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.streaming.event_bus import event_bus

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitor", tags=["monitoring"])


@router.get("/stream/{call_id}")
async def monitor_call_stream(
    call_id: str, request: Request, include_audio: bool = False
):
    q = event_bus.subscribe(call_id)

    async def generate():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30.0)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if event is None:
                    yield "event: call_ended\ndata: {}\n\n"
                    break
                if event.event_type == "audio" and not include_audio:
                    continue
                yield event.to_sse()
        finally:
            event_bus.unsubscribe(call_id, q)
            LOGGER.info("SSE monitor disconnected for call_id=%s", call_id)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
