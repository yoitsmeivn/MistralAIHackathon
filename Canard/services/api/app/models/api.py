# pyright: basic
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.analysis import Analysis
from app.models.calls import Call
from app.models.turns import Turn


class StartCallRequest(BaseModel):
    participant_id: str
    scenario_id: str
    campaign_id: str | None = None


class StartCallResponse(BaseModel):
    call_id: str
    twilio_call_sid: str
    status: str


class CallListItem(BaseModel):
    id: str
    participant_id: str
    participant_name: str | None = None
    scenario_name: str | None = None
    status: str
    consented: bool
    risk_score: int | None = None
    started_at: datetime | None = None


class CallDetail(BaseModel):
    call: Call
    turns: list[Turn] = Field(default_factory=list)
    analysis: Analysis | None = None


class AnalysisSummary(BaseModel):
    call_id: str
    risk_score: int
    flags: list[str]
    summary: str
    coaching: str


class HealthResponse(BaseModel):
    status: str
    timestamp: str
