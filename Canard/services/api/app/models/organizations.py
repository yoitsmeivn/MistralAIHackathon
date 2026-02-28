# pyright: basic
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Organization(BaseModel):
    id: str
    name: str
    slug: str
    industry: str | None = None
    plan_tier: str = "free"
    max_employees: int | None = None
    max_callers: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
