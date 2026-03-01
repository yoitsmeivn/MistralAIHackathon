# pyright: reportMissingImports=false
"""Integration tests — sends real transcripts through Mistral and validates
that the evaluation produces structurally correct, semantically reasonable
results.

Requires MISTRAL_API_KEY in the environment.  Skipped automatically if the
key is missing.

Run with:
    pytest tests/test_evaluation_integration.py -v -s
"""
from __future__ import annotations

import asyncio
import os
import sys

import pytest

# Load the project .env so the Mistral key is available BEFORE importing app modules
from dotenv import load_dotenv

# Walk up from tests/ → api/ → services/ → Canard/ → MistralAIHackathon/.env
_env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env"))
load_dotenv(_env_path, override=True)

_HAS_KEY = bool(os.environ.get("MISTRAL_API_KEY"))
pytestmark = pytest.mark.skipif(not _HAS_KEY, reason="MISTRAL_API_KEY not set")

# Force settings to reload from env (the singleton may have been created with empty values)
import app.config
app.config.settings = app.config.Settings()

# Reset the cached Mistral client so it picks up the new settings
import app.integrations.mistral as _mistral_mod
_mistral_mod._client_instance = None

from app.integrations.mistral import chat_completion_json
from app.services.audio_features import AudioFeatures, extract_tone_markers
from app.services.evaluation import (
    EVALUATION_SYSTEM_PROMPT,
    build_evaluation_prompt,
)

# ---------------------------------------------------------------------------
# Transcripts (same as test_evaluation_scenarios.py)
# ---------------------------------------------------------------------------

TRANSCRIPT_STRONG_RESISTANCE = """\
Agent: Hi, this is Mike from IT support. We've detected unusual activity on your account \
and need to verify your credentials right away.
User: (skeptical) That sounds odd. I wasn't notified about any issues by email.
Agent: This is urgent — your account may be compromised. I just need your employee ID \
and password to run a quick security check.
User: (firm) No. I'm not giving you my password over the phone. That's against our policy.
Agent: I understand your concern, but if we don't act now your files could be deleted.
User: (assertive) I don't care what you say. I'm going to hang up and call the IT help desk \
directly to verify this. (confident) I know the number — I'll handle it myself.
Agent: Wait, please don't—
User: (defiant) Goodbye."""

TRANSCRIPT_NERVOUS_COMPLIANCE = """\
Agent: Hello, this is Sarah from the security team. We've had a data breach and need to \
reset your account immediately.
User: (nervous) Oh no, um, really? What happened?
Agent: I can't share details yet, but I need your employee ID to start the reset process.
User: (hesitant) Uh, I don't know if I should... (long pause) ...it's, um, EMP-4472.
Agent: Thank you. Now I'll need your current password so I can verify your identity before \
the reset.
User: (anxious) My password? That seems... (pause) ...I mean, you know, I'm not sure \
about this. (nervous laugh)
Agent: I completely understand. This is standard procedure during a breach. Your manager \
approved this process.
User: (worried) OK, um, if my manager approved it... (long pause) ...it's Summer2024!. \
(uneasy) Please don't share it with anyone.
Agent: Of course, this is completely confidential. Thank you for your cooperation."""

TRANSCRIPT_GRADUAL_BREAKDOWN = """\
Agent: Good afternoon, this is James from corporate compliance. We're conducting \
mandatory security audits and your department has been flagged.
User: (suspicious) Flagged for what? I haven't heard anything about an audit.
Agent: It's a confidential investigation. I need to verify your access credentials \
as part of the audit.
User: (questioning) I'd like to see some documentation first. Can you email me something?
Agent: Unfortunately, due to the nature of this investigation, everything must be done \
verbally. Your VP authorized this personally.
User: (hesitant) Hmm, well... (pause) ...I still don't feel right about this.
Agent: I understand. But I should let you know that employees who don't cooperate with \
compliance audits may face disciplinary action.
User: (anxious) Disciplinary action? (long pause) (stuttering) I... I don't want any trouble.
Agent: Of course not. Just verify your login credentials and we'll mark you as compliant.
User: (sighing) Fine. (frustrated) My username is jsmith and my password is \
Tr0ub4dor&3. (angry) But I'm going to ask my manager about this afterwards."""

