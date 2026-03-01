# pyright: basic, reportMissingImports=false
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from app.auth.middleware import OptionalUser
from app.db import queries
from app.models.api import (
    CallsOverTimeResponse,
    CampaignPulseWidgetResponse,
    DashboardStatResponse,
    RecentFailuresWidgetResponse,
    RiskDistributionResponse,
    RiskHotspotWidgetResponse,
    SmartWidgetsResponse,
    WidgetCampaignDetail,
    WidgetDeptRisk,
    WidgetEmployee,
    WidgetRecentFailure,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

RISK_COLORS = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e", "unknown": "#94a3b8"}
DEPT_COLORS = ["#ef4444", "#f59e0b", "#22c55e", "#3b82f6", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"]


@router.get("/stats", response_model=list[DashboardStatResponse])
async def api_dashboard_stats(
    user: OptionalUser,
    org_id: str | None = Query(None),
) -> list[DashboardStatResponse]:
    resolved_org_id = user["org_id"] if user else org_id
    if not resolved_org_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    campaigns = queries.list_campaigns(resolved_org_id)
    employees = queries.list_employees(resolved_org_id, active_only=False)
    all_calls = queries.list_calls(org_id=resolved_org_id, limit=10000)

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
    user: OptionalUser,
    org_id: str | None = Query(None),
) -> list[RiskDistributionResponse]:
    resolved_org_id = user["org_id"] if user else org_id
    if not resolved_org_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    employees = queries.list_employees(resolved_org_id, active_only=False)
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
    user: OptionalUser,
    org_id: str | None = Query(None),
) -> list[RiskDistributionResponse]:
    resolved_org_id = user["org_id"] if user else org_id
    if not resolved_org_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    employees = queries.list_employees(resolved_org_id, active_only=False)
    all_calls = queries.list_calls(org_id=resolved_org_id, limit=10000)

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
    user: OptionalUser,
    org_id: str | None = Query(None),
    days: int = Query(7, le=30),
) -> list[CallsOverTimeResponse]:
    resolved_org_id = user["org_id"] if user else org_id
    if not resolved_org_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    all_calls = queries.list_calls(org_id=resolved_org_id, limit=10000)

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


# Flags that indicate the employee responded correctly
_POSITIVE_FLAGS = {
    "Proper Verification",
    "Asked Questions",
    "Immediate Rejection",
    "Proper Protocol",
    "Requested Verification",
}


