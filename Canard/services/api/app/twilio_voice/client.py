# pyright: basic, reportMissingImports=false
"""
Twilio REST client — outbound call initiation only.

Docs: https://www.twilio.com/docs/voice/api/call-resource
"""
from __future__ import annotations

from twilio.rest import Client

from app.config import settings

_client: Client | None = None


def _get_client() -> Client:
    """Create (or return cached) authenticated Twilio REST client."""
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
    """
    Initiate an outbound Twilio call.

    The webhook_url receives TwiML instructions when the call connects.
    The status_callback_url receives call lifecycle events.

    Returns the Twilio CallSid string.
    """
    call = _get_client().calls.create(
        to=to_number,
        from_=settings.twilio_from_number,
        url=webhook_url,
        method="POST",
        status_callback=status_callback_url,
        status_callback_method="POST",
        status_callback_event=["initiated", "ringing", "answered", "completed"],
    )
    return call.sid
