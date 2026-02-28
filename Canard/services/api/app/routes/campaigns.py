# pyright: basic, reportMissingImports=false
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.campaigns import create_campaign, get_campaign, list_campaigns

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


class CreateCampaignRequest(BaseModel):
    name: str
    scenario_id: str
    created_by: str | None = None


@router.post("/")
async def api_create_campaign(req: CreateCampaignRequest) -> dict:
    return create_campaign(
        name=req.name, scenario_id=req.scenario_id, created_by=req.created_by
    )


@router.get("/")
async def api_list_campaigns() -> list[dict]:
    return list_campaigns()


@router.get("/{campaign_id}")
async def api_get_campaign(campaign_id: str) -> dict:
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign
