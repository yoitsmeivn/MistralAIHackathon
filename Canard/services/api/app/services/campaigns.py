# pyright: basic
from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timezone

from app.db import queries

LOGGER = logging.getLogger(__name__)


def create_campaign(
    name: str,
    org_id: str,
    created_by: str | None = None,
    description: str | None = None,
    attack_vector: str | None = None,
    scheduled_at: str | None = None,
) -> dict:
    data: dict[str, str] = {"name": name, "org_id": org_id}
    if created_by:
        data["created_by"] = created_by
    if description:
        data["description"] = description
    if attack_vector:
        data["attack_vector"] = attack_vector
    if scheduled_at:
        data["scheduled_at"] = scheduled_at
    return queries.create_campaign(data)


def get_campaign(campaign_id: str) -> dict | None:
    return queries.get_campaign(campaign_id)


def list_campaigns(org_id: str) -> list[dict]:
    return queries.list_campaigns(org_id)


async def launch_campaign(
    campaign_id: str,
    script_id: str | None = None,
    caller_id: str | None = None,
    department: str | None = None,
    employee_ids: list[str] | None = None,
) -> dict:
    """Validate inputs, create assignments, kick off background execution.

    When script_id is provided, every employee gets that single script
    (caller_id is also required in this mode).

    When script_id is omitted, all scripts belonging to the campaign are used
    and each employee is randomly assigned one of them.  caller_id is resolved
    automatically per assignment (defaults to the campaign's first active caller
    or must be supplied).
    """
    campaign = queries.get_campaign(campaign_id)
    if not campaign:
        raise ValueError("Campaign not found")
    if campaign.get("status") not in ("draft", "paused"):
        raise ValueError(f"Campaign cannot be launched (status={campaign.get('status')})")

    org_id = campaign["org_id"]

    # ── Resolve scripts & callers ──────────────────────────────────────
    if script_id:
        # Single-script mode
        script = queries.get_script(script_id)
        if not script:
            raise ValueError("Script not found")
        if not caller_id:
            raise ValueError("caller_id is required when launching a single script")
        caller = queries.get_caller(caller_id)
        if not caller:
            raise ValueError("Caller not found")
        script_pool = None  # signals single-script mode below
    else:
        # All-scripts (random) mode — pull every active script for this campaign
        campaign_scripts = queries.list_scripts_by_campaign(campaign_id)
        if not campaign_scripts:
            raise ValueError("Campaign has no scripts")
        script_pool = campaign_scripts

        # Resolve a default caller when none was provided
        if not caller_id:
            callers = queries.list_callers(org_id, active_only=True)
            if not callers:
                raise ValueError("No active callers available")
            caller_id = callers[0]["id"]
        else:
            caller = queries.get_caller(caller_id)
            if not caller:
                raise ValueError("Caller not found")

    # ── Resolve target employees ───────────────────────────────────────
    if employee_ids:
        employees = [queries.get_employee(eid) for eid in employee_ids]
        employees = [e for e in employees if e and e.get("is_active")]
    elif department:
        employees = queries.list_employees_by_department(org_id, department)
    else:
        employees = queries.list_employees(org_id, active_only=True)

    if not employees:
        raise ValueError("No eligible employees found")

    # ── Build assignment rows ──────────────────────────────────────────
    assignment_rows: list[dict] = []
    for emp in employees:
        if script_pool:
            chosen_script = random.choice(script_pool)
            row_script_id = chosen_script["id"]
        else:
            row_script_id = script_id

        assignment_rows.append(
            {
                "campaign_id": campaign_id,
                "employee_id": emp["id"],
                "caller_id": caller_id,
                "script_id": row_script_id,
                "status": "pending",
            }
        )

    assignments = queries.bulk_create_campaign_assignments(assignment_rows)

    # Update campaign to running
    now = datetime.now(timezone.utc).isoformat()
    queries.update_campaign(campaign_id, {"status": "running", "started_at": now})

    # Fire background execution — returns immediately
    asyncio.create_task(
        _execute_campaign_calls(campaign_id=campaign_id, assignments=assignments)
    )

    return {
        "campaign_id": campaign_id,
        "status": "running",
        "assignment_count": len(assignments),
    }


async def _execute_campaign_calls(
    campaign_id: str,
    assignments: list[dict],
) -> None:
    """Iterate assignments sequentially, calling each employee.

    script_id and caller_id are read from each assignment row so this
    works for both single-script and random-script modes.
    """
    from app.services.calls import start_call

    LOGGER.info(
        "Campaign %s: starting %d calls", campaign_id, len(assignments)
    )

    for i, assignment in enumerate(assignments):
        assignment_id = assignment["id"]
        employee_id = assignment["employee_id"]
        a_script_id = assignment["script_id"]
        a_caller_id = assignment["caller_id"]

        queries.update_campaign_assignment(assignment_id, {"status": "in_progress"})

        try:
            await start_call(
                employee_id=employee_id,
                script_id=a_script_id,
                caller_id=a_caller_id,
                campaign_id=campaign_id,
                assignment_id=assignment_id,
            )
            queries.update_campaign_assignment(assignment_id, {"status": "completed"})
        except Exception:
            LOGGER.exception(
                "Campaign %s: call failed for employee %s",
                campaign_id,
                employee_id,
            )
            queries.update_campaign_assignment(assignment_id, {"status": "failed"})

        # Rate-limit delay between calls (skip after last)
        if i < len(assignments) - 1:
            await asyncio.sleep(5)

    # Mark campaign completed
    now = datetime.now(timezone.utc).isoformat()
    queries.update_campaign(campaign_id, {"status": "completed", "completed_at": now})
    LOGGER.info("Campaign %s: completed all calls", campaign_id)
