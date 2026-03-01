# pyright: basic
from __future__ import annotations

import json
import logging
from typing import Any

from app.db import queries
from app.integrations.mistral import chat_completion_json
from app.services.audio_features import (
    AudioFeatures,
    download_recording,
    extract_audio_features,
)

# Map Mistral compliance values → analytics-compatible values
COMPLIANCE_MAP = {
    "strong_resistance": "passed",
    "moderate_resistance": "passed",
    "partial_compliance": "partial",
    "significant_compliance": "failed",
    "full_compliance": "failed",
}

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Employee call history aggregation
# ---------------------------------------------------------------------------


def get_employee_call_history(
    employee_id: str, org_id: str, exclude_call_id: str | None = None
) -> dict[str, Any]:
    """Build an employee profile + past call aggregates for evaluation context."""
    employee = queries.get_employee(employee_id)
    if not employee:
        return {"employee": None, "past_calls": []}

    profile = {
        "name": employee.get("name", "Unknown"),
        "department": employee.get("department", ""),
        "title": employee.get("title", ""),
        "risk_level": employee.get("risk_level", "unknown"),
    }

    past_calls = queries.list_calls(org_id, employee_id=employee_id, limit=20)
    if exclude_call_id:
        past_calls = [c for c in past_calls if c.get("id") != exclude_call_id]

    # Aggregate history
    risk_scores: list[int] = []
    compliance_results: list[str] = []
    common_flags: list[str] = []

    for call in past_calls:
        rs = call.get("risk_score")
        if rs is not None:
            risk_scores.append(int(rs))
        ec = call.get("employee_compliance")
        if ec:
            compliance_results.append(str(ec))
        flags = call.get("flags")
        if isinstance(flags, list):
            common_flags.extend(str(f) for f in flags)
        elif isinstance(flags, str):
            try:
                parsed = json.loads(flags)
                if isinstance(parsed, list):
                    common_flags.extend(str(f) for f in parsed)
            except (json.JSONDecodeError, ValueError):
                pass

    return {
        "employee": profile,
        "total_past_calls": len(past_calls),
        "avg_risk_score": (
            round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else None
        ),
        "compliance_results": compliance_results[-5:],  # last 5
        "common_flags": list(set(common_flags))[:10],
    }


# ---------------------------------------------------------------------------
# Evaluation prompt
# ---------------------------------------------------------------------------

EVALUATION_SYSTEM_PROMPT = """\
You are a cybersecurity training evaluator for a phishing-awareness platform.

You will receive:
1. A transcript of a simulated phishing call between an AI attacker and an employee
2. Audio & behavioral features from the call recording
3. The attack script context (attack type, difficulty, objectives)
4. The employee's profile and call history (for context only)

Your task: Evaluate the employee's RESISTANCE to the phishing attempt in THIS call only.
Use history for context, but score only the current call.

Scoring rules:
- risk_score: 0-100 integer. 0 = perfect resistance (refused everything). \
100 = full compliance (gave up all requested info/actions).
- employee_compliance: one of "strong_resistance", "moderate_resistance", \
"partial_compliance", "significant_compliance", "full_compliance"
- flags: array of specific concerning behaviors observed (e.g. "shared_password", \
"clicked_link", "provided_personal_info", "transferred_call", "hesitated_but_complied")
- ai_summary: 2-3 sentence summary of what happened in the call
- coaching: actionable 2-3 sentence coaching advice for the employee
- sentiment_analysis: object with "tone" (string), "stress_indicators" (array of strings), \
"compliance_progression" (string describing how resistance changed over the call)
- risk_level_recommendation: one of "low", "medium", "high", "critical" — \
recommended risk level for this employee going forward

Return ONLY valid JSON with exactly these keys. No extra text.\
"""


def build_evaluation_prompt(
    transcript: str,
    audio_features: AudioFeatures | None,
    script: dict | None,
    employee_history: dict[str, Any],
) -> str:
    """Build the user message with all evaluation context sections."""
    sections: list[str] = []

    # Section 1: Transcript
    sections.append(f"## Call Transcript\n\n{transcript}")

    # Section 2: Audio features
    if audio_features:
        sections.append(
            f"## Audio & Behavioral Features\n\n{audio_features.to_prompt_text()}"
        )

    # Section 3: Script context
    if script:
        attack_type = script.get("attack_type", "unknown")
        difficulty = script.get("difficulty", "unknown")
        objectives = script.get("objectives", [])
        if isinstance(objectives, str):
            try:
                objectives = json.loads(objectives)
            except (json.JSONDecodeError, ValueError):
                objectives = [objectives] if objectives else []

        obj_list = "\n".join(f"- {obj}" for obj in objectives) if objectives else "- None specified"
        sections.append(
            f"## Attack Script Context\n\n"
            f"- Attack type: {attack_type}\n"
            f"- Difficulty: {difficulty}\n"
            f"- Objectives:\n{obj_list}"
        )

    # Section 4: Employee history (context only)
    emp = employee_history.get("employee")
    if emp:
        history_lines = [
            f"- Name: {emp.get('name', 'Unknown')}",
            f"- Department: {emp.get('department', 'N/A')}",
            f"- Title: {emp.get('title', 'N/A')}",
            f"- Current risk level: {emp.get('risk_level', 'unknown')}",
            f"- Past calls: {employee_history.get('total_past_calls', 0)}",
        ]
        avg_rs = employee_history.get("avg_risk_score")
        if avg_rs is not None:
            history_lines.append(f"- Avg past risk score: {avg_rs}")
        common_flags = employee_history.get("common_flags", [])
        if common_flags:
            history_lines.append(f"- Common past flags: {', '.join(common_flags)}")

        sections.append(
            "## Employee Profile & History (context only — evaluate THIS call)\n\n"
            + "\n".join(history_lines)
        )

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Main evaluation pipeline
# ---------------------------------------------------------------------------


