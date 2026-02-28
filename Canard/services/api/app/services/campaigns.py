# pyright: basic
from __future__ import annotations

from app.db import queries


def create_campaign(name: str, scenario_id: str, created_by: str | None = None) -> dict:
    data = {"name": name, "scenario_id": scenario_id}
    if created_by:
        data["created_by"] = created_by
    return queries.create_campaign(data)


def get_campaign(campaign_id: str) -> dict | None:
    return queries.get_campaign(campaign_id)


def list_campaigns() -> list[dict]:
    from app.db.client import get_supabase

    try:
        result = (
            get_supabase()
            .table("campaigns")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data if isinstance(result.data, list) else []
    except Exception:
        return []
