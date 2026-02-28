# pyright: basic
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Campaign(BaseModel):
    id: str
    org_id: str
    created_by: str | None = None
    name: str
    description: str | None = None
    attack_vector: str | None = None
    status: str = "draft"
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
