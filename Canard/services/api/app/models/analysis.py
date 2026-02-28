# pyright: basic
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Analysis(BaseModel):
    id: str | None = None
    call_id: str
    risk_score: int
    flags: list[str] = Field(default_factory=list)
    summary: str
    coaching: str
    created_at: datetime | None = None
