# pyright: basic
"""
Twilio REST client — outbound call initiation only.

Docs: https://www.twilio.com/docs/voice/api/call-resource
"""
from __future__ import annotations

from twilio.rest import Client

from app.config import settings


def _client() -> Client:
    """Create an authenticated Twilio REST client from settings."""
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)


def make_outbound_call(
    to_number: str,
    webhook_url: str,
    status_callback_url: str,
) -> str:
    """
    Initiate an outbound Twilio call.

    The webhook_url receives TwiML instructions when the call connects.
    The status_callback_url receives call lifecycle events (completed, etc.).

    Returns the Twilio CallSid string.
    """
    call = _client().calls.create(
        to=to_number,
        from_=settings.twilio_from_number,
        url=webhook_url,
        method="POST",
        status_callback=status_callback_url,
        status_callback_method="POST",
        status_callback_event=["completed"],
    )
    return call.sid
