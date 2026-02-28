# pyright: basic
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Scenario(BaseModel):
    id: str
    name: str
    description: str
    script_guidelines: str
    difficulty: str = "medium"
    created_at: datetime | None = None
