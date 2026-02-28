# pyright: basic
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CampaignAssignment(BaseModel):
    id: str
    campaign_id: str
    caller_id: str
    script_id: str
    employee_id: str
    status: str = "pending"
    scheduled_at: datetime | None = None
    created_at: datetime | None = None
