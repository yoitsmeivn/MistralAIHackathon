# pyright: basic, reportMissingImports=false
from __future__ import annotations

from fastapi import APIRouter, Query

from app.db import queries

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


@router.get("/")
async def api_list_scripts(org_id: str = Query(...)) -> list[dict]:
    return queries.list_scripts(org_id, active_only=False)
