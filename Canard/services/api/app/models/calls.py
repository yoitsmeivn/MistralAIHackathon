# pyright: basic
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Call(BaseModel):
    id: str
    campaign_id: str | None = None
    participant_id: str
    scenario_id: str
    twilio_call_sid: str | None = None
    status: str = "pending"
    consented: bool = False
    recording_url: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime | None = None
