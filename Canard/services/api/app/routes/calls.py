# pyright: basic, reportMissingImports=false
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.db import queries
from app.models.analysis import Analysis
from app.models.api import CallDetail, CallListItem, StartCallRequest, StartCallResponse
from app.models.calls import Call
from app.models.turns import Turn
from app.services.calls import start_call as svc_start_call

router = APIRouter(prefix="/api/calls", tags=["calls"])


@router.post("/start", response_model=StartCallResponse)
async def api_start_call(req: StartCallRequest) -> StartCallResponse:
    try:
        call = await svc_start_call(
            participant_id=req.participant_id,
            scenario_id=req.scenario_id,
            campaign_id=req.campaign_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return StartCallResponse(
        call_id=call["id"],
        twilio_call_sid=call.get("twilio_call_sid", ""),
        status=call.get("status", "pending"),
    )


@router.get("/", response_model=list[CallListItem])
async def api_list_calls(
    participant_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
) -> list[CallListItem]:
    raw_calls = queries.list_calls(
        participant_id=participant_id, status=status, limit=limit
    )
    items: list[CallListItem] = []
    for call_row in raw_calls:
        analysis = queries.get_analysis_for_call(call_row["id"])
        items.append(
            CallListItem(
                id=call_row["id"],
                participant_id=call_row["participant_id"],
                participant_name=None,
                scenario_name=None,
                status=call_row["status"],
                consented=call_row.get("consented", False),
                risk_score=analysis["risk_score"] if analysis else None,
                started_at=call_row.get("started_at"),
            )
        )
    return items


@router.get("/{call_id}", response_model=CallDetail)
async def api_call_detail(call_id: str) -> CallDetail:
    call_data = queries.get_call(call_id)
    if not call_data:
        raise HTTPException(status_code=404, detail="Call not found")

    turns_data = queries.get_turns_for_call(call_id)
    analysis_data = queries.get_analysis_for_call(call_id)

    return CallDetail(
        call=Call(**call_data),
        turns=[Turn(**turn) for turn in turns_data],
        analysis=Analysis(**analysis_data) if analysis_data else None,
    )
