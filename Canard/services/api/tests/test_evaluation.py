# pyright: reportMissingImports=false
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.audio_features import AudioFeatures
from app.services.evaluation import (
    build_evaluation_prompt,
    evaluate_call,
    get_employee_call_history,
)


# ── get_employee_call_history ──


def test_employee_history_missing_employee() -> None:
    with patch("app.services.evaluation.queries") as mock_queries:
        mock_queries.get_employee.return_value = None
        result = get_employee_call_history("emp-1", "org-1")

    assert result["employee"] is None


def test_employee_history_aggregates_past_calls() -> None:
    employee = {
        "name": "Jane Doe",
        "department": "Finance",
        "title": "Accountant",
        "risk_level": "medium",
    }
    past_calls = [
        {"id": "c1", "risk_score": 30, "employee_compliance": "strong_resistance", "flags": ["none"]},
        {"id": "c2", "risk_score": 70, "employee_compliance": "partial_compliance", "flags": '["shared_info"]'},
        {"id": "c3", "risk_score": 50, "employee_compliance": None, "flags": None},
    ]

    with patch("app.services.evaluation.queries") as mock_queries:
        mock_queries.get_employee.return_value = employee
        mock_queries.list_calls.return_value = past_calls

        result = get_employee_call_history("emp-1", "org-1", exclude_call_id="c-current")

    assert result["employee"]["name"] == "Jane Doe"
    assert result["total_past_calls"] == 3
    assert result["avg_risk_score"] == 50.0  # (30+70+50)/3
    assert "strong_resistance" in result["compliance_results"]


def test_employee_history_excludes_current_call() -> None:
    employee = {"name": "X", "department": "", "title": "", "risk_level": "low"}
    past_calls = [
        {"id": "c-current", "risk_score": 80, "employee_compliance": None, "flags": None},
        {"id": "c-old", "risk_score": 20, "employee_compliance": None, "flags": None},
    ]

    with patch("app.services.evaluation.queries") as mock_queries:
        mock_queries.get_employee.return_value = employee
        mock_queries.list_calls.return_value = past_calls

        result = get_employee_call_history("emp-1", "org-1", exclude_call_id="c-current")

    assert result["total_past_calls"] == 1  # c-current excluded


# ── build_evaluation_prompt ──


def test_build_prompt_all_sections() -> None:
    transcript = "Agent: Hi, I need your password.\nUser: No way."
    audio_features = AudioFeatures(
        duration_seconds=30.0,
        disfluency_count=2,
        disfluency_words=["um", "uh"],
    )
    script = {
        "attack_type": "credential_phishing",
        "difficulty": "medium",
        "objectives": ["obtain password", "get email access"],
    }
    employee_history = {
        "employee": {
            "name": "Bob",
            "department": "IT",
            "title": "Engineer",
            "risk_level": "low",
        },
        "total_past_calls": 3,
        "avg_risk_score": 25.0,
        "common_flags": ["hesitated"],
    }

    prompt = build_evaluation_prompt(transcript, audio_features, script, employee_history)

    assert "## Call Transcript" in prompt
    assert "No way" in prompt
    assert "## Audio & Behavioral Features" in prompt
    assert "Duration: 30.0s" in prompt
    assert "## Attack Script Context" in prompt
    assert "credential_phishing" in prompt
    assert "obtain password" in prompt
    assert "## Employee Profile & History" in prompt
    assert "Bob" in prompt
    assert "hesitated" in prompt


def test_build_prompt_minimal_no_audio_no_script() -> None:
    prompt = build_evaluation_prompt(
        transcript="User: Hello",
        audio_features=None,
        script=None,
        employee_history={"employee": None},
    )

    assert "## Call Transcript" in prompt
    assert "Hello" in prompt
    # Should not contain optional sections
    assert "## Audio" not in prompt
    assert "## Attack Script" not in prompt
    assert "## Employee Profile" not in prompt


def test_build_prompt_json_string_objectives() -> None:
    script = {
        "attack_type": "vishing",
        "difficulty": "hard",
        "objectives": '["steal credentials", "install malware"]',
    }
    prompt = build_evaluation_prompt("transcript", None, script, {"employee": None})

    assert "steal credentials" in prompt
    assert "install malware" in prompt


# ── evaluate_call ──


def _mock_evaluation_response() -> dict:
    return {
        "risk_score": 65,
        "employee_compliance": "partial_compliance",
        "flags": ["shared_partial_info", "hesitated_but_complied"],
        "ai_summary": "Employee initially resisted but eventually shared some info.",
        "coaching": "Always verify caller identity. Never share partial credentials.",
        "sentiment_analysis": {
            "tone": "anxious",
            "stress_indicators": ["long pauses", "filler words"],
            "compliance_progression": "Started resistant, became compliant mid-call",
        },
        "risk_level_recommendation": "high",
    }


