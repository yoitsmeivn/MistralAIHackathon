# pyright: basic
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.calls import Call


class StartCallRequest(BaseModel):
    employee_id: str
    script_id: str
    caller_id: str | None = None
    campaign_id: str | None = None
    assignment_id: str | None = None


class StartCallResponse(BaseModel):
    call_id: str
    status: str


class CallListItem(BaseModel):
    id: str
    employee_id: str
    employee_name: str | None = None
    script_name: str | None = None
    caller_name: str | None = None
    status: str
    risk_score: int | None = None
    employee_compliance: str | None = None
    started_at: datetime | None = None


class CallDetail(BaseModel):
    call: Call


class HealthResponse(BaseModel):
    status: str
    timestamp: str
