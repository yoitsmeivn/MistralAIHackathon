# pyright: basic, reportMissingImports=false
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.db import queries
from app.models.api import CallDetail, CallListItem, StartCallRequest, StartCallResponse
from app.models.calls import Call
from app.services.calls import start_call as svc_start_call

router = APIRouter(prefix="/api/calls", tags=["calls"])


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


@router.get("/", response_model=list[CallListItem])
async def api_list_calls(
    org_id: str = Query(...),
    employee_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
) -> list[CallListItem]:
    raw_calls = queries.list_calls(
        org_id=org_id, employee_id=employee_id, status=status, limit=limit
    )
    items: list[CallListItem] = []
    for call_row in raw_calls:
        items.append(
            CallListItem(
                id=call_row["id"],
                employee_id=call_row["employee_id"],
                status=call_row["status"],
                risk_score=call_row.get("risk_score"),
                employee_compliance=call_row.get("employee_compliance"),
                started_at=call_row.get("started_at"),
            )
        )
    return items


@router.get("/{call_id}", response_model=CallDetail)
async def api_call_detail(call_id: str) -> CallDetail:
    call_data = queries.get_call(call_id)
    if not call_data:
        raise HTTPException(status_code=404, detail="Call not found")

    return CallDetail(call=Call(**call_data))
