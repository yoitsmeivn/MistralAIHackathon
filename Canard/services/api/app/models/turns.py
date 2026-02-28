# pyright: basic
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Turn(BaseModel):
    id: str
    call_id: str
    role: str
    text_redacted: str
    text_raw: str | None = None
    turn_index: int
    created_at: datetime | None = None
