# pyright: basic, reportMissingImports=false
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.auth.middleware import OptionalUser
from app.db import queries
from app.models.api import EmployeeListItem

router = APIRouter(prefix="/api/employees", tags=["employees"])


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
            )
        )
    return items
