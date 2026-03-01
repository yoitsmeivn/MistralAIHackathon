# pyright: basic, reportMissingImports=false
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from app.auth.middleware import OptionalUser
from app.db import queries
from app.models.api import (
    AttackVectorSummary,
    CampaignEffectivenessItem,
    CampaignEffectivenessResponse,
    DepartmentTrendPoint,
    DeptFlagPivotCell,
    DeptFlagPivotResponse,
    EmployeeAnalyticsResponse,
    EmployeeCallHistoryItem,
    FlagFrequencyResponse,
    HeatmapCellResponse,
    HierarchyRiskResponse,
    OrgTreeNode,
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


def _get_flag_str(f: Any) -> str:
    if isinstance(f, str):
        return f.replace("_", " ").title() if "_" in f and f.islower() else f
    if isinstance(f, dict):
        val = f.get("name") or f.get("flag") or f.get("type") or f.get("description")
        if val:
            val_str = str(val)
            return val_str.replace("_", " ").title() if "_" in val_str and val_str.islower() else val_str
        return str(f)
    return str(f)



def _resolve_org(user: dict | None, org_id: str | None) -> str:
    resolved = user["org_id"] if user else org_id
    if not resolved:
        raise HTTPException(status_code=401, detail="Authentication required")
    return resolved


def _format_duration(seconds: int | None) -> str:
    if not seconds:
        return "0:00"
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


# ── Risk Trend ───────────────────────────────────────────────────────


@router.get("/risk-trend", response_model=list[RiskTrendPoint])
async def api_risk_trend(
    user: OptionalUser,
    org_id: str | None = Query(None),
    days: int = Query(30, le=90),
) -> list[RiskTrendPoint]:
    org_id = _resolve_org(user, org_id)
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
    user: OptionalUser,
    org_id: str | None = Query(None),
    days: int = Query(30, le=90),
) -> list[DepartmentTrendPoint]:
    org_id = _resolve_org(user, org_id)
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
    user: OptionalUser,
    org_id: str | None = Query(None),
    min_failures: int = Query(2, ge=1),
) -> list[RepeatOffenderResponse]:
    org_id = _resolve_org(user, org_id)
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
            all_flags.extend([_get_flag_str(f) for f in (c.get("flags") or [])])
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
    user: OptionalUser,
    org_id: str | None = Query(None),
) -> CampaignEffectivenessResponse:
    org_id = _resolve_org(user, org_id)
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
    user: OptionalUser,
    org_id: str | None = Query(None),
    campaign_id: str | None = Query(None),
) -> list[FlagFrequencyResponse]:
    org_id = _resolve_org(user, org_id)
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
        for f_raw in c.get("flags") or []:
            flag_str = _get_flag_str(f_raw)
            flag_counts[flag_str] += 1

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
    user: OptionalUser,
    org_id: str | None = Query(None),
) -> list[HeatmapCellResponse]:
    org_id = _resolve_org(user, org_id)
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
    user: OptionalUser,
    org_id: str | None = Query(None),
) -> EmployeeAnalyticsResponse:
    org_id = _resolve_org(user, org_id)

    emp = queries.get_employee(employee_id)
    if not emp:
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
        for f_raw in c.get("flags") or []:
            flag_counts[_get_flag_str(f_raw)] += 1
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
                flags=[_get_flag_str(f) for f in (c.get("flags") or [])],
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


# ── Departmental Failure Pivot ──────────────────────────────────────


@router.get("/dept-flag-pivot", response_model=DeptFlagPivotResponse)
async def api_dept_flag_pivot(
    user: OptionalUser,
    org_id: str | None = Query(None),
    flag_type: str | None = Query(None),
) -> DeptFlagPivotResponse:
    org_id = _resolve_org(user, org_id)
    employees = queries.list_employees(org_id, active_only=False)
    all_calls = queries.list_calls(org_id=org_id, limit=10000)

    emp_lookup: dict[str, dict] = {e["id"]: e for e in employees}
    completed = [c for c in all_calls if c.get("status") == "completed"]

    # Dept call totals
    dept_call_totals: Counter[str] = Counter()
    for c in completed:
        dept = emp_lookup.get(c.get("employee_id", ""), {}).get("department", "Other")
        dept_call_totals[dept] += 1

    # (dept, flag) -> {count, employees}
    pivot: dict[tuple[str, str], dict] = defaultdict(lambda: {"count": 0, "employees": set()})
    flag_totals: Counter[str] = Counter()

    for c in completed:
        eid = c.get("employee_id", "")
        dept = emp_lookup.get(eid, {}).get("department", "Other")
        for f_raw in c.get("flags") or []:
            flag_str = _get_flag_str(f_raw)
            is_pos = flag_str in POSITIVE_FLAGS
            if flag_type == "positive" and not is_pos:
                continue
            if flag_type == "negative" and is_pos:
                continue
            key = (dept, flag_str)
            pivot[key]["count"] += 1
            pivot[key]["employees"].add(eid)
            flag_totals[flag_str] += 1

    cells: list[DeptFlagPivotCell] = []
    for (dept, flag), data in pivot.items():
        dept_total = dept_call_totals.get(dept, 0)
        cells.append(
            DeptFlagPivotCell(
                department=dept,
                flag=flag,
                count=data["count"],
                total_dept_calls=dept_total,
                percentage=round(data["count"] / dept_total * 100, 1) if dept_total > 0 else 0,
                affected_employees=len(data["employees"]),
                is_positive=flag in POSITIVE_FLAGS,
            )
        )

    # Sorted lists for axis labels
    departments = [d for d, _ in dept_call_totals.most_common()]
    flags = [f for f, _ in flag_totals.most_common()]
    pos_flags = [f for f in flags if f in POSITIVE_FLAGS]

    return DeptFlagPivotResponse(
        cells=cells,
        departments=departments,
        flags=flags,
        positive_flags=pos_flags,
        department_totals=dict(dept_call_totals),
        flag_totals=dict(flag_totals),
    )


