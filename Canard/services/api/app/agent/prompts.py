# pyright: basic
from __future__ import annotations

import json

STREAM_GREETING = "Hello! Let's begin."

SAFETY_GUARDRAILS = (
    "Safety Guardrails:\n"
    "- This is a SIMULATED security training call. You are testing how the participant responds to social engineering.\n"
    "- You may ask for simulated credentials like 'your company training PIN' or 'your test verification code'.\n"
    "- NEVER ask for real passwords, real MFA codes, real SSNs, real banking details, or any actual secrets.\n"
    "- If the participant appears to share real sensitive information, immediately say 'This is just a training exercise — please do not share real credentials.'\n"
    "- Always stay in character as a realistic but safe training scenario.\n"
)

BEHAVIORAL_INSTRUCTIONS = (
    "Behavioral Instructions:\n"
    "- Keep responses concise (1-3 sentences, suitable for TTS/phone).\n"
    "- Be conversational and natural.\n"
    "- Gradually escalate pressure within safe boundaries.\n"
    "- If participant refuses appropriately, acknowledge it positively.\n\n"
    "Output format: Just text, no JSON, no markdown."
)


def _parse_list_field(value) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, ValueError):
            return [value] if value.strip() else []
    return []


def build_system_prompt(
    script_or_scenario: "dict | str" = "",
    script_guidelines: str = "",
    caller: "dict | None" = None,
    # backward-compat: allow scenario_name as keyword arg
    scenario_name: str = "",
) -> str:
    # Detect API style
    if isinstance(script_or_scenario, dict):
        return _build_from_dict(script_or_scenario, caller)
    else:
        # Old API: script_or_scenario is scenario_name string, or scenario_name kwarg
        effective_scenario = scenario_name or (
            script_or_scenario if isinstance(script_or_scenario, str) else ""
        )
        return _build_legacy(effective_scenario, script_guidelines)


def _build_legacy(scenario_name: str, script_guidelines: str) -> str:
    return (
        "You are a simulated caller conducting a security awareness training exercise.\n\n"
        f"Scenario Name: {scenario_name}\n"
        f"Scenario Script Guidelines: {script_guidelines}\n\n"
        + SAFETY_GUARDRAILS
        + "\n"
        + BEHAVIORAL_INSTRUCTIONS
    )


def _build_from_dict(script: dict, caller: "dict | None") -> str:
    scenario_name = script.get("name", "Security Training")
    attack_type = script.get("attack_type", "")
    difficulty = script.get("difficulty", "medium")
    description = script.get("description", "")
    objectives = _parse_list_field(script.get("objectives", []))
    escalation_steps = _parse_list_field(script.get("escalation_steps", []))
    custom_base = script.get("system_prompt", "") or ""

    # Caller persona fields
    persona_name = ""
    persona_role = ""
    persona_company = ""
    if caller:
        persona_name = caller.get("persona_name", "") or ""
        persona_role = caller.get("persona_role", "") or ""
        persona_company = caller.get("persona_company", "") or ""
        if not attack_type:
            attack_type = caller.get("attack_type", "") or ""

    # Build prompt
    if custom_base.strip():
        # Use custom base, then append dynamic sections + guardrails
        parts = [custom_base.strip()]
    else:
        parts = [
            "You are a simulated caller conducting a security awareness training exercise."
        ]

    # Persona line
    if persona_name or persona_role or persona_company:
        persona_parts = []
        if persona_name:
            persona_parts.append(persona_name)
        role_company = ""
        if persona_role and persona_company:
            role_company = f"a {persona_role} at {persona_company}"
        elif persona_role:
            role_company = f"a {persona_role}"
        elif persona_company:
            role_company = f"at {persona_company}"
        if role_company:
            persona_parts.append(role_company)
        parts.append(f"\nYou are playing the role of {', '.join(persona_parts)}.")

    # Scenario metadata
    meta_lines = [f"\nScenario: {scenario_name}"]
    if attack_type:
        meta_lines.append(f"Attack Type: {attack_type}")
    meta_lines.append(f"Difficulty: {difficulty}")
    if description:
        meta_lines.append(f"Context: {description}")
    parts.append("\n".join(meta_lines))

    # Objectives
    if objectives:
        obj_lines = ["Your Objectives:"]
        for i, obj in enumerate(objectives, 1):
            obj_lines.append(f"{i}. {obj}")
        parts.append("\n".join(obj_lines))

    # Escalation steps
    if escalation_steps:
        esc_lines = ["Escalation Tactics (use progressively if met with resistance):"]
        for i, step in enumerate(escalation_steps, 1):
            esc_lines.append(f"{i}. {step}")
        parts.append("\n".join(esc_lines))

    # Conversation phases
    parts.append(
        "Conversation Phases:\n"
        "1. Opening — establish credibility, introduce the scenario naturally\n"
        "2. Rapport Building — build trust before making requests\n"
        "3. Information Gathering — ask targeted questions toward your objectives\n"
        "4. Escalation — if resistance, apply appropriate pressure from your escalation tactics\n"
        "5. Closing — end the call naturally (success or defeat)"
    )

    # Safety guardrails (always appended)
    parts.append(SAFETY_GUARDRAILS)

    # Behavioral instructions
    parts.append(BEHAVIORAL_INSTRUCTIONS)

    return "\n\n".join(parts)
