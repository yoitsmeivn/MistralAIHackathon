from __future__ import annotations

from fastapi import HTTPException

PUBLIC_DOMAINS: set[str] = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "yahoo.co.uk",
    "yahoo.co.in",
    "outlook.com",
    "hotmail.com",
    "hotmail.co.uk",
    "live.com",
    "msn.com",
    "icloud.com",
    "me.com",
    "mac.com",
    "aol.com",
    "protonmail.com",
    "proton.me",
    "zoho.com",
    "yandex.com",
    "mail.com",
    "gmx.com",
    "gmx.net",
    "fastmail.com",
    "tutanota.com",
    "tuta.io",
    "hey.com",
    "inbox.com",
    "mail.ru",
    "qq.com",
    "163.com",
    "126.com",
    "rediffmail.com",
}


def extract_domain(email: str) -> str:
    """Return the part after '@', lowercased."""
    return email.rsplit("@", 1)[-1].lower()


def is_corporate_email(email: str) -> bool:
    """Return False if the email belongs to a known public provider."""
    return extract_domain(email) not in PUBLIC_DOMAINS


def validate_corporate_email(email: str) -> None:
    """Raise HTTP 400 if the email is from a public provider."""
    if not is_corporate_email(email):
        raise HTTPException(
            status_code=400,
            detail="Please use your corporate email address. Public email providers (Gmail, Yahoo, etc.) are not allowed.",
        )
