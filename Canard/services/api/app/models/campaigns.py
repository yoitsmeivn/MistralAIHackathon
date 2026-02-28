# pyright: basic
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Campaign(BaseModel):
    id: str
    name: str
    scenario_id: str
    created_by: str | None = None
    status: str = "draft"
    created_at: datetime | None = None
