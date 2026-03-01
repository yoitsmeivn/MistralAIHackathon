# pyright: reportMissingImports=false
from __future__ import annotations

from app.agent.memory import session_store
from app.agent.prompts import build_system_prompt


def test_build_system_prompt_dict_api() -> None:
    scenario = {
        "name": "CEO Wire Transfer",
        "objectives": ["get_password"],
        "escalation_steps": ["create urgency"],
        "attack_type": "authority_impersonation",
        "difficulty": "hard",
        "system_prompt": "",
        "description": "Test",
    }
    result = build_system_prompt(scenario)

    assert isinstance(result, str)
    assert "authority_impersonation" in result
    assert "get_password" in result
    assert "NEVER ask for real passwords" in result


def test_build_system_prompt_legacy_api() -> None:
    result = build_system_prompt(
        scenario_name="Test Scenario",
        script_guidelines="Be polite",
    )

    assert isinstance(result, str)
    assert "Test Scenario" in result


def test_trim_messages_respects_budget() -> None:
    call_id = "test-trim-1"
    system_prompt = "S" * 500  # 500-char system prompt

    session_store.create(
        call_id=call_id, script_id="script-1", system_prompt=system_prompt
    )

    # Add 50 messages of 200 chars each
    for i in range(50):
        role = "user" if i % 2 == 0 else "assistant"
        session_store.add_message(call_id, role, "M" * 200)

    session_store.trim_messages(call_id)

    session = session_store.get(call_id)
    assert session is not None

    # System prompt must be preserved as first message
    assert session.messages[0]["role"] == "system"
    assert session.messages[0]["content"] == system_prompt

    # At least 5 messages remain (system + at least 4 non-system)
    assert len(session.messages) >= 5

    # Clean up
    session_store.remove(call_id)


def test_get_context_usage_structure() -> None:
    call_id = "test-usage-1"
    session_store.create(
        call_id=call_id, script_id="script-2", system_prompt="System prompt"
    )
    session_store.add_message(call_id, "user", "Hello there")

    usage = session_store.get_context_usage(call_id)

    assert isinstance(usage, dict)
    assert "estimated_tokens" in usage
    assert "message_count" in usage
    assert "budget" in usage
    assert "utilization_pct" in usage

    # Clean up
    session_store.remove(call_id)
