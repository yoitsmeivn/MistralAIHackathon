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


def create_participant(data: dict) -> dict:
    result = _execute(
        get_supabase().table("participants").insert(data), "create_participant"
    )
    row = _first_or_none(result)
    return row or {}


def get_participant(id: str) -> dict | None:
    result = _execute(
        get_supabase().table("participants").select("*").eq("id", id).limit(1),
        "get_participant",
    )
    return _first_or_none(result)


def list_participants(active_only: bool = True) -> list[dict]:
    query = (
        get_supabase().table("participants").select("*").order("created_at", desc=True)
    )
    if active_only:
        query = query.eq("active", True)
    result = _execute(query, "list_participants")
    return result if isinstance(result, list) else []


def create_scenario(data: dict) -> dict:
    result = _execute(get_supabase().table("scenarios").insert(data), "create_scenario")
    row = _first_or_none(result)
    return row or {}


def get_scenario(id: str) -> dict | None:
    result = _execute(
        get_supabase().table("scenarios").select("*").eq("id", id).limit(1),
        "get_scenario",
    )
    return _first_or_none(result)


def list_scenarios() -> list[dict]:
    result = _execute(
        get_supabase().table("scenarios").select("*").order("created_at", desc=True),
        "list_scenarios",
    )
    return result if isinstance(result, list) else []


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


def get_call_by_sid(twilio_call_sid: str) -> dict | None:
    result = _execute(
        get_supabase()
        .table("calls")
        .select("*")
        .eq("twilio_call_sid", twilio_call_sid)
        .limit(1),
        "get_call_by_sid",
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
    participant_id: str | None,
    status: str | None,
    limit: int = 50,
) -> list[dict]:
    query = (
        get_supabase()
        .table("calls")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
    )
    if participant_id:
        query = query.eq("participant_id", participant_id)
    if status:
        query = query.eq("status", status)
    result = _execute(query, "list_calls")
    return result if isinstance(result, list) else []


def create_turn(data: dict) -> dict:
    result = _execute(get_supabase().table("turns").insert(data), "create_turn")
    row = _first_or_none(result)
    return row or {}


def get_turns_for_call(call_id: str) -> list[dict]:
    result = _execute(
        get_supabase()
        .table("turns")
        .select("*")
        .eq("call_id", call_id)
        .order("turn_index"),
        "get_turns_for_call",
    )
    return result if isinstance(result, list) else []


def create_analysis(data: dict) -> dict:
    result = _execute(get_supabase().table("analysis").insert(data), "create_analysis")
    row = _first_or_none(result)
    return row or {}


def get_analysis_for_call(call_id: str) -> dict | None:
    result = _execute(
        get_supabase().table("analysis").select("*").eq("call_id", call_id).limit(1),
        "get_analysis_for_call",
    )
    return _first_or_none(result)
