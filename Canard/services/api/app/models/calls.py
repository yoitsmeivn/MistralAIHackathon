# pyright: basic
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Call(BaseModel):
    id: str
    org_id: str
    campaign_id: str | None = None
    assignment_id: str | None = None
    caller_id: str | None = None
    script_id: str | None = None
    employee_id: str
    status: str = "pending"
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: int | None = None
    phone_from: str | None = None
    phone_to: str | None = None
    recording_url: str | None = None
    transcript: str | None = None
    transcript_json: list[dict[str, Any]] | None = None
    risk_score: int | None = None
    employee_compliance: str | None = None
    flags: list[str] = Field(default_factory=list)
    ai_summary: str | None = None
    sentiment_analysis: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
