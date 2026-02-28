# pyright: basic
from __future__ import annotations

import re
from dataclasses import dataclass

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)"
)
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CC_RE = re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b")
CODE_RE = re.compile(r"(?<!\d)\d{4,8}(?!\d)")
PASSWORD_RE = re.compile(
    r"\b(?:my\s+password\s+is|the\s+password\s+is|password\s*[:=])\s*[^\s,.;]+",
    flags=re.IGNORECASE,
)

PII_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("email", EMAIL_RE, "[REDACTED_EMAIL]"),
    ("phone", PHONE_RE, "[REDACTED_PHONE]"),
    ("ssn", SSN_RE, "[REDACTED_SSN]"),
    ("cc", CC_RE, "[REDACTED_CC]"),
    ("password", PASSWORD_RE, "[REDACTED_PASSWORD]"),
    ("code", CODE_RE, "[REDACTED_CODE]"),
]


@dataclass
class RedactionResult:
    redacted_text: str
    original_text: str
    redactions: list[dict]
    has_sensitive_content: bool


def redact_pii(text: str) -> RedactionResult:
    if not text:
        return RedactionResult(
            redacted_text=text,
            original_text=text,
            redactions=[],
            has_sensitive_content=False,
        )

    all_matches: list[dict[str, int | str]] = []
    for pii_type, pattern, replacement in PII_PATTERNS:
        for match in pattern.finditer(text):
            all_matches.append(
                {
                    "type": pii_type,
                    "start": match.start(),
                    "end": match.end(),
                    "original": match.group(0),
                    "replacement": replacement,
                }
            )

    all_matches.sort(
        key=lambda item: (int(item["start"]), -(int(item["end"]) - int(item["start"])))
    )

    selected: list[dict[str, int | str]] = []
    cursor = -1
    for item in all_matches:
        start = int(item["start"])
        end = int(item["end"])
        if start < cursor:
            continue
        selected.append(item)
        cursor = end

    if not selected:
        return RedactionResult(
            redacted_text=text,
            original_text=text,
            redactions=[],
            has_sensitive_content=False,
        )

    redacted_parts: list[str] = []
    redaction_metadata: list[dict] = []
    pointer = 0
    for item in selected:
        start = int(item["start"])
        end = int(item["end"])
        redacted_parts.append(text[pointer:start])
        redacted_parts.append(str(item["replacement"]))
        pointer = end
        redaction_metadata.append(
            {
                "type": str(item["type"]),
                "start": start,
                "end": end,
                "original": str(item["original"]),
            }
        )

    redacted_parts.append(text[pointer:])

    return RedactionResult(
        redacted_text="".join(redacted_parts),
        original_text=text,
        redactions=redaction_metadata,
        has_sensitive_content=True,
    )
