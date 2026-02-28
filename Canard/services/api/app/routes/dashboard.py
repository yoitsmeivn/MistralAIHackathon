# pyright: basic, reportMissingImports=false
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from app.db import queries
from app.models.api import (
    CallsOverTimeResponse,
    DashboardStatResponse,
    RiskDistributionResponse,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

RISK_COLORS = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e", "unknown": "#94a3b8"}
DEPT_COLORS = ["#ef4444", "#f59e0b", "#22c55e", "#3b82f6", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"]


@router.get("/stats", response_model=list[DashboardStatResponse])
async def api_dashboard_stats(
    org_id: str = Query(...),
) -> list[DashboardStatResponse]:
    campaigns = queries.list_campaigns(org_id)
    employees = queries.list_employees(org_id, active_only=False)
    all_calls = queries.list_calls(org_id=org_id, limit=10000)

    active_campaigns = sum(1 for c in campaigns if c.get("status") in ("in_progress", "active"))
    total_calls = len(all_calls)
    completed = [c for c in all_calls if c.get("status") == "completed"]
    tested_employee_ids = {c["employee_id"] for c in completed if c.get("employee_id")}

    avg_risk = 0
    if completed:
        scores = [c.get("risk_score", 0) or 0 for c in completed]
        avg_risk = round(sum(scores) / len(scores))

    return [
        DashboardStatResponse(label="Active Campaigns", value=str(active_campaigns), change=f"{len(campaigns)} total", trend="neutral"),
        DashboardStatResponse(label="Total Calls", value=str(total_calls), change=f"{len(completed)} completed", trend="up"),
        DashboardStatResponse(label="Employees Tested", value=str(len(tested_employee_ids)), change=f"of {len(employees)} total", trend="neutral"),
        DashboardStatResponse(label="Avg Risk Score", value=f"{avg_risk}%", change="across all calls", trend="down" if avg_risk > 60 else "up"),
    ]


@router.get("/risk-distribution", response_model=list[RiskDistributionResponse])
async def api_risk_distribution(
    org_id: str = Query(...),
) -> list[RiskDistributionResponse]:
    employees = queries.list_employees(org_id, active_only=False)
    counts: dict[str, int] = defaultdict(int)
    for emp in employees:
        level = emp.get("risk_level", "unknown") or "unknown"
        counts[level] += 1

    return [
        RiskDistributionResponse(name=f"{level.title()} Risk", value=count, fill=RISK_COLORS.get(level, "#94a3b8"))
        for level, count in counts.items()
    ]


@router.get("/risk-by-department", response_model=list[RiskDistributionResponse])
async def api_risk_by_department(
    org_id: str = Query(...),
) -> list[RiskDistributionResponse]:
    employees = queries.list_employees(org_id, active_only=False)
    all_calls = queries.list_calls(org_id=org_id, limit=10000)

    emp_dept: dict[str, str] = {e["id"]: e.get("department", "Other") for e in employees}

    dept_stats: dict[str, dict[str, int]] = {}
    for c in all_calls:
        if c.get("status") != "completed":
            continue
        dept = emp_dept.get(c.get("employee_id", ""), "Other")
        stats = dept_stats.setdefault(dept, {"failed": 0, "total": 0})
        stats["total"] += 1
        if c.get("employee_compliance") == "failed":
            stats["failed"] += 1

    items: list[RiskDistributionResponse] = []
    for i, (dept, stats) in enumerate(dept_stats.items()):
        fail_rate = round(stats["failed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        items.append(RiskDistributionResponse(name=dept, value=fail_rate, fill=DEPT_COLORS[i % len(DEPT_COLORS)]))
    return items


@router.get("/calls-over-time", response_model=list[CallsOverTimeResponse])
async def api_calls_over_time(
    org_id: str = Query(...),
    days: int = Query(7, le=30),
) -> list[CallsOverTimeResponse]:
    all_calls = queries.list_calls(org_id=org_id, limit=10000)

    today = datetime.now(timezone.utc).date()
    date_range = [(today - timedelta(days=i)) for i in range(days - 1, -1, -1)]

    daily: dict[str, dict[str, int]] = {
        d.isoformat(): {"calls": 0, "passed": 0, "failed": 0} for d in date_range
    }

    for c in all_calls:
        started = c.get("started_at") or c.get("created_at") or ""
        if not started:
            continue
        day_key = started[:10]  # YYYY-MM-DD
        if day_key in daily:
            daily[day_key]["calls"] += 1
            compliance = c.get("employee_compliance", "")
            if compliance == "passed":
                daily[day_key]["passed"] += 1
            elif compliance == "failed":
                daily[day_key]["failed"] += 1

    items: list[CallsOverTimeResponse] = []
    for d in date_range:
        key = d.isoformat()
        stats = daily[key]
        label = d.strftime("%b %d")
        items.append(CallsOverTimeResponse(date=label, calls=stats["calls"], passed=stats["passed"], failed=stats["failed"]))
    return items
