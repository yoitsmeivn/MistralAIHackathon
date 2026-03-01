# pyright: basic, reportMissingImports=false
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.auth.middleware import OptionalUser
from app.db import queries
from app.models.api import CallerListItem

router = APIRouter(prefix="/api/callers", tags=["callers"])


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
                attack_type=caller.get("attack_type", ""),
                description=caller.get("description", ""),
                is_active=caller.get("is_active") if caller.get("is_active") is not None else True,
                total_calls=len(calls),
                avg_success_rate=success_rate,
            )
        )
    return items
