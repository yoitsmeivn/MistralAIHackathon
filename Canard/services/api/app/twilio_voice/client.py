# pyright: basic, reportMissingImports=false
from __future__ import annotations

from twilio.rest import Client

from app.config import settings


def get_twilio_client() -> Client:
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are required")
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)


def make_outbound_call(
    to_number: str, webhook_url: str, status_callback_url: str
) -> str:
    client = get_twilio_client()
    call = client.calls.create(
        to=to_number,
        from_=settings.twilio_from_number,
        url=webhook_url,
        status_callback=status_callback_url,
        status_callback_event=["initiated", "ringing", "answered", "completed"],
        status_callback_method="POST",
        method="POST",
        record=True,
    )
    return call.sid
