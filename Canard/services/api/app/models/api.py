# pyright: basic
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel

from app.models.calls import Call


class CamelModel(BaseModel):
    """Base model that serialises fields as camelCase in JSON responses."""

    model_config = {"alias_generator": to_camel, "populate_by_name": True}


# ── Request / generic models ──


class StartCallRequest(BaseModel):
    employee_id: str
    script_id: str
    caller_id: str | None = None
    campaign_id: str | None = None
    assignment_id: str | None = None


class StartCallResponse(CamelModel):
    call_id: str
    status: str


class HealthResponse(BaseModel):
    status: str
    timestamp: str


# ── Employee ──


class EmployeeListItem(CamelModel):
    id: str
    full_name: str
    email: str
    phone: str = ""
    department: str = ""
    job_title: str = ""
    risk_level: str = "unknown"
    total_tests: int = 0
    failed_tests: int = 0
    last_test_date: str = ""
    is_active: bool = True


# ── Caller ──


class CallerListItem(CamelModel):
    id: str
    persona_name: str = ""
    persona_role: str = ""
    persona_company: str = ""
    phone_number: str = ""
    attack_type: str = ""
    description: str = ""
    is_active: bool = True
    total_calls: int = 0
    avg_success_rate: int = 0


# ── Campaign ──


class CampaignListItem(CamelModel):
    id: str
    name: str
    description: str = ""
    attack_vector: str = ""
    status: str = "draft"
    scheduled_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    total_calls: int = 0
    completed_calls: int = 0
    avg_risk_score: int = 0
    created_at: str = ""


# ── Call (enriched with names) ──


class CallEnriched(CamelModel):
    id: str
    employee_name: str = ""
    caller_name: str = ""
    campaign_name: str = ""
    status: str = "pending"
    started_at: str = ""
    duration: str = ""
    duration_seconds: int | None = None
    risk_score: int = 0
    employee_compliance: str = ""
    transcript: str = ""
    flags: list[str] = Field(default_factory=list)
    ai_summary: str = ""


# ── Dashboard aggregates ──


class DashboardStatResponse(CamelModel):
    label: str
    value: str
    change: str
    trend: str


class RiskDistributionResponse(CamelModel):
    name: str
    value: int
    fill: str


class CallsOverTimeResponse(CamelModel):
    date: str
    calls: int
    passed: int
    failed: int
