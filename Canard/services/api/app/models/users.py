# pyright: basic
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    id: str
    org_id: str
    email: str
    password_hash: str
    full_name: str
    role: str = "viewer"
    is_active: bool = True
    last_login_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
