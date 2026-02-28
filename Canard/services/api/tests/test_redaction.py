# pyright: reportMissingImports=false
from app.agent.redaction import redact_pii


def test_redacts_email() -> None:
    result = redact_pii("Reach me at alice@example.com")

    assert "[REDACTED_EMAIL]" in result.redacted_text
    assert result.has_sensitive_content is True


def test_redacts_phone() -> None:
    result = redact_pii("Call me at 415-555-2671")

    assert "[REDACTED_PHONE]" in result.redacted_text
    assert result.has_sensitive_content is True


def test_redacts_ssn() -> None:
    result = redact_pii("My SSN is 123-45-6789")

    assert "[REDACTED_SSN]" in result.redacted_text
    assert result.has_sensitive_content is True


def test_redacts_credit_card() -> None:
    result = redact_pii("Use card 4111 1111 1111 1111")

    assert "[REDACTED_CC]" in result.redacted_text
    assert result.has_sensitive_content is True


def test_redacts_password_disclosure() -> None:
    result = redact_pii("My password is hunter2")

    assert "[REDACTED_PASSWORD]" in result.redacted_text
    assert result.has_sensitive_content is True


def test_redacts_otp_code() -> None:
    result = redact_pii("Your OTP code is 123456")

    assert "[REDACTED_CODE]" in result.redacted_text
    assert result.has_sensitive_content is True


def test_clean_text_is_not_sensitive() -> None:
    result = redact_pii("Hello team, this call is about onboarding process updates.")

    assert (
        result.redacted_text
        == "Hello team, this call is about onboarding process updates."
    )
    assert result.has_sensitive_content is False


def test_empty_string_returns_empty_without_sensitive_content() -> None:
    result = redact_pii("")

    assert result.redacted_text == ""
    assert result.original_text == ""
    assert result.has_sensitive_content is False