async def evaluate_call(
    call_id: str,
    recording_transcript: str | None = None,
) -> dict[str, Any] | None:
    """Run full post-call evaluation for a completed call.

    1. Fetch call + script from DB
    2. Build transcript
    3. Extract audio features (best-effort)
    4. Gather employee call history
    5. Call Mistral with JSON mode
    6. Validate + persist results

    Returns the evaluation result dict, or None on failure.
    """
    # ── 1. Fetch call + script ──
    call = queries.get_call(call_id)
    if not call:
        LOGGER.warning("Evaluation: call %s not found", call_id)
        return None

    script: dict | None = None
    script_id = call.get("script_id")
    if script_id:
        script = queries.get_script(script_id)

    # ── 2. Build transcript ──
    transcript = recording_transcript or call.get("transcript") or ""
    if not transcript:
        LOGGER.info("Evaluation: no transcript for call %s, skipping", call_id)
        return None

    # ── 3. Audio features (best-effort) ──
    audio_features: AudioFeatures | None = None
    recording_url = call.get("recording_url")
    if recording_url:
        try:
            audio_bytes = await download_recording(recording_url)
            audio_features = extract_audio_features(
                audio_bytes, transcript=transcript
            )
            LOGGER.info("Audio features extracted for call %s", call_id)
        except Exception:
            LOGGER.warning(
                "Audio feature extraction failed for call %s, continuing without",
                call_id,
                exc_info=True,
            )

    # ── 4. Employee history ──
    employee_id = call.get("employee_id")
    org_id = call.get("org_id")
    employee_history: dict[str, Any] = {"employee": None, "past_calls": []}
    if employee_id and org_id:
        try:
            employee_history = get_employee_call_history(
                employee_id, org_id, exclude_call_id=call_id
            )
        except Exception:
            LOGGER.warning(
                "Failed to fetch employee history for call %s", call_id, exc_info=True
            )

    # ── 5. Build prompt → Mistral JSON mode ──
    user_message = build_evaluation_prompt(
        transcript, audio_features, script, employee_history
    )

    messages = [
        {"role": "system", "content": EVALUATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    try:
        result = await chat_completion_json(messages=messages, temperature=0.1)
    except Exception:
        LOGGER.exception("Mistral evaluation call failed for call %s", call_id)
        return None

    # ── 6. Validate and clamp ──
    risk_score = max(0, min(100, int(result.get("risk_score", 0))))

    valid_compliance = {"passed", "failed", "partial"}
    employee_compliance_raw = result.get("employee_compliance", "partial_compliance")
    employee_compliance = COMPLIANCE_MAP.get(employee_compliance_raw, employee_compliance_raw)
    if employee_compliance not in valid_compliance:
        employee_compliance = "partial"

    flags_raw = result.get("flags", [])
    flags = [str(f) for f in flags_raw] if isinstance(flags_raw, list) else []

    ai_summary_raw = result.get("ai_summary", "")
    if isinstance(ai_summary_raw, dict):
        ai_summary = str(ai_summary_raw.get("summary", "") or ai_summary_raw)
    else:
        ai_summary = str(ai_summary_raw)

    coaching_raw = result.get("coaching", "")
    if isinstance(coaching_raw, dict):
        coaching = str(coaching_raw.get("advice", "") or coaching_raw.get("coaching", "") or coaching_raw)
    else:
        coaching = str(coaching_raw)

    sentiment_raw = result.get("sentiment_analysis")
    sentiment_analysis = (
        sentiment_raw if isinstance(sentiment_raw, dict) else {}
    )

    valid_risk_levels = {"low", "medium", "high", "critical"}
    risk_level_rec = result.get("risk_level_recommendation", "medium")
    if risk_level_rec not in valid_risk_levels:
        risk_level_rec = "medium"

    # ── 7. Persist to calls table ──
    call_update: dict[str, Any] = {
        "risk_score": risk_score,
        "employee_compliance": employee_compliance,
        "flags": flags,
        "ai_summary": ai_summary,
        "sentiment_analysis": sentiment_analysis,
    }

    # Also save the transcript if we have one and the call doesn't already
    if transcript and not call.get("transcript"):
        call_update["transcript"] = transcript

    try:
        queries.update_call(call_id, call_update)
    except Exception:
        LOGGER.warning(
            "Failed to persist evaluation results for call %s", call_id, exc_info=True
        )

    # ── 8. Update employee risk_level ──
    if employee_id and risk_level_rec:
        try:
            queries.update_employee(employee_id, {"risk_level": risk_level_rec})
        except Exception:
            LOGGER.warning(
                "Failed to update employee risk_level for %s", employee_id, exc_info=True
            )

    LOGGER.info(
        "Evaluation complete for call %s: risk_score=%d, compliance=%s, risk_level=%s",
        call_id,
        risk_score,
        employee_compliance,
        risk_level_rec,
    )

    return {
        "call_id": call_id,
        "risk_score": risk_score,
        "employee_compliance": employee_compliance,
        "flags": flags,
        "ai_summary": ai_summary,
        "coaching": coaching,
        "sentiment_analysis": sentiment_analysis,
        "risk_level_recommendation": risk_level_rec,
    }
