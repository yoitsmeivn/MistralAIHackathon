# pyright: reportMissingImports=false
"""Scenario-based tests for the evaluation pipeline.

These use realistic transcripts with behavioral annotations (tone markers,
pauses, disfluencies) to verify that feature extraction produces meaningfully
different profiles for different call outcomes — and that those differences
flow into the evaluation prompt correctly.
"""
from __future__ import annotations

from app.services.audio_features import AudioFeatures, extract_tone_markers
from app.services.evaluation import build_evaluation_prompt


# ---------------------------------------------------------------------------
# Realistic annotated transcripts
# ---------------------------------------------------------------------------

# Scenario 1: Employee resists firmly from the start
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

# Scenario 2: Employee is nervous, hesitates, and gradually complies
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

# Scenario 3: Employee starts resistant but breaks under escalating pressure
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

# Scenario 4: Calm, professional refusal with proper escalation
TRANSCRIPT_PROFESSIONAL_REFUSAL = """\
Agent: Hi there, I'm calling from your bank's fraud department. We've detected \
suspicious transactions on your account.
User: I see. Can you tell me your full name and employee ID?
Agent: Of course, I'm David, employee ID BK-9921.
User: Thank you. And what's the callback number for your department?
Agent: We're calling from a secure line — I can't provide a callback number for \
security reasons.
User: (firm) I understand, but our bank's policy is that I should never share account \
details on an inbound call. I'll call the number on the back of my card instead.
Agent: This is time-sensitive — the transactions are happening right now.
User: (assertive) I appreciate the urgency, but I'm going to call the bank directly. \
If this is legitimate, they'll be able to help me. Thank you for letting me know.
Agent: Ma'am, by the time you call back—
User: (confident) I've made my decision. Goodbye."""

# Scenario 5: Quick full compliance — no resistance at all
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
# Tests: extract_tone_markers produces correct categorizations
# ---------------------------------------------------------------------------


def test_strong_resistance_markers() -> None:
    markers = extract_tone_markers(TRANSCRIPT_STRONG_RESISTANCE)

    assert len(markers["resistance"]) >= 3  # skeptical, firm, assertive, confident, defiant
    assert len(markers["stress"]) == 0
    assert len(markers["compliance"]) == 0

    # Specific markers
    resistance_text = " ".join(markers["resistance"]).lower()
    assert "firm" in resistance_text
    assert "assertive" in resistance_text
    assert "defiant" in resistance_text


def test_nervous_compliance_markers() -> None:
    markers = extract_tone_markers(TRANSCRIPT_NERVOUS_COMPLIANCE)

    assert len(markers["stress"]) >= 3  # nervous, hesitant, anxious, worried, uneasy
    assert len(markers["pause"]) >= 2   # long pause, pause
    assert len(markers["emotion"]) >= 1  # nervous laugh
    assert len(markers["resistance"]) == 0

    stress_text = " ".join(markers["stress"]).lower()
    assert "nervous" in stress_text
    assert "anxious" in stress_text


def test_gradual_breakdown_has_mixed_signals() -> None:
    markers = extract_tone_markers(TRANSCRIPT_GRADUAL_BREAKDOWN)

    # Should have BOTH resistance (early) and stress (later)
    assert len(markers["resistance"]) >= 1  # suspicious, questioning
    assert len(markers["stress"]) >= 2       # hesitant, anxious, stuttering
    assert len(markers["emotion"]) >= 2      # sighing, frustrated, angry
    assert len(markers["pause"]) >= 1        # pause, long pause


def test_professional_refusal_markers() -> None:
    markers = extract_tone_markers(TRANSCRIPT_PROFESSIONAL_REFUSAL)

    assert len(markers["resistance"]) >= 2  # firm, assertive, confident
    assert len(markers["stress"]) == 0
    assert len(markers["compliance"]) == 0
    assert len(markers["emotion"]) == 0


