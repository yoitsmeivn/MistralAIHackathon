# pyright: basic, reportMissingImports=false
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.auth.middleware import OptionalUser
from app.db import queries
from app.models.api import CallerListItem

router = APIRouter(prefix="/api/callers", tags=["callers"])


class CreateCallerRequest(BaseModel):
    persona_name: str
    persona_role: str = ""
    persona_company: str = ""
    phone_number: str = ""
    voice_profile: dict[str, Any] | None = None
    org_id: str | None = None


class UpdateCallerRequest(BaseModel):
    persona_name: str | None = None
    persona_role: str | None = None
    persona_company: str | None = None
    phone_number: str | None = None
    voice_profile: dict[str, Any] | None = None


@router.patch("/{caller_id}")
async def api_update_caller(caller_id: str, req: UpdateCallerRequest, user: OptionalUser) -> dict:
    caller = queries.get_caller(caller_id)
    if not caller:
        raise HTTPException(status_code=404, detail="Caller not found")
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        return caller
    return queries.update_caller(caller_id, updates)


@router.post("/")
async def api_create_caller(req: CreateCallerRequest, user: OptionalUser) -> dict:
    resolved_org_id = user["org_id"] if user else req.org_id
    if not resolved_org_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    data = req.model_dump(exclude={"org_id"})
    data["org_id"] = resolved_org_id
    return queries.create_caller(data)


@router.delete("/{caller_id}")
async def api_delete_caller(caller_id: str, user: OptionalUser) -> dict:
    caller = queries.get_caller(caller_id)
    if not caller:
        raise HTTPException(status_code=404, detail="Caller not found")
    queries.update_caller(caller_id, {"is_active": False})
    return {"status": "deleted"}


@router.get("/", response_model=list[CallerListItem])
async def api_list_callers(
    user: OptionalUser,
    org_id: str | None = Query(None),
) -> list[CallerListItem]:
    resolved_org_id = user["org_id"] if user else org_id
    if not resolved_org_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    callers = queries.list_callers(resolved_org_id, active_only=False)
    all_calls = queries.list_calls(org_id=resolved_org_id, limit=10000)

    # Build per-caller aggregates
    caller_calls: dict[str, list[dict]] = {}
    for c in all_calls:
        cid = c.get("caller_id")
        if cid:
            caller_calls.setdefault(cid, []).append(c)

    items: list[CallerListItem] = []
    for caller in callers:
        cid = caller["id"]
        calls = caller_calls.get(cid, [])
        completed = [c for c in calls if c.get("status") == "completed"]
        failed = [c for c in completed if c.get("employee_compliance") == "failed"]
        success_rate = (
            round(len(failed) / len(completed) * 100) if completed else 0
        )

        items.append(
            CallerListItem(
                id=cid,
                persona_name=caller.get("persona_name", ""),
                persona_role=caller.get("persona_role", ""),
                persona_company=caller.get("persona_company", ""),
                phone_number=caller.get("phone_number", ""),
                voice_profile=caller.get("voice_profile") or {},
                is_active=caller.get("is_active") if caller.get("is_active") is not None else True,
                total_calls=len(calls),
                avg_success_rate=success_rate,
                created_at=caller.get("created_at", ""),
            )
        )
    return items
