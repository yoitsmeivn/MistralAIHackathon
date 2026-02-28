# pyright: basic
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Employee(BaseModel):
    id: str
    org_id: str
    full_name: str
    email: str
    phone: str
    department: str | None = None
    job_title: str | None = None
    risk_level: str = "unknown"
    notes: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
