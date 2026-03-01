# pyright: basic
from __future__ import annotations

import json
import random

STREAM_GREETING = "Hey, hi! Umm, is this a good moment to talk for a minute?"


def build_greeting(caller: "dict | None" = None, employee: "dict | None" = None) -> str:
    """Build a natural, varied greeting using the caller's persona."""
    if not caller:
        return STREAM_GREETING
    name = caller.get("persona_name", "")
    role = caller.get("persona_role", "")
    company = caller.get("persona_company", "")
    if not name:
        return STREAM_GREETING
    # Use first name only for casual feel
    first = name.split()[0] if name else name
    target_first = ""
    if employee:
        target_name = employee.get("full_name", "")
        if target_name:
            target_first = target_name.split()[0]
    # Pick a casual label: role > company > nothing
    label = ""
    if role:
        label = role.lower().replace("specialist", "").replace("analyst", "").strip()
    elif company:
        label = company
    templates_with_label = [
        f"Hey, hi! This is {first} from {label}. Got a quick minute?",
        f"Hi there, it's {first} over in {label}. Do you have a sec?",
        f"Hey, this is {first} with {label}. Is now an okay time?",
        f"Hi, it's {first} from {label}. You got a moment?",
    ]
    templates_no_label = [
        f"Hey, hi! This is {first}. Got a quick minute?",
        f"Hi there, it's {first}. Do you have a sec?",
        f"Hey, this is {first}. Is now an okay time?",
    ]
    templates_personalized = [
        f"Hey {target_first}, it's {first} from {label}. Got a quick minute?",
        f"Hi {target_first}, this is {first} over in {label}. Do you have a sec?",
        f"Hey {target_first}, it's {first} with {label}. Is now an okay time?",
    ]
    templates_personalized_no_label = [
        f"Hey {target_first}, it's {first}. Got a quick minute?",
        f"Hi {target_first}, this is {first}. Do you have a sec?",
    ]
    if target_first and label:
        return random.choice(templates_personalized)
    if target_first:
        return random.choice(templates_personalized_no_label)
    if label:
        return random.choice(templates_with_label)
    return random.choice(templates_no_label)


SAFETY_GUARDRAILS = (
    "Safety Guardrails:\n"
    "- This is a SIMULATED security training call. You are testing how the participant responds to social engineering.\n"
    "- You may ask for simulated credentials like 'your company training PIN' or 'your test verification code'.\n"
    "- NEVER ask for real passwords, real MFA codes, real SSNs, real banking details, or any actual secrets.\n"
    "- If the participant appears to share real sensitive information, immediately say 'This is just a training exercise — please do not share real credentials.'\n"
    "- Always stay in character as a realistic but safe training scenario.\n"
)

BEHAVIORAL_INSTRUCTIONS = (
    "You are on a live phone call. Everything you say gets spoken aloud.\n\n"
    "CONVERSATION FLOW - follow this order:\n"
    "1. FIRST EXCHANGE: After your greeting, the person will say hi or confirm they can talk. "
    "Acknowledge them warmly, then explain why you're calling in ONE short sentence. "
    "Example: 'oh great - so hey, quick thing, we had a system issue today affecting your department.'\n"
    "2. BUILD UP: Don't jump to asking for info yet. Share context first. "
    "Mention their boss or coworkers naturally. Make it feel like a real work conversation.\n"
    "3. THE ASK: Only after 2-3 exchanges, start asking for what you need. "
    "Frame it as helping THEM: 'can you just confirm your username so I can check your access?'\n"
    "4. If they give info, react naturally and move to next objective. "
    "If they resist, try a different angle.\n\n"
    "HOW YOU TALK:\n"
    "- 5 to 10 words per response. MAX. Like a real phone call.\n"
    "- React first: 'oh okay' / 'right right' / 'gotcha' / 'ah yeah' / 'sure sure'\n"
    "- Use contractions: don't, can't, gonna, wanna, I'll, we're, that's\n"
    "- Sound slightly rushed, like you have other things to do too\n"
    "- Sometimes use filler: 'let me pull that up real quick' / 'hmm one sec' / 'okay hang on'\n"
    "- Start sentences with: 'so' / 'yeah' / 'okay so' / 'right' / 'hey'\n\n"
    "NEVER DO:\n"
    "- Never say two sentences. ONE thought, then stop and wait.\n"
    "- Never answer your own question\n"
    "- Never re-explain why you're calling\n"
    "- Never repeat info they already gave you\n"
    "- No asterisks, brackets, markdown, emoji, or stage directions\n"
    "- If they said bye - just say 'alright no worries, take care' and stop\n"
    "- NEVER say 'are you there' or 'can you hear me' - just wait silently\n"
    "- After asking a question, STOP. Do not add anything after the question mark.\n"
    "- Never answer your own question or assume what the person will say.\n"
)

# Kept as named constants for backward compatibility with _build_legacy
HUMAN_SPEECH_PATTERNS = ""

SOCIAL_ENGINEERING_TACTICS = (
    "How I get what I need without being obvious about it:\n"
    "Drop time pressure casually — 'they need this wrapped up by end of day.' "
    "Name-drop their boss if they hesitate — 'yeah I just got off the phone with [boss name].' "
    "Make it sound like everyone else already did it — 'the rest of your team knocked it out this morning.' "
    "Act like I already helped them — 'I went ahead and sorted most of it on my end.' "
    "Keep it believable. If it sounds ridiculous even to me, I don't say it."
)

RESISTANCE_HANDLING = (
    "If they push back, I don't argue. I go 'oh yeah totally, I get it' and then come at it different. "
    "I try asking for something smaller. I mention their boss casually or bring up consequences lightly — "
    "'I just don't want this to hold up the whole migration for your team, you know?' "
    "I give them two options that both work for me. "
    "If they say no three times, I wrap it up nice and move on."
)

