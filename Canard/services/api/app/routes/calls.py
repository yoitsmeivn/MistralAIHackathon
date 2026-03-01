# pyright: basic, reportMissingImports=false
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.auth.middleware import OptionalUser
from app.db import queries
from app.models.api import CallEnriched, StartCallRequest, StartCallResponse
from app.services.calls import start_call as svc_start_call

router = APIRouter(prefix="/api/calls", tags=["calls"])


def _format_duration(seconds: int | None) -> str:
    if not seconds:
        return ""
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


@router.post("/start", response_model=StartCallResponse)
async def api_start_call(req: StartCallRequest) -> StartCallResponse:
    try:
        call = await svc_start_call(
            employee_id=req.employee_id,
            script_id=req.script_id,
            caller_id=req.caller_id,
            campaign_id=req.campaign_id,
            assignment_id=req.assignment_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return StartCallResponse(
        call_id=call["id"],
        status=call.get("status", "pending"),
    )


@router.get("/", response_model=list[CallEnriched])
async def api_list_calls(
    user: OptionalUser,
    org_id: str | None = Query(None),
    campaign_id: str | None = Query(None),
    employee_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
) -> list[CallEnriched]:
    resolved_org_id = user["org_id"] if user else org_id
    if not resolved_org_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    raw_calls = queries.list_calls(
        org_id=resolved_org_id,
        employee_id=employee_id,
        campaign_id=campaign_id,
        status=status,
        limit=limit,
    )

    # Build lookup dicts for names
    employees = queries.list_employees(resolved_org_id, active_only=False)
    callers = queries.list_callers(resolved_org_id, active_only=False)
    campaigns = queries.list_campaigns(resolved_org_id)

    emp_names = {e["id"]: e.get("full_name", "") for e in employees}
    caller_names = {c["id"]: c.get("persona_name", "") for c in callers}
    campaign_names = {c["id"]: c.get("name", "") for c in campaigns}

    items: list[CallEnriched] = []
    for c in raw_calls:
        flags = c.get("flags") or []
        if isinstance(flags, str):
            flags = [flags]

        items.append(
            CallEnriched(
                id=c["id"],
                employee_name=emp_names.get(c.get("employee_id", ""), ""),
                caller_name=caller_names.get(c.get("caller_id", ""), ""),
                campaign_name=campaign_names.get(c.get("campaign_id", ""), ""),
                status=c.get("status", "pending"),
                started_at=c.get("started_at", "") or "",
                duration=_format_duration(c.get("duration_seconds")),
                duration_seconds=c.get("duration_seconds"),
                risk_score=c.get("risk_score") or 0,
                employee_compliance=c.get("employee_compliance", ""),
                transcript=c.get("transcript", "") or "",
                flags=flags,
                ai_summary=c.get("ai_summary", "") or "",
            )
        )
    return items


@router.get("/{call_id}", response_model=CallEnriched)
async def api_call_detail(call_id: str) -> CallEnriched:
    c = queries.get_call(call_id)
    if not c:
        raise HTTPException(status_code=404, detail="Call not found")

    # Resolve names
    emp = queries.get_employee(c.get("employee_id", ""))
    caller = queries.get_caller(c.get("caller_id", ""))
    campaign = queries.get_campaign(c.get("campaign_id", ""))

    flags = c.get("flags") or []
    if isinstance(flags, str):
        flags = [flags]

    return CallEnriched(
        id=c["id"],
        employee_name=emp.get("full_name", "") if emp else "",
        caller_name=caller.get("persona_name", "") if caller else "",
        campaign_name=campaign.get("name", "") if campaign else "",
        status=c.get("status", "pending"),
        started_at=c.get("started_at", "") or "",
        duration=_format_duration(c.get("duration_seconds")),
        duration_seconds=c.get("duration_seconds"),
        risk_score=c.get("risk_score") or 0,
        employee_compliance=c.get("employee_compliance", ""),
        transcript=c.get("transcript", "") or "",
        flags=flags,
        ai_summary=c.get("ai_summary", "") or "",
    )
