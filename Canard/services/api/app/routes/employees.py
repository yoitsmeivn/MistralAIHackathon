# pyright: basic, reportMissingImports=false
from __future__ import annotations

import csv
import io

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel

from app.auth.middleware import CurrentUser, OptionalUser
from app.db import queries
from app.models.api import EmployeeListItem

router = APIRouter(prefix="/api/employees", tags=["employees"])

# ── Column name mapping for flexible CSV headers ──

COLUMN_MAP: dict[str, list[str]] = {
    "full_name": ["full_name", "full name", "name", "employee name"],
    "email": ["email", "work email", "work_email", "email address"],
    "phone": ["phone", "phone number", "work phone", "mobile"],
    "department": ["department", "dept"],
    "job_title": ["job_title", "job title", "title", "role", "position"],
    "manager_email": [
        "manager_email",
        "manager email",
        "reports to",
        "reports_to",
        "supervisor email",
        "manager",
    ],
    "employee_id": ["employee_id", "employee id", "emp_id", "id", "external_id"],
}


def _resolve_columns(headers: list[str]) -> dict[str, str]:
    """Map CSV header names to canonical field names."""
    lower_headers = [h.strip().lower() for h in headers]
    mapping: dict[str, str] = {}
    for field, aliases in COLUMN_MAP.items():
        for alias in aliases:
            if alias in lower_headers:
                idx = lower_headers.index(alias)
                mapping[field] = headers[idx].strip()
                break
    return mapping


# ── Schemas ──


class CreateEmployeeRequest(BaseModel):
    full_name: str
    email: str
    phone: str
    department: str | None = None
    job_title: str | None = None


class ImportResult(BaseModel):
    created: int
    updated: int
    errors: list[str]


# ── GET / ──


@router.get("/", response_model=list[EmployeeListItem])
async def api_list_employees(
    user: OptionalUser,
    org_id: str | None = Query(None),
) -> list[EmployeeListItem]:
    resolved_org_id = user["org_id"] if user else org_id
    if not resolved_org_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    employees = queries.list_employees(resolved_org_id, active_only=False)
    all_calls = queries.list_calls(org_id=resolved_org_id, limit=10000)

    # Build per-employee aggregates
    emp_calls: dict[str, list[dict]] = {}
    for c in all_calls:
        eid = c.get("employee_id")
        if eid:
            emp_calls.setdefault(eid, []).append(c)

    items: list[EmployeeListItem] = []
    for emp in employees:
        eid = emp["id"]
        calls = emp_calls.get(eid, [])
        completed = [c for c in calls if c.get("status") == "completed"]
        failed = [c for c in completed if c.get("employee_compliance") == "failed"]
        last_date = ""
        if completed:
            dates = [c.get("started_at", "") for c in completed if c.get("started_at")]
            if dates:
                last_date = max(dates)[:10]  # YYYY-MM-DD

        items.append(
            EmployeeListItem(
                id=eid,
                full_name=emp.get("full_name", ""),
                email=emp.get("email", ""),
                phone=emp.get("phone", ""),
                department=emp.get("department", ""),
                job_title=emp.get("job_title", ""),
                risk_level=emp.get("risk_level", "unknown"),
                total_tests=len(completed),
                failed_tests=len(failed),
                last_test_date=last_date,
                is_active=emp.get("is_active", True),
                boss_id=emp.get("boss_id"),
            )
        )
    return items


# ── POST / ── single employee creation


@router.post("/")
async def api_create_employee(body: CreateEmployeeRequest, user: CurrentUser) -> dict:
    org_id = user["org_id"]
    data = {
        "org_id": org_id,
        "full_name": body.full_name,
        "email": body.email,
        "phone": body.phone,
        "department": body.department or "",
        "job_title": body.job_title or "",
    }
    existing = queries.get_employee_by_email(body.email, org_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Employee with email {body.email} already exists",
        )
    row = queries.create_employee(data)
    return row


# ── POST /import ── CSV bulk import


@router.post("/import", response_model=ImportResult)
async def api_import_csv(user: CurrentUser, file: UploadFile = File(...)) -> ImportResult:
    org_id = user["org_id"]

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file has no headers")

    col_map = _resolve_columns(list(reader.fieldnames))

    if "full_name" not in col_map or "email" not in col_map:
        raise HTTPException(
            status_code=400,
            detail="CSV must contain at least 'full_name' (or 'name') and 'email' columns",
        )

    rows = list(reader)
    created = 0
    updated = 0
    errors: list[str] = []

    # Build existing email→id map for this org
    existing_employees = queries.list_employees(org_id, active_only=False)
    email_to_id: dict[str, str] = {
        e["email"].lower(): e["id"] for e in existing_employees if e.get("email")
    }

    # Pass 1: Create or update employees (without boss_id), collect email→id
    row_results: list[tuple[str, str]] = []  # (email, id) for newly processed rows

    for i, row in enumerate(rows, start=2):  # start=2 because row 1 is header
        try:
            email = row.get(col_map.get("email", ""), "").strip()
            full_name = row.get(col_map.get("full_name", ""), "").strip()

            if not email or not full_name:
                errors.append(f"Row {i}: missing required field (full_name or email)")
                continue

            phone = row.get(col_map.get("phone", ""), "").strip() if "phone" in col_map else ""
            department = row.get(col_map.get("department", ""), "").strip() if "department" in col_map else ""
            job_title = row.get(col_map.get("job_title", ""), "").strip() if "job_title" in col_map else ""

            data = {
                "org_id": org_id,
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "department": department,
                "job_title": job_title,
            }

            existing = queries.get_employee_by_email(email, org_id)
            if existing:
                queries.update_employee(existing["id"], {
                    "full_name": full_name,
                    "phone": phone,
                    "department": department,
                    "job_title": job_title,
                })
                email_to_id[email.lower()] = existing["id"]
                row_results.append((email.lower(), existing["id"]))
                updated += 1
            else:
                new_emp = queries.create_employee(data)
                emp_id = new_emp["id"]
                email_to_id[email.lower()] = emp_id
                row_results.append((email.lower(), emp_id))
                created += 1

        except Exception as exc:  # noqa: BLE001
            errors.append(f"Row {i}: {exc}")

    # Pass 2: Resolve manager_email → boss_id
    if "manager_email" in col_map:
        for i, row in enumerate(rows, start=2):
            try:
                email = row.get(col_map.get("email", ""), "").strip().lower()
                manager_email = row.get(col_map.get("manager_email", ""), "").strip().lower()

                if not email or not manager_email:
                    continue

                emp_id = email_to_id.get(email)
                boss_id = email_to_id.get(manager_email)

                if emp_id and boss_id:
                    queries.update_employee(emp_id, {"boss_id": boss_id})
                elif emp_id and manager_email:
                    errors.append(
                        f"Row {i}: manager '{manager_email}' not found for '{email}'"
                    )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Row {i} (boss resolution): {exc}")

    return ImportResult(created=created, updated=updated, errors=errors)
