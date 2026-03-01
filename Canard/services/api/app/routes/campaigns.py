# pyright: basic, reportMissingImports=false
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.auth.middleware import OptionalUser
from app.db import queries
from app.models.api import CampaignListItem, ScriptListItem

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


class CreateCampaignRequest(BaseModel):
    name: str
    org_id: str | None = None
    created_by: str | None = None
    description: str | None = None
    attack_vector: str | None = None


def _enrich_campaigns(campaigns: list[dict], all_calls: list[dict]) -> list[CampaignListItem]:
    """Add computed totalCalls, completedCalls, avgRiskScore from calls data."""
    camp_calls: dict[str, list[dict]] = {}
    for c in all_calls:
        cid = c.get("campaign_id")
        if cid:
            camp_calls.setdefault(cid, []).append(c)

    items: list[CampaignListItem] = []
    for camp in campaigns:
        cid = camp["id"]
        calls = camp_calls.get(cid, [])
        completed = [c for c in calls if c.get("status") == "completed"]
        scores = [c.get("risk_score", 0) or 0 for c in completed]
        avg_risk = round(sum(scores) / len(scores)) if scores else 0

        items.append(
            CampaignListItem(
                id=cid,
                name=camp.get("name", ""),
                description=camp.get("description", ""),
                attack_vector=camp.get("attack_vector", ""),
                status=camp.get("status", "draft"),
                scheduled_at=camp.get("scheduled_at"),
                started_at=camp.get("started_at"),
                completed_at=camp.get("completed_at"),
                total_calls=len(calls),
                completed_calls=len(completed),
                avg_risk_score=avg_risk,
                created_at=camp.get("created_at", ""),
            )
        )
    return items


@router.post("/")
async def api_create_campaign(req: CreateCampaignRequest, user: OptionalUser) -> dict:
    from app.services.campaigns import create_campaign

    resolved_org_id = user["org_id"] if user else req.org_id
    if not resolved_org_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    return create_campaign(
        name=req.name,
        org_id=resolved_org_id,
        created_by=req.created_by or (user["id"] if user else None),
        description=req.description,
        attack_vector=req.attack_vector,
    )


@router.get("/", response_model=list[CampaignListItem])
async def api_list_campaigns(
    user: OptionalUser,
    org_id: str | None = Query(None),
) -> list[CampaignListItem]:
    resolved_org_id = user["org_id"] if user else org_id
    if not resolved_org_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    campaigns = queries.list_campaigns(resolved_org_id)
    all_calls = queries.list_calls(org_id=resolved_org_id, limit=10000)
    return _enrich_campaigns(campaigns, all_calls)


class UpdateCampaignRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    attack_vector: str | None = None
    status: str | None = None
    scheduled_at: str | None = None


@router.patch("/{campaign_id}")
async def api_update_campaign(
    campaign_id: str, req: UpdateCampaignRequest, user: OptionalUser
) -> dict:
    campaign = queries.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    updates = req.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    return queries.update_campaign(campaign_id, updates)


@router.delete("/{campaign_id}")
async def api_delete_campaign(campaign_id: str, user: OptionalUser) -> dict:
    campaign = queries.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    queries.delete_campaign(campaign_id)
    return {"status": "deleted"}


class LaunchCampaignRequest(BaseModel):
    script_id: str | None = None
    caller_id: str | None = None
    department: str | None = None
    employee_ids: list[str] | None = None


@router.get("/{campaign_id}/scripts", response_model=list[ScriptListItem])
async def api_get_campaign_scripts(campaign_id: str) -> list[ScriptListItem]:
    campaign = queries.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    camp_name = campaign.get("name", "")
    rows = queries.list_scripts_by_campaign(campaign_id)
    return [
        ScriptListItem(
            id=s["id"],
            name=s.get("name", ""),
            campaign_id=campaign_id,
            campaign_name=camp_name,
            attack_type=s.get("attack_type", ""),
            difficulty=s.get("difficulty", "medium"),
            system_prompt=s.get("system_prompt", ""),
            objectives=s.get("objectives", []),
            escalation_steps=s.get("escalation_steps", []),
            description=s.get("description", ""),
            is_active=s.get("is_active", True),
            created_at=s.get("created_at", ""),
        )
        for s in rows
    ]


@router.post("/{campaign_id}/launch")
async def api_launch_campaign(
    campaign_id: str, req: LaunchCampaignRequest, user: OptionalUser
) -> dict:
    from app.services.campaigns import launch_campaign

    try:
        return await launch_campaign(
            campaign_id=campaign_id,
            script_id=req.script_id,
            caller_id=req.caller_id,
            department=req.department,
            employee_ids=req.employee_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{campaign_id}", response_model=CampaignListItem)
async def api_get_campaign(campaign_id: str) -> CampaignListItem:
    campaign = queries.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    org_id = campaign.get("org_id", "")
    all_calls = queries.list_calls(org_id=org_id, campaign_id=campaign_id, limit=10000)
    enriched = _enrich_campaigns([campaign], all_calls)
    return enriched[0]
