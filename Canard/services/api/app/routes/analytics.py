# pyright: basic, reportMissingImports=false
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from app.db import queries
from app.models.api import (
    AttackVectorSummary,
    CampaignEffectivenessItem,
    CampaignEffectivenessResponse,
    DepartmentTrendPoint,
    EmployeeAnalyticsResponse,
    EmployeeCallHistoryItem,
    FlagFrequencyResponse,
    HeatmapCellResponse,
    RepeatOffenderResponse,
    RiskTrendPoint,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Flags that indicate the employee responded correctly
POSITIVE_FLAGS = {
    "Proper Verification",
    "Asked Questions",
    "Immediate Rejection",
    "Proper Protocol",
    "Requested Verification",
}


def _format_duration(seconds: int | None) -> str:
    if not seconds:
        return "0:00"
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


# ── Risk Trend ───────────────────────────────────────────────────────


@router.get("/risk-trend", response_model=list[RiskTrendPoint])
async def api_risk_trend(
    org_id: str = Query(...),
    days: int = Query(30, le=90),
) -> list[RiskTrendPoint]:
    all_calls = queries.list_calls(org_id=org_id, limit=10000)

    today = datetime.now(timezone.utc).date()
    date_range = [(today - timedelta(days=i)) for i in range(days - 1, -1, -1)]

    daily: dict[str, list[int]] = {d.isoformat(): [] for d in date_range}

    for c in all_calls:
        if c.get("status") != "completed":
            continue
        started = c.get("started_at") or c.get("created_at") or ""
        if not started:
            continue
        day_key = started[:10]
        if day_key in daily and c.get("risk_score") is not None:
            daily[day_key].append(c["risk_score"])

    items: list[RiskTrendPoint] = []
    for d in date_range:
        key = d.isoformat()
        scores = daily[key]
        avg = round(sum(scores) / len(scores), 1) if scores else 0
        items.append(
            RiskTrendPoint(
                date=d.strftime("%b %d"),
                avg_risk=avg,
                call_count=len(scores),
            )
        )
    return items


# ── Department Trends ────────────────────────────────────────────────


@router.get("/department-trends", response_model=list[DepartmentTrendPoint])
async def api_department_trends(
    org_id: str = Query(...),
    days: int = Query(30, le=90),
) -> list[DepartmentTrendPoint]:
    employees = queries.list_employees(org_id, active_only=False)
    all_calls = queries.list_calls(org_id=org_id, limit=10000)

    emp_dept: dict[str, str] = {
        e["id"]: e.get("department", "Other") for e in employees
    }

    today = datetime.now(timezone.utc).date()
    date_range = [(today - timedelta(days=i)) for i in range(days - 1, -1, -1)]

    # {date_iso: {department: {total, failed}}}
    buckets: dict[str, dict[str, dict[str, int]]] = {
        d.isoformat(): defaultdict(lambda: {"total": 0, "failed": 0})
        for d in date_range
    }

    for c in all_calls:
        if c.get("status") != "completed":
            continue
        started = c.get("started_at") or c.get("created_at") or ""
        if not started:
            continue
        day_key = started[:10]
        if day_key not in buckets:
            continue
        dept = emp_dept.get(c.get("employee_id", ""), "Other")
        buckets[day_key][dept]["total"] += 1
        if c.get("employee_compliance") == "failed":
            buckets[day_key][dept]["failed"] += 1

    items: list[DepartmentTrendPoint] = []
    for d in date_range:
        key = d.isoformat()
        label = d.strftime("%b %d")
        for dept, stats in buckets[key].items():
            rate = round(stats["failed"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0
            items.append(
                DepartmentTrendPoint(
                    date=label,
                    department=dept,
                    total_calls=stats["total"],
                    failed_calls=stats["failed"],
                    failure_rate=rate,
                )
            )
    return items


# ── Repeat Offenders ─────────────────────────────────────────────────


@router.get("/repeat-offenders", response_model=list[RepeatOffenderResponse])
async def api_repeat_offenders(
    org_id: str = Query(...),
    min_failures: int = Query(2, ge=1),
) -> list[RepeatOffenderResponse]:
    employees = queries.list_employees(org_id, active_only=False)
    all_calls = queries.list_calls(org_id=org_id, limit=10000)

    emp_lookup: dict[str, dict] = {e["id"]: e for e in employees}

    # Group completed calls by employee
    by_employee: dict[str, list[dict]] = defaultdict(list)
    for c in all_calls:
        if c.get("status") != "completed":
            continue
        eid = c.get("employee_id", "")
        if eid:
            by_employee[eid].append(c)

    items: list[RepeatOffenderResponse] = []
    for eid, calls in by_employee.items():
        failed = [c for c in calls if c.get("employee_compliance") == "failed"]
        if len(failed) < min_failures:
            continue

        emp = emp_lookup.get(eid, {})
        # Collect all flags across failures
        all_flags: list[str] = []
        for c in failed:
            all_flags.extend(c.get("flags") or [])
        common = [f for f, _ in Counter(all_flags).most_common(3)]

        # Chronological risk scores for sparkline
        sorted_calls = sorted(calls, key=lambda x: x.get("started_at") or x.get("created_at") or "")
        risk_scores = [c.get("risk_score", 0) or 0 for c in sorted_calls]

        most_recent = max(
            (c.get("started_at") or c.get("created_at") or "" for c in failed),
            default="",
        )

        total = len(calls)
        items.append(
            RepeatOffenderResponse(
                employee_id=eid,
                employee_name=emp.get("full_name", "Unknown"),
                department=emp.get("department", "Unknown"),
                total_tests=total,
                failed_tests=len(failed),
                failure_rate=round(len(failed) / total * 100, 1) if total > 0 else 0,
                most_recent_failure=most_recent[:10] if most_recent else "",
                common_flags=common,
                risk_scores=risk_scores,
            )
        )

    items.sort(key=lambda x: x.failure_rate, reverse=True)
    return items


# ── Campaign Effectiveness ───────────────────────────────────────────


@router.get("/campaign-effectiveness", response_model=CampaignEffectivenessResponse)
async def api_campaign_effectiveness(
    org_id: str = Query(...),
) -> CampaignEffectivenessResponse:
    campaigns = queries.list_campaigns(org_id)
    all_calls = queries.list_calls(org_id=org_id, limit=10000)

    camp_lookup: dict[str, dict] = {c["id"]: c for c in campaigns}

    # Group calls by campaign
    by_campaign: dict[str, list[dict]] = defaultdict(list)
    for c in all_calls:
        if c.get("status") != "completed":
            continue
        cid = c.get("campaign_id", "")
        if cid:
            by_campaign[cid].append(c)

    campaign_items: list[CampaignEffectivenessItem] = []
    for cid, calls in by_campaign.items():
        camp = camp_lookup.get(cid, {})
        total = len(calls)
        failed = sum(1 for c in calls if c.get("employee_compliance") == "failed")
        passed = sum(1 for c in calls if c.get("employee_compliance") == "passed")
        partial = sum(1 for c in calls if c.get("employee_compliance") == "partial")
        scores = [c.get("risk_score", 0) or 0 for c in calls]
        durations = [c.get("duration_seconds", 0) or 0 for c in calls]

        campaign_items.append(
            CampaignEffectivenessItem(
                campaign_id=cid,
                campaign_name=camp.get("name", "Unknown"),
                attack_vector=camp.get("attack_vector", "Unknown"),
                total_calls=total,
                failed_calls=failed,
                passed_calls=passed,
                partial_calls=partial,
                failure_rate=round(failed / total * 100, 1) if total > 0 else 0,
                avg_risk_score=round(sum(scores) / len(scores), 1) if scores else 0,
                avg_duration_seconds=round(sum(durations) / len(durations), 1) if durations else 0,
            )
        )

    # Aggregate by attack vector
    vector_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "failed": 0, "scores": []})
    for item in campaign_items:
        v = item.attack_vector
        vector_stats[v]["total"] += item.total_calls
        vector_stats[v]["failed"] += item.failed_calls
        vector_stats[v]["scores"].extend(
            [item.avg_risk_score] * item.total_calls
        )

    vector_items: list[AttackVectorSummary] = []
    for vector, stats in vector_stats.items():
        total = stats["total"]
        vector_items.append(
            AttackVectorSummary(
                attack_vector=vector,
                total_calls=total,
                failure_rate=round(stats["failed"] / total * 100, 1) if total > 0 else 0,
                avg_risk_score=round(sum(stats["scores"]) / len(stats["scores"]), 1)
                if stats["scores"]
                else 0,
            )
        )

    vector_items.sort(key=lambda x: x.failure_rate, reverse=True)
    campaign_items.sort(key=lambda x: x.failure_rate, reverse=True)

    return CampaignEffectivenessResponse(
        campaigns=campaign_items,
        by_attack_vector=vector_items,
    )


# ── Flag Frequency ───────────────────────────────────────────────────


@router.get("/flag-frequency", response_model=list[FlagFrequencyResponse])
async def api_flag_frequency(
    org_id: str = Query(...),
    campaign_id: str | None = Query(None),
) -> list[FlagFrequencyResponse]:
    all_calls = queries.list_calls(
        org_id=org_id,
        campaign_id=campaign_id,
        limit=10000,
    )

    completed = [c for c in all_calls if c.get("status") == "completed"]
    total_completed = len(completed)
    if total_completed == 0:
        return []

    flag_counts: Counter[str] = Counter()
    for c in completed:
        for flag in c.get("flags") or []:
            flag_counts[flag] += 1

    items: list[FlagFrequencyResponse] = []
    for flag, count in flag_counts.most_common():
        items.append(
            FlagFrequencyResponse(
                flag=flag,
                count=count,
                percentage=round(count / total_completed * 100, 1),
                is_positive=flag in POSITIVE_FLAGS,
            )
        )
    return items


# ── Attack Heatmap ───────────────────────────────────────────────────


@router.get("/attack-heatmap", response_model=list[HeatmapCellResponse])
async def api_attack_heatmap(
    org_id: str = Query(...),
) -> list[HeatmapCellResponse]:
    employees = queries.list_employees(org_id, active_only=False)
    campaigns = queries.list_campaigns(org_id)
    all_calls = queries.list_calls(org_id=org_id, limit=10000)

    emp_dept: dict[str, str] = {e["id"]: e.get("department", "Other") for e in employees}
    camp_vector: dict[str, str] = {c["id"]: c.get("attack_vector", "Unknown") for c in campaigns}

    # {(vector, dept): {total, failed, scores}}
    cells: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"total": 0, "failed": 0, "scores": []}
    )

    for c in all_calls:
        if c.get("status") != "completed":
            continue
        vector = camp_vector.get(c.get("campaign_id", ""), "Unknown")
        dept = emp_dept.get(c.get("employee_id", ""), "Other")
        cell = cells[(vector, dept)]
        cell["total"] += 1
        if c.get("employee_compliance") == "failed":
            cell["failed"] += 1
        cell["scores"].append(c.get("risk_score", 0) or 0)

    items: list[HeatmapCellResponse] = []
    for (vector, dept), stats in cells.items():
        total = stats["total"]
        items.append(
            HeatmapCellResponse(
                attack_vector=vector,
                department=dept,
                total_calls=total,
                failure_rate=round(stats["failed"] / total * 100, 1) if total > 0 else 0,
                avg_risk_score=round(sum(stats["scores"]) / len(stats["scores"]), 1)
                if stats["scores"]
                else 0,
            )
        )
    return items


