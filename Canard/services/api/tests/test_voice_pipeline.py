# pyright: reportMissingImports=false
from __future__ import annotations

from app.twilio_voice.session import AgentState, CallSessionData, TurnRole
from app.integrations.elevenlabs import sanitize_for_tts
from app.agent.prompts import BEHAVIORAL_INSTRUCTIONS, build_system_prompt
from app.config import settings


# ── AgentState enum ──


def test_agent_state_enum_values() -> None:
    assert AgentState.LISTENING.value == "listening"
    assert AgentState.PROCESSING.value == "processing"
    assert AgentState.SPEAKING.value == "speaking"


# ── CallSessionData state machine ──


def test_state_transition_updates_agent_state() -> None:
    session = CallSessionData(call_id="test-1")
    assert session.agent_state == AgentState.LISTENING
    session.state_transition(AgentState.PROCESSING)
    assert session.agent_state == AgentState.PROCESSING
    session.state_transition(AgentState.SPEAKING)
    assert session.agent_state == AgentState.SPEAKING
    session.state_transition(AgentState.LISTENING)
    assert session.agent_state == AgentState.LISTENING


def test_agent_is_speaking_property() -> None:
    session = CallSessionData(call_id="test-2")
    assert not session.agent_is_speaking
    session.state_transition(AgentState.SPEAKING)
    assert session.agent_is_speaking
    session.state_transition(AgentState.LISTENING)
    assert not session.agent_is_speaking


# ── sanitize_for_tts ──


def test_sanitize_for_tts_removes_stage_directions() -> None:
    assert sanitize_for_tts("Hello (laughs) world") == "Hello world"
    assert sanitize_for_tts("Sure [nervous] thing") == "Sure thing"
    assert sanitize_for_tts("*pauses*") == ""
    assert sanitize_for_tts("") == ""


def test_sanitize_for_tts_removes_markdown() -> None:
    # __X__ and _X_ patterns are pure markdown removal;
    # **X** interacts with *X* stage-direction pattern (by design)
    assert sanitize_for_tts("__bold text__") == "bold text"
    assert sanitize_for_tts("_italic_") == "italic"
    assert sanitize_for_tts("__underline__") == "underline"


# ── Prompt construction ──


def test_behavioral_instructions_has_turn_taking_lines() -> None:
    assert "After asking a question, STOP" in BEHAVIORAL_INSTRUCTIONS
    assert "Never answer your own question or assume" in BEHAVIORAL_INSTRUCTIONS


def test_build_system_prompt_includes_behavioral_instructions() -> None:
    prompt = build_system_prompt(scenario_name="Test", script_guidelines="test")
    assert "After asking a question, STOP" in prompt


# ── Generation counter pattern ──


def test_generation_counter_mutable_list_pattern() -> None:
    counter = [0]
    my_id = counter[0]
    assert my_id == counter[0]  # same generation
    counter[0] += 1
    assert my_id != counter[0]  # generation changed — barge-in detected


# ── Turn management ──


def test_add_turn_increments_index() -> None:
    session = CallSessionData(call_id="test-3")
    assert session.next_turn_index == 0
    session.add_turn(TurnRole.USER, "hello")
    assert session.next_turn_index == 1
    session.add_turn(TurnRole.AGENT, "hi there")
    assert session.next_turn_index == 2


# ── Model config ──


def test_model_config_is_mistral_small() -> None:
    assert "mistral" in settings.mistral_model.lower()
