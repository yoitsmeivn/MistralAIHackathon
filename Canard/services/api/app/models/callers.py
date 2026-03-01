# pyright: basic
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Caller(BaseModel):
    id: str
    org_id: str
    created_by: str | None = None
    persona_name: str
    persona_role: str | None = None
    persona_company: str | None = None
    voice_profile: dict[str, Any] = Field(default_factory=dict)
    phone_number: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
