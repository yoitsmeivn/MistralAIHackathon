# pyright: basic
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Script(BaseModel):
    id: str
    org_id: str
    created_by: str | None = None
    name: str
    attack_type: str | None = None
    difficulty: str = "medium"
    system_prompt: str = ""
    objectives: list[str] = Field(default_factory=list)
    escalation_steps: list[str] = Field(default_factory=list)
    description: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
