# pyright: basic
from __future__ import annotations

from typing import Any

from app.db.client import get_supabase


def _first_or_none(data: Any) -> dict[str, Any] | None:
    if isinstance(data, list):
        if not data:
            return None
        first = data[0]
        return first if isinstance(first, dict) else None
    return data if isinstance(data, dict) else None


def _execute(query: Any, context: str) -> Any:
    try:
        response = query.execute()
        return response.data
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Database query failed during {context}") from exc


# ── Organizations ──


def create_organization(data: dict) -> dict:
    result = _execute(
        get_supabase().table("organizations").insert(data), "create_organization"
    )
    row = _first_or_none(result)
    return row or {}


def get_organization(id: str) -> dict | None:
    result = _execute(
        get_supabase().table("organizations").select("*").eq("id", id).limit(1),
        "get_organization",
    )
    return _first_or_none(result)


def get_organization_by_slug(slug: str) -> dict | None:
    result = _execute(
        get_supabase().table("organizations").select("*").eq("slug", slug).limit(1),
        "get_organization_by_slug",
    )
    return _first_or_none(result)


# ── Users ──


def create_user(data: dict) -> dict:
    result = _execute(get_supabase().table("users").insert(data), "create_user")
    row = _first_or_none(result)
    return row or {}


def get_user(id: str) -> dict | None:
    result = _execute(
        get_supabase().table("users").select("*").eq("id", id).limit(1),
        "get_user",
    )
    return _first_or_none(result)


def get_user_by_email(email: str) -> dict | None:
    result = _execute(
        get_supabase().table("users").select("*").eq("email", email).limit(1),
        "get_user_by_email",
    )
    return _first_or_none(result)


def list_users(org_id: str, active_only: bool = True) -> list[dict]:
    query = (
        get_supabase()
        .table("users")
        .select("*")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
    )
    if active_only:
        query = query.eq("is_active", True)
    result = _execute(query, "list_users")
    return result if isinstance(result, list) else []


# ── Employees ──


def create_employee(data: dict) -> dict:
    result = _execute(
        get_supabase().table("employees").insert(data), "create_employee"
    )
    row = _first_or_none(result)
    return row or {}


def get_employee(id: str) -> dict | None:
    result = _execute(
        get_supabase().table("employees").select("*").eq("id", id).limit(1),
        "get_employee",
    )
    return _first_or_none(result)


def list_employees(org_id: str, active_only: bool = True) -> list[dict]:
    query = (
        get_supabase()
        .table("employees")
        .select("*")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
    )
    if active_only:
        query = query.eq("is_active", True)
    result = _execute(query, "list_employees")
    return result if isinstance(result, list) else []


def update_employee(id: str, data: dict) -> dict:
    result = _execute(
        get_supabase().table("employees").update(data).eq("id", id),
        "update_employee",
    )
    row = _first_or_none(result)
    return row or {}


# ── Callers ──


def create_caller(data: dict) -> dict:
    result = _execute(get_supabase().table("callers").insert(data), "create_caller")
    row = _first_or_none(result)
    return row or {}


def get_caller(id: str) -> dict | None:
    result = _execute(
        get_supabase().table("callers").select("*").eq("id", id).limit(1),
        "get_caller",
    )
    return _first_or_none(result)


def list_callers(org_id: str, active_only: bool = True) -> list[dict]:
    query = (
        get_supabase()
        .table("callers")
        .select("*")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
    )
    if active_only:
        query = query.eq("is_active", True)
    result = _execute(query, "list_callers")
    return result if isinstance(result, list) else []


# ── Scripts ──


def create_script(data: dict) -> dict:
    result = _execute(get_supabase().table("scripts").insert(data), "create_script")
    row = _first_or_none(result)
    return row or {}


def get_script(id: str) -> dict | None:
    result = _execute(
        get_supabase().table("scripts").select("*").eq("id", id).limit(1),
        "get_script",
    )
    return _first_or_none(result)


def list_scripts(org_id: str, active_only: bool = True) -> list[dict]:
    query = (
        get_supabase()
        .table("scripts")
        .select("*")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
    )
    if active_only:
        query = query.eq("is_active", True)
    result = _execute(query, "list_scripts")
    return result if isinstance(result, list) else []


# ── Campaigns ──


def create_campaign(data: dict) -> dict:
    result = _execute(get_supabase().table("campaigns").insert(data), "create_campaign")
    row = _first_or_none(result)
    return row or {}


def get_campaign(id: str) -> dict | None:
    result = _execute(
        get_supabase().table("campaigns").select("*").eq("id", id).limit(1),
        "get_campaign",
    )
    return _first_or_none(result)


def list_campaigns(org_id: str) -> list[dict]:
    result = _execute(
        get_supabase()
        .table("campaigns")
        .select("*")
        .eq("org_id", org_id)
        .order("created_at", desc=True),
        "list_campaigns",
    )
    return result if isinstance(result, list) else []


def update_campaign(id: str, data: dict) -> dict:
    result = _execute(
        get_supabase().table("campaigns").update(data).eq("id", id),
        "update_campaign",
    )
    row = _first_or_none(result)
    return row or {}


# ── Campaign Assignments ──


def create_campaign_assignment(data: dict) -> dict:
    result = _execute(
        get_supabase().table("campaign_assignments").insert(data),
        "create_campaign_assignment",
    )
    row = _first_or_none(result)
    return row or {}


def list_campaign_assignments(campaign_id: str) -> list[dict]:
    result = _execute(
        get_supabase()
        .table("campaign_assignments")
        .select("*")
        .eq("campaign_id", campaign_id)
        .order("created_at", desc=True),
        "list_campaign_assignments",
    )
    return result if isinstance(result, list) else []


def update_campaign_assignment(id: str, data: dict) -> dict:
    result = _execute(
        get_supabase().table("campaign_assignments").update(data).eq("id", id),
        "update_campaign_assignment",
    )
    row = _first_or_none(result)
    return row or {}


# ── Calls ──


def create_call(data: dict) -> dict:
    result = _execute(get_supabase().table("calls").insert(data), "create_call")
    row = _first_or_none(result)
    return row or {}


def get_call(id: str) -> dict | None:
    result = _execute(
        get_supabase().table("calls").select("*").eq("id", id).limit(1),
        "get_call",
    )
    return _first_or_none(result)


def update_call(id: str, data: dict) -> dict:
    result = _execute(
        get_supabase().table("calls").update(data).eq("id", id),
        "update_call",
    )
    row = _first_or_none(result)
    return row or {}


def list_calls(
    org_id: str,
    employee_id: str | None = None,
    campaign_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict]:
    query = (
        get_supabase()
        .table("calls")
        .select("*")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
        .limit(limit)
    )
    if employee_id:
        query = query.eq("employee_id", employee_id)
    if campaign_id:
        query = query.eq("campaign_id", campaign_id)
    if status:
        query = query.eq("status", status)
    result = _execute(query, "list_calls")
    return result if isinstance(result, list) else []


def get_subordinates(manager_id: str) -> list[dict]:
    """Return all direct + transitive reports via the recursive RPC."""
    try:
        response = get_supabase().rpc(
            "get_subordinates", {"manager_uuid": manager_id}
        ).execute()
        return response.data if isinstance(response.data, list) else []
    except Exception:  # noqa: BLE001
        return []


def get_call_by_sid(twilio_call_sid: str) -> dict | None:
    """Look up a call by its Twilio CallSid."""
    result = _execute(
        get_supabase()
        .table("calls")
        .select("*")
        .eq("twilio_call_sid", twilio_call_sid)
        .limit(1),
        "get_call_by_sid",
    )
    return _first_or_none(result)
