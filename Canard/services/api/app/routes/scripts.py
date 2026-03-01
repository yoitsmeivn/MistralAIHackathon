# pyright: basic, reportMissingImports=false
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.auth.middleware import OptionalUser
from app.db import queries

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


@router.get("/")
async def api_list_scripts(
    user: OptionalUser,
    org_id: str | None = Query(None),
) -> list[dict]:
    resolved_org_id = user["org_id"] if user else org_id
    if not resolved_org_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    return queries.list_scripts(resolved_org_id, active_only=False)
