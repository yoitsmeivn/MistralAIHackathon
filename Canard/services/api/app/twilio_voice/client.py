# pyright: basic, reportMissingImports=false
from __future__ import annotations

from twilio.rest import Client

from app.config import settings

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN required")
        _client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    return _client


def make_outbound_call(
    to_number: str,
    webhook_url: str,
    status_callback_url: str,
) -> str:
    """Place an outbound call via Twilio and return the CallSid."""
    call = _get_client().calls.create(
        to=to_number,
        from_=settings.twilio_from_number,
        url=webhook_url,
        status_callback=status_callback_url,
        status_callback_event=["initiated", "ringing", "answered", "completed"],
    )
    return call.sid
