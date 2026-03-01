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
    boss_id: str | None = None


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


# ── Analytics aggregates ──


class RiskTrendPoint(CamelModel):
    date: str
    avg_risk: float
    call_count: int


class DepartmentTrendPoint(CamelModel):
    date: str
    department: str
    total_calls: int
    failed_calls: int
    failure_rate: float


class RepeatOffenderResponse(CamelModel):
    employee_id: str
    employee_name: str
    department: str
    total_tests: int
    failed_tests: int
    failure_rate: float
    most_recent_failure: str
    common_flags: list[str] = Field(default_factory=list)
    risk_scores: list[int] = Field(default_factory=list)


class AttackVectorSummary(CamelModel):
    attack_vector: str
    total_calls: int
    failure_rate: float
    avg_risk_score: float


class CampaignEffectivenessItem(CamelModel):
    campaign_id: str
    campaign_name: str
    attack_vector: str
    total_calls: int
    failed_calls: int
    passed_calls: int
    partial_calls: int
    failure_rate: float
    avg_risk_score: float
    avg_duration_seconds: float


class CampaignEffectivenessResponse(CamelModel):
    campaigns: list[CampaignEffectivenessItem] = Field(default_factory=list)
    by_attack_vector: list[AttackVectorSummary] = Field(default_factory=list)


class FlagFrequencyResponse(CamelModel):
    flag: str
    count: int
    percentage: float
    is_positive: bool


class HeatmapCellResponse(CamelModel):
    attack_vector: str
    department: str
    total_calls: int
    failure_rate: float
    avg_risk_score: float


class EmployeeCallHistoryItem(CamelModel):
    id: str
    campaign_name: str = ""
    caller_name: str = ""
    attack_vector: str = ""
    status: str = "pending"
    started_at: str = ""
    duration: str = ""
    duration_seconds: int | None = None
    risk_score: int = 0
    employee_compliance: str = ""
    flags: list[str] = Field(default_factory=list)
    ai_summary: str = ""


class EmployeeAnalyticsResponse(CamelModel):
    id: str
    full_name: str
    email: str = ""
    phone: str = ""
    department: str = ""
    job_title: str = ""
    risk_level: str = "unknown"
    is_active: bool = True
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    partial_tests: int = 0
    failure_rate: float = 0.0
    avg_risk_score: float = 0.0
    risk_score_trend: list[int] = Field(default_factory=list)
    risk_score_dates: list[str] = Field(default_factory=list)
    compliance_breakdown: dict[str, int] = Field(default_factory=dict)
    flag_summary: list[FlagFrequencyResponse] = Field(default_factory=list)
    calls: list[EmployeeCallHistoryItem] = Field(default_factory=list)


# ── Smart Dashboard Widgets ──


class WidgetEmployee(CamelModel):
    id: str
    full_name: str
    department: str = ""
    risk_score: float = 0.0
    failure_rate: float = 0.0
    total_tests: int = 0
    recent_flags: list[str] = Field(default_factory=list)


class WidgetDeptRisk(CamelModel):
    department: str
    avg_risk: float = 0.0
    failure_rate: float = 0.0
    employee_count: int = 0
    total_tests: int = 0
    failed_tests: int = 0


class RiskHotspotWidgetResponse(CamelModel):
    overall_risk: float = 0.0
    risk_trend: str = "neutral"
    worst_department: str = ""
    worst_attack_vector: str = ""
    top_risk_employees: list[WidgetEmployee] = Field(default_factory=list)
    dept_breakdown: list[WidgetDeptRisk] = Field(default_factory=list)


class WidgetRecentFailure(CamelModel):
    call_id: str
    employee_id: str
    employee_name: str = ""
    department: str = ""
    attack_vector: str = ""
    risk_score: float = 0.0
    flags: list[str] = Field(default_factory=list)
    occurred_at: str = ""


class RecentFailuresWidgetResponse(CamelModel):
    failures_7d: int = 0
    failures_30d: int = 0
    trend: str = "neutral"
    most_common_flag: str = ""
    recent_failures: list[WidgetRecentFailure] = Field(default_factory=list)


class WidgetCampaignDetail(CamelModel):
    id: str
    name: str
    attack_vector: str = ""
    total_calls: int = 0
    completed_calls: int = 0
    failure_rate: float = 0.0
    avg_risk: float = 0.0


class CampaignPulseWidgetResponse(CamelModel):
    active_count: int = 0
    completion_rate: float = 0.0
    best_performing: str = ""
    worst_performing: str = ""
    campaigns: list[WidgetCampaignDetail] = Field(default_factory=list)


class SmartWidgetsResponse(CamelModel):
    risk_hotspot: RiskHotspotWidgetResponse = Field(default_factory=RiskHotspotWidgetResponse)
    recent_failures: RecentFailuresWidgetResponse = Field(default_factory=RecentFailuresWidgetResponse)
    campaign_pulse: CampaignPulseWidgetResponse = Field(default_factory=CampaignPulseWidgetResponse)


# ── Departmental Failure Pivots ──


class DeptFlagPivotCell(CamelModel):
    department: str
    flag: str
    count: int = 0
    total_dept_calls: int = 0
    percentage: float = 0.0
    affected_employees: int = 0
    is_positive: bool = False


class DeptFlagPivotResponse(CamelModel):
    cells: list[DeptFlagPivotCell] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
    positive_flags: list[str] = Field(default_factory=list)
    department_totals: dict[str, int] = Field(default_factory=dict)
    flag_totals: dict[str, int] = Field(default_factory=dict)


# ── Hierarchical Risk Roll-Up ──


class OrgTreeNode(CamelModel):
    id: str
    full_name: str
    department: str = ""
    job_title: str = ""
    risk_level: str = "unknown"
    personal_risk_score: float = 0.0
    personal_failure_rate: float = 0.0
    personal_total_tests: int = 0
    personal_failed_tests: int = 0
    team_risk_score: float = 0.0
    team_failure_rate: float = 0.0
    team_total_tests: int = 0
    team_failed_tests: int = 0
    depth: int = 0
    children: list["OrgTreeNode"] = Field(default_factory=list)


class HierarchyRiskResponse(CamelModel):
    manager: OrgTreeNode
    total_downstream_employees: int = 0
    highest_risk_path: list[str] = Field(default_factory=list)
    risk_hotspots: list[OrgTreeNode] = Field(default_factory=list)