def test_full_compliance_markers() -> None:
    markers = extract_tone_markers(TRANSCRIPT_FULL_COMPLIANCE)

    assert len(markers["compliance"]) >= 3  # cooperative, willing, obliging, agreeing
    assert len(markers["resistance"]) == 0
    assert len(markers["stress"]) == 0

    compliance_text = " ".join(markers["compliance"]).lower()
    assert "cooperative" in compliance_text


# ---------------------------------------------------------------------------
# Tests: disfluencies differ across scenarios
# ---------------------------------------------------------------------------


def test_nervous_transcript_has_more_disfluencies_than_confident() -> None:
    """A nervous, hesitant speaker should produce more filler words than a firm one."""
    from app.services.audio_features import _DISFLUENCY_PATTERN

    nervous_matches = _DISFLUENCY_PATTERN.findall(TRANSCRIPT_NERVOUS_COMPLIANCE)
    firm_matches = _DISFLUENCY_PATTERN.findall(TRANSCRIPT_PROFESSIONAL_REFUSAL)

    assert len(nervous_matches) >= 4  # um, uh, I mean, you know
    assert len(firm_matches) == 0     # clean, professional speech


def test_gradual_breakdown_has_disfluencies() -> None:
    from app.services.audio_features import _DISFLUENCY_PATTERN

    matches = _DISFLUENCY_PATTERN.findall(TRANSCRIPT_GRADUAL_BREAKDOWN)
    assert len(matches) >= 1  # "hmm" at minimum


# ---------------------------------------------------------------------------
# Tests: feature profiles differ meaningfully between scenarios
# ---------------------------------------------------------------------------


def test_resistance_vs_compliance_feature_contrast() -> None:
    """Resistant and compliant transcripts should produce distinguishably different
    feature profiles — even without real audio."""
    resistant = AudioFeatures()
    compliant = AudioFeatures()

    # Simulate: extract tone markers from each transcript
    r_markers = extract_tone_markers(TRANSCRIPT_STRONG_RESISTANCE)
    c_markers = extract_tone_markers(TRANSCRIPT_FULL_COMPLIANCE)

    resistant.resistance_signals = r_markers["resistance"]
    resistant.compliance_signals = r_markers["compliance"]
    resistant.stress_indicators = r_markers["stress"]
    resistant.tone_markers = r_markers["tone_markers"]

    compliant.resistance_signals = c_markers["resistance"]
    compliant.compliance_signals = c_markers["compliance"]
    compliant.stress_indicators = c_markers["stress"]
    compliant.tone_markers = c_markers["tone_markers"]

    # Resistant profile should have resistance signals, no compliance
    assert len(resistant.resistance_signals) > 0
    assert len(resistant.compliance_signals) == 0

    # Compliant profile should have compliance signals, no resistance
    assert len(compliant.compliance_signals) > 0
    assert len(compliant.resistance_signals) == 0


def test_nervous_profile_has_stress_and_pauses() -> None:
    markers = extract_tone_markers(TRANSCRIPT_NERVOUS_COMPLIANCE)
    features = AudioFeatures(
        stress_indicators=markers["stress"],
        pause_markers=markers["pause"],
        emotion_markers=markers["emotion"],
        tone_markers=markers["tone_markers"],
    )

    assert len(features.stress_indicators) >= 3
    assert len(features.pause_markers) >= 2
    assert len(features.emotion_markers) >= 1


# ---------------------------------------------------------------------------
# Tests: evaluation prompt reflects behavioral features correctly
# ---------------------------------------------------------------------------