# ── Hierarchical Risk Roll-Up ──────────────────────────────────────


@router.get("/hierarchy-risk/{employee_id}", response_model=HierarchyRiskResponse)
async def api_hierarchy_risk(
    employee_id: str,
    user: OptionalUser,
    org_id: str | None = Query(None),
) -> HierarchyRiskResponse:
    org_id = _resolve_org(user, org_id)

    emp = queries.get_employee(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    subordinates = queries.get_subordinates(employee_id)
    all_sub_ids = {s["id"] for s in subordinates}

    # Fetch all org calls in one go
    all_calls = queries.list_calls(org_id=org_id, limit=10000)
    completed = [c for c in all_calls if c.get("status") == "completed"]

    # Group calls by employee
    calls_by_emp: dict[str, list[dict]] = defaultdict(list)
    for c in completed:
        eid = c.get("employee_id", "")
        if eid:
            calls_by_emp[eid].append(c)

    def _personal_metrics(eid: str) -> tuple[float, float, int, int]:
        calls = calls_by_emp.get(eid, [])
        total = len(calls)
        failed = sum(1 for c in calls if c.get("employee_compliance") == "failed")
        scores = [c.get("risk_score", 0) or 0 for c in calls]
        avg = round(sum(scores) / len(scores), 1) if scores else 0
        rate = round(failed / total * 100, 1) if total > 0 else 0
        return avg, rate, total, failed

    # Build nodes for each subordinate
    nodes: dict[str, OrgTreeNode] = {}
    for s in subordinates:
        sid = s["id"]
        avg, rate, total, failed = _personal_metrics(sid)
        nodes[sid] = OrgTreeNode(
            id=sid,
            full_name=s.get("full_name", ""),
            department=s.get("department", ""),
            job_title=s.get("job_title", ""),
            risk_level=s.get("risk_level", "unknown"),
            personal_risk_score=avg,
            personal_failure_rate=rate,
            personal_total_tests=total,
            personal_failed_tests=failed,
            depth=s.get("depth", 1),
        )

    # Wire children to parents
    for s in subordinates:
        sid = s["id"]
        boss = s.get("boss_id")
        if boss and boss in nodes:
            nodes[boss].children.append(nodes[sid])
        # If boss == employee_id, it's a direct report (handled below)

    # Roll up team metrics bottom-up (process deepest first)
    max_depth = max((n.depth for n in nodes.values()), default=0)
    for d in range(max_depth, 0, -1):
        for node in nodes.values():
            if node.depth != d:
                continue
            # Team = personal + all children's team
            t_total = node.personal_total_tests
            t_failed = node.personal_failed_tests
            t_risk_weighted = node.personal_risk_score * max(node.personal_total_tests, 1)
            t_weight = max(node.personal_total_tests, 1)
            for child in node.children:
                t_total += child.team_total_tests
                t_failed += child.team_failed_tests
                t_risk_weighted += child.team_risk_score * max(child.team_total_tests, 1)
                t_weight += max(child.team_total_tests, 1)
            node.team_total_tests = t_total
            node.team_failed_tests = t_failed
            node.team_risk_score = round(t_risk_weighted / t_weight, 1) if t_weight > 0 else 0
            node.team_failure_rate = round(t_failed / t_total * 100, 1) if t_total > 0 else 0

    # Build root node for the manager
    m_avg, m_rate, m_total, m_failed = _personal_metrics(employee_id)
    direct_reports = [nodes[s["id"]] for s in subordinates if s.get("boss_id") == employee_id]
    direct_reports.sort(key=lambda n: n.team_risk_score, reverse=True)

    # Roll up team for the root
    rt_total = m_total
    rt_failed = m_failed
    rt_risk_w = m_avg * max(m_total, 1)
    rt_weight = max(m_total, 1)
    for child in direct_reports:
        rt_total += child.team_total_tests
        rt_failed += child.team_failed_tests
        rt_risk_w += child.team_risk_score * max(child.team_total_tests, 1)
        rt_weight += max(child.team_total_tests, 1)

    root = OrgTreeNode(
        id=employee_id,
        full_name=emp.get("full_name", ""),
        department=emp.get("department", ""),
        job_title=emp.get("job_title", ""),
        risk_level=emp.get("risk_level", "unknown"),
        personal_risk_score=m_avg,
        personal_failure_rate=m_rate,
        personal_total_tests=m_total,
        personal_failed_tests=m_failed,
        team_risk_score=round(rt_risk_w / rt_weight, 1) if rt_weight > 0 else 0,
        team_failure_rate=round(rt_failed / rt_total * 100, 1) if rt_total > 0 else 0,
        team_total_tests=rt_total,
        team_failed_tests=rt_failed,
        depth=0,
        children=direct_reports,
    )

    # Highest-risk path: greedy walk to child with highest team_risk_score
    risk_path = [root.id]
    current = root
    while current.children:
        worst = max(current.children, key=lambda n: n.team_risk_score)
        risk_path.append(worst.id)
        current = worst

    # Top 3 risk hotspots (by personal risk, excluding root)
    all_nodes = list(nodes.values())
    all_nodes.sort(key=lambda n: n.personal_risk_score, reverse=True)
    hotspots = all_nodes[:3]

    return HierarchyRiskResponse(
        manager=root,
        total_downstream_employees=len(all_sub_ids),
        highest_risk_path=risk_path,
        risk_hotspots=hotspots,
    )
