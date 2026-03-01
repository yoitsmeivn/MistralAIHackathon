# pyright: basic, reportMissingImports=false
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.db.client import get_supabase
from app.db import queries
from app.auth.middleware import CurrentUser
from app.auth.domain import extract_domain, validate_corporate_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Request Models ──


class RegisterOrgRequest(BaseModel):
    company_name: str
    industry: str
    email: EmailStr
    password: str
    full_name: str


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class TransferAdminRequest(BaseModel):
    target_user_id: str


# ── Helpers ──


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug


def _require_admin(user: dict) -> None:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")


# ── Routes ──


@router.post("/register-org")
async def register_org(req: RegisterOrgRequest) -> dict:
    """Create a Supabase auth user + organization + public.users record (admin)."""
    # Validate corporate email
    validate_corporate_email(req.email)

    # Check no org already exists with this domain
    domain = extract_domain(req.email)
    existing = queries.get_organization_by_domain(domain)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"An organization is already registered for the domain '{domain}'",
        )

    sb = get_supabase()

    # 1. Create Supabase auth user (service_role auto-confirms)
    try:
        auth_resp = sb.auth.admin.create_user(
            {
                "email": req.email,
                "password": req.password,
                "email_confirm": True,
            }
        )
    except Exception as exc:
        detail = str(exc)
        if "already" in detail.lower() or "duplicate" in detail.lower():
            raise HTTPException(status_code=409, detail="Email already registered") from exc
        raise HTTPException(status_code=400, detail=f"Failed to create auth user: {detail}") from exc

    auth_user = auth_resp.user
    if not auth_user:
        raise HTTPException(status_code=500, detail="Auth user creation returned no user")

    # 2. Create organization with domain
    slug = _slugify(req.company_name)
    org = queries.create_organization(
        {
            "name": req.company_name,
            "slug": slug,
            "industry": req.industry,
            "domain": domain,
        }
    )
    if not org or not org.get("id"):
        raise HTTPException(status_code=500, detail="Failed to create organization")

    # 3. Create public.users record linked to org (use Supabase auth UUID as id)
    user = queries.create_user(
        {
            "id": str(auth_user.id),
            "org_id": org["id"],
            "email": req.email,
            "password_hash": "managed_by_supabase",
            "full_name": req.full_name,
            "role": "admin",
            "is_active": True,
        }
    )

    return {
        "user_id": user.get("id"),
        "org_id": org["id"],
        "org_slug": slug,
        "email": req.email,
    }


@router.get("/me")
async def get_me(user: CurrentUser) -> dict:
    """Return current user profile + org info."""
    org = queries.get_organization(user["org_id"]) if user.get("org_id") else None
    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "full_name": user.get("full_name"),
        "role": user.get("role"),
        "org_id": user.get("org_id"),
        "org_name": org.get("name") if org else None,
        "org_slug": org.get("slug") if org else None,
    }


@router.get("/users")
async def list_org_users(user: CurrentUser) -> list[dict]:
    """Return all users in the current org."""
    org_id = user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User has no organization")
    users = queries.list_users(org_id, active_only=False)
    return [
        {
            "id": u.get("id"),
            "email": u.get("email"),
            "full_name": u.get("full_name"),
            "role": u.get("role"),
            "is_active": u.get("is_active"),
            "created_at": u.get("created_at"),
        }
        for u in users
    ]


@router.post("/users")
async def create_org_user(req: CreateUserRequest, user: CurrentUser) -> dict:
    """Admin-only: create a manager in the current org."""
    _require_admin(user)

    org_id = user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User has no organization")

    # Validate new user's domain matches org domain
    org = queries.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=500, detail="Organization not found")

    org_domain = org.get("domain")
    new_user_domain = extract_domain(req.email)
    if org_domain and new_user_domain != org_domain:
        raise HTTPException(
            status_code=400,
            detail=f"Email domain must match your organization's domain ({org_domain})",
        )

    sb = get_supabase()

    # Create Supabase auth user
    try:
        auth_resp = sb.auth.admin.create_user(
            {
                "email": req.email,
                "password": req.password,
                "email_confirm": True,
            }
        )
    except Exception as exc:
        detail = str(exc)
        if "already" in detail.lower() or "duplicate" in detail.lower():
            raise HTTPException(status_code=409, detail="Email already registered") from exc
        raise HTTPException(status_code=400, detail=f"Failed to create auth user: {detail}") from exc

    auth_user = auth_resp.user
    if not auth_user:
        raise HTTPException(status_code=500, detail="Auth user creation returned no user")

    # Create public.users record
    new_user = queries.create_user(
        {
            "id": str(auth_user.id),
            "org_id": org_id,
            "email": req.email,
            "password_hash": "managed_by_supabase",
            "full_name": req.full_name,
            "role": "manager",
            "is_active": True,
        }
    )

    return {
        "id": new_user.get("id"),
        "email": new_user.get("email"),
        "full_name": new_user.get("full_name"),
        "role": new_user.get("role"),
        "org_id": org_id,
    }


@router.post("/transfer-admin")
async def transfer_admin(req: TransferAdminRequest, user: CurrentUser) -> dict:
    """Admin-only: transfer admin role to another user in the same org."""
    _require_admin(user)

    target = queries.get_user(req.target_user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target user not found")
    if target.get("org_id") != user.get("org_id"):
        raise HTTPException(status_code=400, detail="Target user is not in your organization")
    if not target.get("is_active"):
        raise HTTPException(status_code=400, detail="Target user is not active")
    if target.get("id") == user.get("id"):
        raise HTTPException(status_code=400, detail="You are already the admin")

    # Demote current admin to manager
    queries.update_user(user["id"], {"role": "manager"})
    # Promote target to admin
    queries.update_user(req.target_user_id, {"role": "admin"})

    return {"message": "Admin role transferred", "new_admin_id": req.target_user_id}


@router.delete("/me")
async def delete_account(user: CurrentUser) -> dict:
    """Delete the current user's account. Admins must transfer role first (unless sole user)."""
    org_id = user.get("org_id")
    user_id = user["id"]
    sb = get_supabase()

    if user.get("role") == "admin" and org_id:
        org_users = queries.list_users(org_id, active_only=True)
        other_users = [u for u in org_users if u.get("id") != user_id]
        if other_users:
            raise HTTPException(
                status_code=400,
                detail="Transfer admin role to another user before deleting your account",
            )
        # Sole user — delete user + org
        queries.delete_user(user_id)
        queries.delete_organization(org_id)
    else:
        # Manager — just delete user record
        queries.delete_user(user_id)

    # Delete Supabase auth user
    try:
        sb.auth.admin.delete_user(user_id)
    except Exception:
        pass  # Best-effort; public.users row is already gone

    return {"message": "Account deleted"}