def test_evaluate_call_full_pipeline() -> None:
    call = {
        "id": "call-1",
        "script_id": "script-1",
        "employee_id": "emp-1",
        "org_id": "org-1",
        "recording_url": None,
        "transcript": None,
    }
    script = {
        "attack_type": "credential_phishing",
        "difficulty": "medium",
        "objectives": ["get password"],
    }
    employee = {
        "name": "Test User",
        "department": "IT",
        "title": "Dev",
        "risk_level": "low",
    }

    eval_response = _mock_evaluation_response()

    with patch("app.services.evaluation.queries") as mock_queries:
        mock_queries.get_call.return_value = call
        mock_queries.get_script.return_value = script
        mock_queries.get_employee.return_value = employee
        mock_queries.list_calls.return_value = []
        mock_queries.update_call.return_value = {}
        mock_queries.update_employee.return_value = {}

        with patch(
            "app.services.evaluation.chat_completion_json",
            new_callable=AsyncMock,
            return_value=eval_response,
        ):
            result = asyncio.run(
                evaluate_call("call-1", recording_transcript="Agent: Give me your password.\nUser: OK, it's abc123.")
            )

    assert result is not None
    assert result["risk_score"] == 65
    assert result["employee_compliance"] == "partial_compliance"
    assert "shared_partial_info" in result["flags"]
    assert result["risk_level_recommendation"] == "high"

    # Verify DB writes
    mock_queries.update_call.assert_called_once()
    update_data = mock_queries.update_call.call_args[0][1]
    assert update_data["risk_score"] == 65
    assert update_data["employee_compliance"] == "partial_compliance"

    mock_queries.update_employee.assert_called_once_with("emp-1", {"risk_level": "high"})


def test_evaluate_call_no_transcript_returns_none() -> None:
    call = {
        "id": "call-1",
        "script_id": None,
        "employee_id": None,
        "org_id": None,
        "recording_url": None,
        "transcript": None,
    }

    with patch("app.services.evaluation.queries") as mock_queries:
        mock_queries.get_call.return_value = call
        result = asyncio.run(evaluate_call("call-1"))

    assert result is None


def test_evaluate_call_missing_call_returns_none() -> None:
    with patch("app.services.evaluation.queries") as mock_queries:
        mock_queries.get_call.return_value = None
        result = asyncio.run(evaluate_call("nonexistent"))

    assert result is None


def test_evaluate_call_clamps_risk_score() -> None:
    call = {
        "id": "call-1",
        "script_id": None,
        "employee_id": None,
        "org_id": None,
        "recording_url": None,
        "transcript": "some transcript",
    }
    bad_response = {
        "risk_score": 150,  # out of range
        "employee_compliance": "invalid_value",
        "flags": "not_a_list",
        "ai_summary": "",
        "coaching": "",
        "sentiment_analysis": "not_a_dict",
        "risk_level_recommendation": "invalid",
    }

    with patch("app.services.evaluation.queries") as mock_queries:
        mock_queries.get_call.return_value = call
        mock_queries.update_call.return_value = {}

        with patch(
            "app.services.evaluation.chat_completion_json",
            new_callable=AsyncMock,
            return_value=bad_response,
        ):
            result = asyncio.run(evaluate_call("call-1"))

    assert result is not None
    assert result["risk_score"] == 100  # clamped
    assert result["employee_compliance"] == "partial_compliance"  # default
    assert result["flags"] == []  # "not_a_list" is not a list
    assert result["sentiment_analysis"] == {}  # "not_a_dict" rejected
    assert result["risk_level_recommendation"] == "medium"  # default


def test_evaluate_call_audio_failure_continues() -> None:
    """Audio feature extraction failure should not block evaluation."""
    call = {
        "id": "call-1",
        "script_id": None,
        "employee_id": None,
        "org_id": None,
        "recording_url": "https://api.twilio.com/recording/123",
        "transcript": None,
    }
    eval_response = _mock_evaluation_response()

    with patch("app.services.evaluation.queries") as mock_queries:
        mock_queries.get_call.return_value = call
        mock_queries.update_call.return_value = {}

        with patch(
            "app.services.evaluation.download_recording",
            new_callable=AsyncMock,
            side_effect=Exception("Network error"),
        ):
            with patch(
                "app.services.evaluation.chat_completion_json",
                new_callable=AsyncMock,
                return_value=eval_response,
            ):
                result = asyncio.run(
                    evaluate_call("call-1", recording_transcript="User: Hello")
                )

    # Should still succeed despite audio failure
    assert result is not None
    assert result["risk_score"] == 65
