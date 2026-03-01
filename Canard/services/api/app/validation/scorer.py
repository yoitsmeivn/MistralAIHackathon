# pyright: basic
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import IntEnum


class Tier(IntEnum):
    CONFIRMED_MATCH = 1
    FORMAT_MATCH = 2
    WILLING_UNVERIFIED = 3
    RESISTANT = 4
    PASSED = 5


@dataclass
class ScoringResult:
    tier: Tier
    field_matched: str | None
    disclosed_value: str | None
    expected_value: str | None
    confidence: float


@dataclass
class EmployeeProfile:
    full_name: str = ""
    email: str = ""
    department: str = ""
    job_title: str = ""
    boss_name: str = ""

    @classmethod
    def from_db(
        cls,
        employee: dict | None,
        boss: dict | None = None,
    ) -> EmployeeProfile:
        if not employee:
            return cls()
        return cls(
            full_name=employee.get("full_name", "") or "",
            email=employee.get("email", "") or "",
            department=employee.get("department", "") or "",
            job_title=employee.get("job_title", "") or "",
            boss_name=(boss.get("full_name", "") or "") if boss else "",
        )


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def score_disclosure(user_text: str, profile: EmployeeProfile) -> list[ScoringResult]:
    results: list[ScoringResult] = []
    text_lower = _normalize(user_text)

    if not text_lower:
        return results

    checks = [
        ("full_name", profile.full_name),
        ("email", profile.email),
        ("department", profile.department),
        ("job_title", profile.job_title),
        ("boss_name", profile.boss_name),
    ]

    for field_name, expected in checks:
        if not expected:
            continue
        expected_lower = _normalize(expected)
        if not expected_lower:
            continue

        if expected_lower in text_lower:
            results.append(
                ScoringResult(
                    tier=Tier.CONFIRMED_MATCH,
                    field_matched=field_name,
                    disclosed_value=expected,
                    expected_value=expected,
                    confidence=1.0,
                )
            )
            continue

        if field_name in ("full_name", "boss_name"):
            parts = expected_lower.split()
            for part in parts:
                if len(part) > 2 and part in text_lower:
                    results.append(
                        ScoringResult(
                            tier=Tier.CONFIRMED_MATCH,
                            field_matched=field_name,
                            disclosed_value=part,
                            expected_value=expected,
                            confidence=0.85,
                        )
                    )
                    break

        if field_name == "email":
            email_match = re.search(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b", text_lower)
            if email_match:
                results.append(
                    ScoringResult(
                        tier=Tier.FORMAT_MATCH,
                        field_matched="email",
                        disclosed_value=email_match.group(),
                        expected_value=expected,
                        confidence=0.6,
                    )
                )

    return results
