#!/usr/bin/env python3
"""Re-evaluate completed calls that have transcripts but missing evaluation data."""

import asyncio
import os
import sys

# Add the api app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

# Load .env from repo root
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))

from app.db.client import get_supabase
from app.services.evaluation import evaluate_call


async def main():
    sb = get_supabase()

    # Fetch all completed calls
    result = (
        sb.table("calls")
        .select("id,status,transcript,risk_score,employee_compliance")
        .eq("status", "completed")
        .limit(500)
        .execute()
    )

    all_calls = result.data or []

    # Filter: has transcript (non-empty) AND missing risk_score or employee_compliance
    to_evaluate = [
        c
        for c in all_calls
        if c.get("transcript")
        and len(c.get("transcript", "")) > 50
        and (c.get("risk_score") is None or c.get("employee_compliance") is None)
    ]

    print(f"Total completed calls: {len(all_calls)}")
    print(f"Calls to re-evaluate: {len(to_evaluate)}")

    if not to_evaluate:
        print("Nothing to evaluate.")
        return

    for i, call in enumerate(to_evaluate):
        call_id = call["id"]
        print(
            f"[{i + 1}/{len(to_evaluate)}] Evaluating {call_id[:8]}...",
            end=" ",
            flush=True,
        )
        try:
            result = await evaluate_call(call_id)
            if result:
                print(
                    f"risk={result['risk_score']} compliance={result['employee_compliance']}"
                )
            else:
                print("SKIPPED (no result)")
        except Exception as e:
            print(f"ERROR: {e}")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