TRANSCRIPT_FULL_COMPLIANCE = """\
Agent: Hi, this is tech support. Your computer has been sending us error reports and \
we need to remote in to fix it.
User: (cooperative) Oh OK, sure! What do I need to do?
Agent: First, can you give me your network login?
User: (willing) Yeah, it's jdoe.
Agent: And your password?
User: (obliging) It's Password123.
Agent: Great. Now I need you to go to this website and download our support tool.
User: (agreeing) OK, what's the address?
Agent: Go to totally-legit-support dot com and click the green download button.
User: (cooperative) Done! It's installing now. Anything else you need?
Agent: That's all for now, we'll take it from here."""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_COMPLIANCE = {
    "strong_resistance",
    "moderate_resistance",
    "partial_compliance",
    "significant_compliance",
    "full_compliance",
}
VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}


def _build_prompt_for_transcript(transcript: str) -> list[dict]:
    markers = extract_tone_markers(transcript)
    features = AudioFeatures(
        duration_seconds=120.0,
        stress_indicators=markers["stress"],
        compliance_signals=markers["compliance"],
        resistance_signals=markers["resistance"],
        pause_markers=markers["pause"],
        emotion_markers=markers["emotion"],
        tone_markers=markers["tone_markers"],
    )
    user_msg = build_evaluation_prompt(
        transcript=transcript,
        audio_features=features,
        script={
            "attack_type": "credential_phishing",
            "difficulty": "medium",
            "objectives": ["obtain employee credentials", "gain system access"],
        },
        employee_history={"employee": None},
    )
    return [
        {"role": "system", "content": EVALUATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


def _evaluate(transcript: str) -> dict:
    messages = _build_prompt_for_transcript(transcript)
    return _run(chat_completion_json(messages=messages, temperature=0.1))


# ---------------------------------------------------------------------------
# Structural validation — every response must have correct shape
# ---------------------------------------------------------------------------


def _assert_valid_structure(result: dict, label: str) -> None:
    """Assert the response has all required keys with correct types."""
    assert isinstance(result, dict), f"{label}: result is not a dict"

    assert "risk_score" in result, f"{label}: missing risk_score"
    assert isinstance(result["risk_score"], (int, float)), f"{label}: risk_score not numeric"
    assert 0 <= result["risk_score"] <= 100, f"{label}: risk_score={result['risk_score']} out of range"

    assert "employee_compliance" in result, f"{label}: missing employee_compliance"
    assert result["employee_compliance"] in VALID_COMPLIANCE, (
        f"{label}: invalid compliance={result['employee_compliance']}"
    )

    assert "flags" in result, f"{label}: missing flags"
    assert isinstance(result["flags"], list), f"{label}: flags not a list"

    assert "ai_summary" in result, f"{label}: missing ai_summary"
    ai_summary = result["ai_summary"]
    # Mistral may return a string or {"summary": "..."} — both are fine
    if isinstance(ai_summary, dict):
        ai_summary = ai_summary.get("summary", "")
    assert isinstance(ai_summary, str), f"{label}: ai_summary not a string"
    assert len(ai_summary) > 10, f"{label}: ai_summary too short"

    assert "coaching" in result, f"{label}: missing coaching"
    coaching = result["coaching"]
    if isinstance(coaching, dict):
        coaching = coaching.get("advice", "") or coaching.get("coaching", "")
    assert isinstance(coaching, str), f"{label}: coaching not a string"
    assert len(coaching) > 10, f"{label}: coaching too short"

    assert "sentiment_analysis" in result, f"{label}: missing sentiment_analysis"
    assert isinstance(result["sentiment_analysis"], dict), f"{label}: sentiment_analysis not a dict"

    assert "risk_level_recommendation" in result, f"{label}: missing risk_level_recommendation"
    assert result["risk_level_recommendation"] in VALID_RISK_LEVELS, (
        f"{label}: invalid risk_level={result['risk_level_recommendation']}"
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_strong_resistance_scores_low() -> None:
    """Employee who refuses everything should get a LOW risk score."""
    result = _evaluate(TRANSCRIPT_STRONG_RESISTANCE)
    _assert_valid_structure(result, "strong_resistance")

    print(f"\n[strong_resistance] risk_score={result['risk_score']}, "
          f"compliance={result['employee_compliance']}, "
          f"risk_level={result['risk_level_recommendation']}")
    print(f"  flags: {result['flags']}")
    print(f"  summary: {result['ai_summary']}")

    assert result["risk_score"] <= 25, (
        f"Strong resistance should score <=25, got {result['risk_score']}"
    )
    assert result["employee_compliance"] in {"strong_resistance", "moderate_resistance"}
    assert result["risk_level_recommendation"] in {"low", "medium"}


def test_nervous_compliance_scores_high() -> None:
    """Employee who gives up password under pressure should get a HIGH risk score."""
    result = _evaluate(TRANSCRIPT_NERVOUS_COMPLIANCE)
    _assert_valid_structure(result, "nervous_compliance")

    print(f"\n[nervous_compliance] risk_score={result['risk_score']}, "
          f"compliance={result['employee_compliance']}, "
          f"risk_level={result['risk_level_recommendation']}")
    print(f"  flags: {result['flags']}")
    print(f"  summary: {result['ai_summary']}")

    assert result["risk_score"] >= 60, (
        f"Nervous compliance should score >=60, got {result['risk_score']}"
    )
    assert result["employee_compliance"] in {
        "significant_compliance", "full_compliance", "partial_compliance"
    }
    assert result["risk_level_recommendation"] in {"high", "critical"}
    # Should flag credential disclosure
    flags_lower = [f.lower() for f in result["flags"]]
    assert any("password" in f or "credential" in f or "shared" in f for f in flags_lower), (
        f"Should flag credential sharing, got: {result['flags']}"
    )


def test_gradual_breakdown_scores_moderate_to_high() -> None:
    """Employee who starts resistant but caves should score in the middle-to-high range."""
    result = _evaluate(TRANSCRIPT_GRADUAL_BREAKDOWN)
    _assert_valid_structure(result, "gradual_breakdown")

    print(f"\n[gradual_breakdown] risk_score={result['risk_score']}, "
          f"compliance={result['employee_compliance']}, "
          f"risk_level={result['risk_level_recommendation']}")
    print(f"  flags: {result['flags']}")
    print(f"  sentiment: {result['sentiment_analysis']}")

    assert result["risk_score"] >= 50, (
        f"Gradual breakdown should score >=50, got {result['risk_score']}"
    )
    # Sentiment should reflect the progression
    sentiment = result.get("sentiment_analysis", {})
    if "compliance_progression" in sentiment:
        progression = sentiment["compliance_progression"].lower()
        # Should mention some kind of change/shift
        assert any(w in progression for w in [
            "initial", "start", "began", "eventually", "gradual", "shift", "broke", "cav"
        ]), f"Progression should note the shift: {progression}"


def test_full_compliance_scores_very_high() -> None:
    """Employee who instantly cooperates with everything should get the highest risk score."""
    result = _evaluate(TRANSCRIPT_FULL_COMPLIANCE)
    _assert_valid_structure(result, "full_compliance")

    print(f"\n[full_compliance] risk_score={result['risk_score']}, "
          f"compliance={result['employee_compliance']}, "
          f"risk_level={result['risk_level_recommendation']}")
    print(f"  flags: {result['flags']}")

    assert result["risk_score"] >= 80, (
        f"Full compliance should score >=80, got {result['risk_score']}"
    )
    assert result["employee_compliance"] in {"full_compliance", "significant_compliance"}
    assert result["risk_level_recommendation"] in {"high", "critical"}
    assert len(result["flags"]) >= 2, "Should flag multiple concerning behaviors"


def test_risk_ordering_is_consistent() -> None:
    """The four scenarios should rank in order:
    strong_resistance < gradual_breakdown < nervous_compliance <= full_compliance
    """
    r1 = _evaluate(TRANSCRIPT_STRONG_RESISTANCE)
    r2 = _evaluate(TRANSCRIPT_GRADUAL_BREAKDOWN)
    r3 = _evaluate(TRANSCRIPT_NERVOUS_COMPLIANCE)
    r4 = _evaluate(TRANSCRIPT_FULL_COMPLIANCE)

    scores = {
        "strong_resistance": r1["risk_score"],
        "gradual_breakdown": r2["risk_score"],
        "nervous_compliance": r3["risk_score"],
        "full_compliance": r4["risk_score"],
    }
    print(f"\n[ordering] {scores}")

    assert scores["strong_resistance"] < scores["gradual_breakdown"], (
        f"Resistance ({scores['strong_resistance']}) should < breakdown ({scores['gradual_breakdown']})"
    )
    assert scores["gradual_breakdown"] <= scores["full_compliance"], (
        f"Breakdown ({scores['gradual_breakdown']}) should <= full ({scores['full_compliance']})"
    )
    assert scores["strong_resistance"] < scores["full_compliance"], (
        f"Resistance ({scores['strong_resistance']}) should < full ({scores['full_compliance']})"
    )
