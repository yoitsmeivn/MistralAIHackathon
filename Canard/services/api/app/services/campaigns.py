# pyright: basic
from __future__ import annotations

from app.db import queries


def create_campaign(
    name: str,
    org_id: str,
    created_by: str | None = None,
    description: str | None = None,
    attack_vector: str | None = None,
) -> dict:
    data: dict[str, str] = {"name": name, "org_id": org_id}
    if created_by:
        data["created_by"] = created_by
    if description:
        data["description"] = description
    if attack_vector:
        data["attack_vector"] = attack_vector
    return queries.create_campaign(data)


def get_campaign(campaign_id: str) -> dict | None:
    return queries.get_campaign(campaign_id)


def list_campaigns(org_id: str) -> list[dict]:
    return queries.list_campaigns(org_id)