@router.get("/smart-widgets", response_model=SmartWidgetsResponse)
async def api_smart_widgets(
    org_id: str = Query(...),
) -> SmartWidgetsResponse:
    employees = queries.list_employees(org_id, active_only=False)
    all_calls = queries.list_calls(org_id=org_id, limit=10000)
    campaigns = queries.list_campaigns(org_id)

    emp_lookup: dict[str, dict] = {e["id"]: e for e in employees}
    camp_lookup: dict[str, dict] = {c["id"]: c for c in campaigns}

    completed = [c for c in all_calls if c.get("status") == "completed"]
    now = datetime.now(timezone.utc)
    cutoff_7d = (now - timedelta(days=7)).isoformat()
    cutoff_14d = (now - timedelta(days=14)).isoformat()
    cutoff_30d = (now - timedelta(days=30)).isoformat()

    # ── Risk Hotspot Widget ──

    # Per-employee aggregates
    emp_stats: dict[str, dict] = defaultdict(lambda: {"scores": [], "total": 0, "failed": 0, "flags": []})
    for c in completed:
        eid = c.get("employee_id", "")
        if not eid:
            continue
        es = emp_stats[eid]
        es["scores"].append(c.get("risk_score", 0) or 0)
        es["total"] += 1
        if c.get("employee_compliance") == "failed":
            es["failed"] += 1
        for flag in c.get("flags") or []:
            if flag not in _POSITIVE_FLAGS:
                es["flags"].append(flag)

    # Department aggregates
    dept_agg: dict[str, dict] = defaultdict(lambda: {"scores": [], "total": 0, "failed": 0, "emps": set()})
    for eid, stats in emp_stats.items():
        emp = emp_lookup.get(eid, {})
        dept = emp.get("department", "Other")
        da = dept_agg[dept]
        da["scores"].extend(stats["scores"])
        da["total"] += stats["total"]
        da["failed"] += stats["failed"]
        da["emps"].add(eid)

    dept_breakdown = [
        WidgetDeptRisk(
            department=dept,
            avg_risk=round(sum(da["scores"]) / len(da["scores"]), 1) if da["scores"] else 0,
            failure_rate=round(da["failed"] / da["total"] * 100, 1) if da["total"] > 0 else 0,
            employee_count=len(da["emps"]),
            total_tests=da["total"],
            failed_tests=da["failed"],
        )
        for dept, da in dept_agg.items()
    ]
    dept_breakdown.sort(key=lambda d: d.avg_risk, reverse=True)

    worst_dept = dept_breakdown[0].department if dept_breakdown else ""

    # Worst attack vector
    vector_fails: Counter[str] = Counter()
    vector_total: Counter[str] = Counter()
    for c in completed:
        camp = camp_lookup.get(c.get("campaign_id", ""), {})
        v = camp.get("attack_vector", "Unknown")
        vector_total[v] += 1
        if c.get("employee_compliance") == "failed":
            vector_fails[v] += 1
    worst_vector = ""
    worst_rate = 0.0
    for v, total in vector_total.items():
        rate = vector_fails[v] / total * 100 if total > 0 else 0
        if rate > worst_rate:
            worst_rate = rate
            worst_vector = v

    # Top risk employees
    top_emps: list[WidgetEmployee] = []
    for eid, stats in emp_stats.items():
        emp = emp_lookup.get(eid, {})
        avg_r = round(sum(stats["scores"]) / len(stats["scores"]), 1) if stats["scores"] else 0
        top_emps.append(
            WidgetEmployee(
                id=eid,
                full_name=emp.get("full_name", "Unknown"),
                department=emp.get("department", ""),
                risk_score=avg_r,
                failure_rate=round(stats["failed"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0,
                total_tests=stats["total"],
                recent_flags=list(dict.fromkeys(stats["flags"]))[:3],
            )
        )
    top_emps.sort(key=lambda e: e.risk_score, reverse=True)

    # 7d vs prior-7d trend
    scores_7d = [c.get("risk_score", 0) or 0 for c in completed if (c.get("started_at") or "") >= cutoff_7d]
    scores_prior = [
        c.get("risk_score", 0) or 0
        for c in completed
        if cutoff_14d <= (c.get("started_at") or "") < cutoff_7d
    ]
    avg_7d = sum(scores_7d) / len(scores_7d) if scores_7d else 0
    avg_prior = sum(scores_prior) / len(scores_prior) if scores_prior else 0
    overall_scores = [c.get("risk_score", 0) or 0 for c in completed]
    overall_risk = round(sum(overall_scores) / len(overall_scores), 1) if overall_scores else 0
    trend = "up" if avg_7d > avg_prior + 2 else ("down" if avg_7d < avg_prior - 2 else "neutral")

    risk_hotspot = RiskHotspotWidgetResponse(
        overall_risk=overall_risk,
        risk_trend=trend,
        worst_department=worst_dept,
        worst_attack_vector=worst_vector,
        top_risk_employees=top_emps[:5],
        dept_breakdown=dept_breakdown,
    )

    # ── Recent Failures Widget ──

    failed_calls = [c for c in completed if c.get("employee_compliance") == "failed"]
    failures_7d = [c for c in failed_calls if (c.get("started_at") or "") >= cutoff_7d]
    failures_30d = [c for c in failed_calls if (c.get("started_at") or "") >= cutoff_30d]
    failures_prior_7d = [
        c for c in failed_calls
        if cutoff_14d <= (c.get("started_at") or "") < cutoff_7d
    ]
    f_trend = "up" if len(failures_7d) > len(failures_prior_7d) else ("down" if len(failures_7d) < len(failures_prior_7d) else "neutral")

    neg_flags: Counter[str] = Counter()
    for c in failures_30d:
        for flag in c.get("flags") or []:
            if flag not in _POSITIVE_FLAGS:
                neg_flags[flag] += 1
    most_common_flag = neg_flags.most_common(1)[0][0] if neg_flags else ""

    sorted_failures = sorted(failed_calls, key=lambda x: x.get("started_at") or "", reverse=True)[:10]
    recent_list = [
        WidgetRecentFailure(
            call_id=c["id"],
            employee_id=c.get("employee_id", ""),
            employee_name=emp_lookup.get(c.get("employee_id", ""), {}).get("full_name", "Unknown"),
            department=emp_lookup.get(c.get("employee_id", ""), {}).get("department", ""),
            attack_vector=camp_lookup.get(c.get("campaign_id", ""), {}).get("attack_vector", "Unknown"),
            risk_score=c.get("risk_score", 0) or 0,
            flags=[f for f in (c.get("flags") or []) if f not in _POSITIVE_FLAGS],
            occurred_at=c.get("started_at") or c.get("created_at") or "",
        )
        for c in sorted_failures
    ]

    recent_failures = RecentFailuresWidgetResponse(
        failures_7d=len(failures_7d),
        failures_30d=len(failures_30d),
        trend=f_trend,
        most_common_flag=most_common_flag,
        recent_failures=recent_list,
    )

    # ── Campaign Pulse Widget ──

    active_campaigns = [c for c in campaigns if c.get("status") in ("in_progress", "active")]

    camp_details: list[WidgetCampaignDetail] = []
    for camp in campaigns:
        cid = camp["id"]
        camp_calls = [c for c in completed if c.get("campaign_id") == cid]
        total = len(camp_calls)
        c_failed = sum(1 for c in camp_calls if c.get("employee_compliance") == "failed")
        c_scores = [c.get("risk_score", 0) or 0 for c in camp_calls]
        camp_details.append(
            WidgetCampaignDetail(
                id=cid,
                name=camp.get("name", ""),
                attack_vector=camp.get("attack_vector", ""),
                total_calls=total,
                completed_calls=total,
                failure_rate=round(c_failed / total * 100, 1) if total > 0 else 0,
                avg_risk=round(sum(c_scores) / len(c_scores), 1) if c_scores else 0,
            )
        )

    with_calls = [c for c in camp_details if c.total_calls > 0]
    best = min(with_calls, key=lambda c: c.failure_rate).name if with_calls else ""
    worst = max(with_calls, key=lambda c: c.failure_rate).name if with_calls else ""

    total_camp_calls = sum(c.total_calls for c in camp_details)
    total_camp_completed = sum(c.completed_calls for c in camp_details)
    completion = round(total_camp_completed / total_camp_calls * 100, 1) if total_camp_calls > 0 else 0

    campaign_pulse = CampaignPulseWidgetResponse(
        active_count=len(active_campaigns),
        completion_rate=completion,
        best_performing=best,
        worst_performing=worst,
        campaigns=camp_details,
    )

    return SmartWidgetsResponse(
        risk_hotspot=risk_hotspot,
        recent_failures=recent_failures,
        campaign_pulse=campaign_pulse,
    )