# ── Employee Detail ──────────────────────────────────────────────────


@router.get("/employee-detail/{employee_id}", response_model=EmployeeAnalyticsResponse)
async def api_employee_detail(
    employee_id: str,
    org_id: str = Query(...),
) -> EmployeeAnalyticsResponse:
    emp = queries.get_employee(employee_id)
    if not emp:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Employee not found")

    all_calls = queries.list_calls(org_id=org_id, employee_id=employee_id, limit=10000)
    campaigns = queries.list_campaigns(org_id)
    callers = queries.list_callers(org_id, active_only=False)

    camp_lookup: dict[str, dict] = {c["id"]: c for c in campaigns}
    caller_lookup: dict[str, dict] = {c["id"]: c for c in callers}

    completed = [c for c in all_calls if c.get("status") == "completed"]

    # Compliance counts
    passed = sum(1 for c in completed if c.get("employee_compliance") == "passed")
    failed = sum(1 for c in completed if c.get("employee_compliance") == "failed")
    partial = sum(1 for c in completed if c.get("employee_compliance") == "partial")
    total = len(completed)

    # Risk score trend (chronological)
    sorted_calls = sorted(completed, key=lambda x: x.get("started_at") or x.get("created_at") or "")
    risk_scores = [c.get("risk_score", 0) or 0 for c in sorted_calls]
    risk_dates = [
        (c.get("started_at") or c.get("created_at") or "")[:10]
        for c in sorted_calls
    ]

    # Avg risk
    avg_risk = round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else 0

    # Flag summary
    flag_counts: Counter[str] = Counter()
    for c in completed:
        for flag in c.get("flags") or []:
            flag_counts[flag] += 1
    flag_summary = [
        FlagFrequencyResponse(
            flag=flag,
            count=count,
            percentage=round(count / total * 100, 1) if total > 0 else 0,
            is_positive=flag in POSITIVE_FLAGS,
        )
        for flag, count in flag_counts.most_common()
    ]

    # Enrich call history
    call_items: list[EmployeeCallHistoryItem] = []
    for c in sorted_calls:
        camp = camp_lookup.get(c.get("campaign_id", ""), {})
        caller = caller_lookup.get(c.get("caller_id", ""), {})
        dur_s = c.get("duration_seconds")
        call_items.append(
            EmployeeCallHistoryItem(
                id=c["id"],
                campaign_name=camp.get("name", "Ad-hoc"),
                caller_name=caller.get("persona_name", "Unknown"),
                attack_vector=camp.get("attack_vector", "Unknown"),
                status=c.get("status", ""),
                started_at=c.get("started_at") or c.get("created_at") or "",
                duration=_format_duration(dur_s),
                duration_seconds=dur_s,
                risk_score=c.get("risk_score", 0) or 0,
                employee_compliance=c.get("employee_compliance", ""),
                flags=c.get("flags") or [],
                ai_summary=c.get("ai_summary") or "",
            )
        )

    return EmployeeAnalyticsResponse(
        id=emp["id"],
        full_name=emp.get("full_name", ""),
        email=emp.get("email", ""),
        phone=emp.get("phone", ""),
        department=emp.get("department", ""),
        job_title=emp.get("job_title", ""),
        risk_level=emp.get("risk_level", "unknown"),
        is_active=emp.get("is_active", True),
        total_tests=total,
        passed_tests=passed,
        failed_tests=failed,
        partial_tests=partial,
        failure_rate=round(failed / total * 100, 1) if total > 0 else 0,
        avg_risk_score=avg_risk,
        risk_score_trend=risk_scores,
        risk_score_dates=risk_dates,
        compliance_breakdown={"passed": passed, "failed": failed, "partial": partial},
        flag_summary=flag_summary,
        calls=call_items,
    )