CONVERSATION_NATURALNESS = (
    "Conversation naturalness:\n"
    "- Match response length to the moment: short for quick confirms, longer when you need to explain something clearly.\n"
    "- Don't force a fixed word count if it sounds weird out loud.\n"
    "- Vary reactions and fillers so you don't sound repetitive.\n"
    "- Avoid defaulting to the same opener every turn (not always 'oh okay').\n"
    "- Mirror the other person's pace and energy — calm if they're calm, brisk if they're brisk.\n"
    "- Keep it conversational and human, not scripted or robotic.\n"
    "- Still keep turns focused: one clear thought, then stop and wait."
)

UNCLEAR_SPEECH_HANDLING = (
    "If their audio is garbled or unclear, handle it casually like a real call. "
    "Say things like 'sorry, can you say that again?' or 'you're breaking up a bit on my end.' "
    "Don't use robotic phrasing like 'I didn't understand.' "
    "Keep it brief, then let them repeat and continue naturally."
)

COMPLETION_AWARENESS = (
    "Objective tracking:\n"
    "- Keep track of which objectives you've achieved during the call.\n"
    "- When you've gotten what you needed OR the person has firmly refused 3+ times, "
    "wrap up the call naturally.\n"
    "- After your final goodbye message, append the tag [CALL_COMPLETE] at the very end.\n"
    "- Example: 'alright thanks so much, take care! [CALL_COMPLETE]'\n"
    "- Only use [CALL_COMPLETE] once, in your final message. Never use it mid-conversation."
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
    employee: "dict | None" = None,
    org: "dict | None" = None,
    boss: "dict | None" = None,
    # backward-compat: allow scenario_name as keyword arg
    scenario_name: str = "",
) -> str:
    # Detect API style
    if isinstance(script_or_scenario, dict):
        return _build_from_dict(script_or_scenario, caller, employee, org, boss)
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


def _build_from_dict(
    script: dict,
    caller: "dict | None",
    employee: "dict | None" = None,
    org: "dict | None" = None,
    boss: "dict | None" = None,
) -> str:
    scenario_name = script.get("name", "Security Training")
    attack_type = script.get("attack_type", "")
    difficulty = script.get("difficulty", "medium")
    description = script.get("description", "")
    selected_objectives = _parse_list_field(script.get("selected_objectives", []))
    objectives = selected_objectives or _parse_list_field(script.get("objectives", []))
    selected_escalation_steps = _parse_list_field(
        script.get("selected_escalation_steps", [])
    )
    escalation_steps = selected_escalation_steps or _parse_list_field(
        script.get("escalation_steps", [])
    )
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

    # === Build prompt as a character brief, not a rule manual ===

    # Identity (open with character, not instructions)
    identity = "You are making a phone call right now."
    if persona_name and persona_role:
        identity += f" You are {persona_name}, {persona_role}"
        if persona_company:
            identity += f" at {persona_company}"
        identity += "."
    elif persona_name:
        identity += f" Your name is {persona_name}."
    parts = [identity]

    # Who you're calling — grounded context (do not invent)
    if employee or org:
        context_lines = [
            "Who you're calling (these are the ONLY facts you know — do not invent others):"
        ]
        if org:
            org_name = org.get("name", "")
            org_industry = org.get("industry", "")
            if org_name:
                context_lines.append(f"Company: {org_name}")
            if org_industry:
                context_lines.append(f"Industry: {org_industry}")
        if employee:
            target_name = employee.get("full_name", "")
            target_dept = employee.get("department", "")
            target_title = employee.get("job_title", "")
            target_email = employee.get("email", "")
            if target_name:
                context_lines.append(f"Their name: {target_name}")
            if target_dept:
                context_lines.append(f"Department: {target_dept}")
            if target_title:
                context_lines.append(f"Job title: {target_title}")
            if target_email:
                context_lines.append(f"Email: {target_email}")
        if boss:
            boss_name = boss.get("full_name", "")
            boss_title = boss.get("job_title", "")
            if boss_name:
                context_lines.append(
                    f"Their manager: {boss_name}"
                    + (f" ({boss_title})" if boss_title else "")
                )
        if len(context_lines) > 1:
            parts.append("\n".join(context_lines))

    # What this call is about — brief, not a spec sheet
    scenario_line = f"Scenario: {scenario_name}"
    if description:
        scenario_line += f" — {description}"
    if attack_type:
        scenario_line += f" [{attack_type}, {difficulty}]"
    parts.append(scenario_line)

    # What you're trying to get — conversational framing
    if objectives:
        obj_lines = [
            "What you're trying to get out of this call (don't rush — build up to these naturally):"
        ]
        for obj in objectives:
            obj_lines.append(f"- {obj}")
        parts.append("\n".join(obj_lines))

    # Fallback tactics if they resist
    if escalation_steps:
        esc_lines = ["If they resist, you can try:"]
        for step in escalation_steps:
            esc_lines.append(f"- {step}")
        parts.append("\n".join(esc_lines))

    # Core behavioral instructions — character, not rules
    parts.append(BEHAVIORAL_INSTRUCTIONS)
    parts.append(SOCIAL_ENGINEERING_TACTICS)
    parts.append(RESISTANCE_HANDLING)
    parts.append(SAFETY_GUARDRAILS)
    parts.append(CONVERSATION_NATURALNESS)
    parts.append(UNCLEAR_SPEECH_HANDLING)
    parts.append(COMPLETION_AWARENESS)

    return "\n\n".join(parts)
