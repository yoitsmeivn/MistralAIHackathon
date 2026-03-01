# pyright: basic, reportMissingImports=false
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.auth.middleware import OptionalUser
from app.db import queries
from app.models.api import ScriptListItem

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


class CreateScriptRequest(BaseModel):
    name: str
    campaign_id: str | None = None
    attack_type: str = ""
    difficulty: str = "medium"
    objectives: list[str] = []
    escalation_steps: list[str] = []
    description: str = ""
    org_id: str | None = None


class UpdateScriptRequest(BaseModel):
    name: str | None = None
    campaign_id: str | None = None
    attack_type: str | None = None
    difficulty: str | None = None
    objectives: list[str] | None = None
    escalation_steps: list[str] | None = None
    description: str | None = None


@router.post("/")
async def api_create_script(req: CreateScriptRequest, user: OptionalUser) -> dict:
    resolved_org_id = user["org_id"] if user else req.org_id
    if not resolved_org_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    data = req.model_dump(exclude={"org_id"})
    data["org_id"] = resolved_org_id
    if user:
        data["created_by"] = user["id"]
    return queries.create_script(data)


@router.get("/", response_model=list[ScriptListItem])
async def api_list_scripts(
    user: OptionalUser,
    org_id: str | None = Query(None),
) -> list[ScriptListItem]:
    resolved_org_id = user["org_id"] if user else org_id
    if not resolved_org_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    rows = queries.list_scripts(resolved_org_id, active_only=False)

    # Build campaign name lookup
    campaigns = queries.list_campaigns(resolved_org_id)
    camp_names: dict[str, str] = {c["id"]: c.get("name", "") for c in campaigns}

    return [
        ScriptListItem(**r, campaign_name=camp_names.get(r.get("campaign_id", ""), None))
        for r in rows
    ]


@router.get("/{script_id}", response_model=ScriptListItem)
async def api_get_script(script_id: str, user: OptionalUser) -> ScriptListItem:
    script = queries.get_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return ScriptListItem(**script)


@router.patch("/{script_id}")
async def api_update_script(
    script_id: str, req: UpdateScriptRequest, user: OptionalUser
) -> dict:
    script = queries.get_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    updates = req.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    return queries.update_script(script_id, updates)


@router.delete("/{script_id}")
async def api_delete_script(script_id: str, user: OptionalUser) -> dict:
    script = queries.get_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    queries.update_script(script_id, {"is_active": False})
    return {"status": "deleted"}