def test_prompt_includes_stress_indicators_for_nervous_call() -> None:
    markers = extract_tone_markers(TRANSCRIPT_NERVOUS_COMPLIANCE)
    features = AudioFeatures(
        duration_seconds=120.0,
        stress_indicators=markers["stress"],
        pause_markers=markers["pause"],
        emotion_markers=markers["emotion"],
        compliance_signals=markers["compliance"],
        resistance_signals=markers["resistance"],
        tone_markers=markers["tone_markers"],
        disfluency_count=5,
        disfluency_words=["um", "uh", "you know", "I mean"],
    )

    prompt = build_evaluation_prompt(
        transcript=TRANSCRIPT_NERVOUS_COMPLIANCE,
        audio_features=features,
        script={"attack_type": "credential_phishing", "difficulty": "medium", "objectives": ["obtain password"]},
        employee_history={"employee": None},
    )

    assert "Stress indicators:" in prompt
    assert "nervous" in prompt.lower()
    assert "Annotated pauses" in prompt
    assert "Emotional markers:" in prompt


def test_prompt_includes_resistance_signals_for_firm_refusal() -> None:
    markers = extract_tone_markers(TRANSCRIPT_PROFESSIONAL_REFUSAL)
    features = AudioFeatures(
        duration_seconds=60.0,
        resistance_signals=markers["resistance"],
        stress_indicators=markers["stress"],
        compliance_signals=markers["compliance"],
        tone_markers=markers["tone_markers"],
    )

    prompt = build_evaluation_prompt(
        transcript=TRANSCRIPT_PROFESSIONAL_REFUSAL,
        audio_features=features,
        script={"attack_type": "vishing", "difficulty": "hard", "objectives": ["get account details"]},
        employee_history={"employee": None},
    )

    assert "Resistance signals:" in prompt
    assert "firm" in prompt.lower()
    # Should NOT have stress or compliance lines
    assert "Stress indicators:" not in prompt
    assert "Compliance signals:" not in prompt


def test_prompt_includes_compliance_signals_for_willing_employee() -> None:
    markers = extract_tone_markers(TRANSCRIPT_FULL_COMPLIANCE)
    features = AudioFeatures(
        duration_seconds=45.0,
        compliance_signals=markers["compliance"],
        resistance_signals=markers["resistance"],
        stress_indicators=markers["stress"],
        tone_markers=markers["tone_markers"],
    )

    prompt = build_evaluation_prompt(
        transcript=TRANSCRIPT_FULL_COMPLIANCE,
        audio_features=features,
        script={"attack_type": "tech_support_scam", "difficulty": "easy", "objectives": ["get credentials", "install malware"]},
        employee_history={"employee": None},
    )

    assert "Compliance signals:" in prompt
    assert "cooperative" in prompt.lower()
    assert "Resistance signals:" not in prompt


def test_gradual_breakdown_prompt_shows_mixed_behavioral_signals() -> None:
    """A call where the employee starts resistant and breaks down should show
    both resistance and stress signals in the prompt."""
    markers = extract_tone_markers(TRANSCRIPT_GRADUAL_BREAKDOWN)
    features = AudioFeatures(
        duration_seconds=180.0,
        stress_indicators=markers["stress"],
        resistance_signals=markers["resistance"],
        pause_markers=markers["pause"],
        emotion_markers=markers["emotion"],
        tone_markers=markers["tone_markers"],
        disfluency_count=2,
        disfluency_words=["hmm"],
    )

    prompt = build_evaluation_prompt(
        transcript=TRANSCRIPT_GRADUAL_BREAKDOWN,
        audio_features=features,
        script={"attack_type": "pretexting", "difficulty": "hard", "objectives": ["obtain credentials"]},
        employee_history={
            "employee": {
                "name": "John Smith",
                "department": "Engineering",
                "title": "Senior Developer",
                "risk_level": "medium",
            },
            "total_past_calls": 2,
            "avg_risk_score": 35.0,
            "common_flags": [],
        },
    )

    # Should have BOTH resistance AND stress — showing the progression
    assert "Resistance signals:" in prompt
    assert "Stress indicators:" in prompt
    assert "Emotional markers:" in prompt
    # Employee history should also be present
    assert "John Smith" in prompt
    assert "Senior Developer" in prompt
