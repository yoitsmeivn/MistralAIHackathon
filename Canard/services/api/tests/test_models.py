# pyright: reportMissingImports=false
from datetime import datetime

from app.models import Analysis, Call, HealthResponse, Participant, StartCallRequest


def test_participant_model_creation_with_all_fields() -> None:
    participant = Participant(
        id="part-123",
        name="Alex Doe",
        email="alex@example.com",
        phone="+14155552671",
        team="Security",
        active=True,
        opt_in=True,
        created_at=datetime.fromisoformat("2026-02-28T12:00:00+00:00"),
    )

    assert participant.id == "part-123"
    assert participant.team == "Security"
    assert participant.opt_in is True


def test_call_model_defaults() -> None:
    call = Call(id="call-1", participant_id="part-123", scenario_id="scn-456")

    assert call.status == "pending"
    assert call.consented is False
    assert call.campaign_id is None


def test_start_call_request_model_creation() -> None:
    req = StartCallRequest(participant_id="part-123", scenario_id="scn-456")

    assert req.participant_id == "part-123"
    assert req.scenario_id == "scn-456"
    assert req.campaign_id is None


def test_analysis_model_with_flags_list() -> None:
    analysis = Analysis(
        call_id="call-1",
        risk_score=72,
        flags=["credential_harvest", "urgency_pressure"],
        summary="Caller attempted social engineering.",
        coaching="Verify identity before sharing credentials.",
    )

    assert analysis.risk_score == 72
    assert analysis.flags == ["credential_harvest", "urgency_pressure"]


def test_health_response_model_creation() -> None:
    health = HealthResponse(status="ok", timestamp="2026-02-28T12:00:00Z")

    assert health.status == "ok"
    assert "T" in health.timestamp
