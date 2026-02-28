# pyright: reportMissingImports=false
from datetime import datetime

from app.models import Call, Employee, HealthResponse, StartCallRequest


def test_employee_model_creation_with_all_fields() -> None:
    employee = Employee(
        id="emp-123",
        org_id="org-456",
        full_name="Alex Doe",
        email="alex@example.com",
        phone="+14155552671",
        department="Security",
        job_title="Analyst",
        risk_level="low",
        is_active=True,
        created_at=datetime.fromisoformat("2026-02-28T12:00:00+00:00"),
    )

    assert employee.id == "emp-123"
    assert employee.department == "Security"
    assert employee.risk_level == "low"


def test_call_model_defaults() -> None:
    call = Call(id="call-1", org_id="org-456", employee_id="emp-123")

    assert call.status == "pending"
    assert call.campaign_id is None
    assert call.risk_score is None
    assert call.flags == []


def test_start_call_request_model_creation() -> None:
    req = StartCallRequest(employee_id="emp-123", script_id="scr-456")

    assert req.employee_id == "emp-123"
    assert req.script_id == "scr-456"
    assert req.campaign_id is None


def test_call_model_with_analysis_fields() -> None:
    call = Call(
        id="call-1",
        org_id="org-456",
        employee_id="emp-123",
        risk_score=72,
        flags=["credential_harvest", "urgency_pressure"],
        ai_summary="Caller attempted social engineering.",
        employee_compliance="failed",
    )

    assert call.risk_score == 72
    assert call.flags == ["credential_harvest", "urgency_pressure"]
    assert call.employee_compliance == "failed"


def test_health_response_model_creation() -> None:
    health = HealthResponse(status="ok", timestamp="2026-02-28T12:00:00Z")

    assert health.status == "ok"
    assert "T" in health.timestamp
