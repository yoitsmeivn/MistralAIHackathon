# pyright: basic, reportMissingImports=false
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field

LOGGER = logging.getLogger(__name__)


@dataclass
class CallEvent:
    call_id: str
    event_type: str
    data: dict[str, object]
    timestamp: float = field(default_factory=time.time)

    def to_sse(self) -> str:
        payload = {
            "call_id": self.call_id,
            "type": self.event_type,
            "data": self.data,
            "ts": self.timestamp,
        }
        return f"event: {self.event_type}\ndata: {json.dumps(payload)}\n\n"


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[CallEvent | None]]] = {}

    def subscribe(self, call_id: str) -> asyncio.Queue[CallEvent | None]:
        q: asyncio.Queue[CallEvent | None] = asyncio.Queue(maxsize=500)
        self._subscribers.setdefault(call_id, []).append(q)
        LOGGER.info(
            "EventBus: subscriber added for call_id=%s (total=%d)",
            call_id,
            len(self._subscribers.get(call_id, [])),
        )
        return q

    def unsubscribe(self, call_id: str, q: asyncio.Queue[CallEvent | None]) -> None:
        subs = self._subscribers.get(call_id, [])
        if q in subs:
            subs.remove(q)
        if not subs:
            _ = self._subscribers.pop(call_id, None)

    async def emit(self, event: CallEvent) -> None:
        for q in self._subscribers.get(event.call_id, []):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                LOGGER.warning(
                    "EventBus: queue full for call_id=%s, dropping %s event",
                    event.call_id,
                    event.event_type,
                )

    async def close_call(self, call_id: str) -> None:
        for q in self._subscribers.pop(call_id, []):
            await q.put(None)


event_bus = EventBus()
