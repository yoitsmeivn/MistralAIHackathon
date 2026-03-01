# pyright: basic, reportMissingImports=false
from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request

from app.db.client import get_supabase
from app.db import queries


async def _extract_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:]
    return None


def _verify_and_resolve(token: str) -> dict[str, Any]:
    """Verify JWT via Supabase GoTrue and resolve the public.users record."""
    sb = get_supabase()
    try:
        auth_response = sb.auth.get_user(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    if not auth_response or not auth_response.user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    email = auth_response.user.email
    if not email:
        raise HTTPException(status_code=401, detail="Auth user has no email")

    user = queries.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found in application database")

    return user


async def get_current_user(request: Request) -> dict[str, Any]:
    """Require a valid JWT. Returns the public.users row as a dict."""
    token = await _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    return _verify_and_resolve(token)


async def get_current_user_optional(request: Request) -> dict[str, Any] | None:
    """Return authenticated user if token present, else None (for backward compat)."""
    token = await _extract_token(request)
    if not token:
        return None
    try:
        return _verify_and_resolve(token)
    except HTTPException:
        return None


CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
OptionalUser = Annotated[dict[str, Any] | None, Depends(get_current_user_optional)]
