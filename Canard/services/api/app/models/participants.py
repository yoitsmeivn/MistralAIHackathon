# pyright: basic
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Participant(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    team: str | None = None
    active: bool = True
    opt_in: bool = False
    created_at: datetime | None = None
