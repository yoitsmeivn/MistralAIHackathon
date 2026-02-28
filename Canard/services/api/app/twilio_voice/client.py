# pyright: basic
"""
Twilio REST client — outbound call initiation with recording.

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
    recording_callback_url: str = "",
) -> str:
    """
    Initiate an outbound Twilio call with recording enabled.

    The webhook_url receives TwiML instructions when the call connects.
    The status_callback_url receives call lifecycle events.
    The recording_callback_url receives recording completion events.

    Recording is always enabled — Twilio records from answer to hangup.
    The recording URL is delivered via both the status callback and
    the dedicated recording callback for reliability.

    Returns the Twilio CallSid string.
    """
    create_kwargs: dict = {
        "to": to_number,
        "from_": settings.twilio_from_number,
        "url": webhook_url,
        "method": "POST",
        "record": True,
        "status_callback": status_callback_url,
        "status_callback_method": "POST",
        "status_callback_event": ["initiated", "ringing", "answered", "completed"],
    }

    if recording_callback_url:
        create_kwargs["recording_status_callback"] = recording_callback_url
        create_kwargs["recording_status_callback_method"] = "POST"
        create_kwargs["recording_status_callback_event"] = ["completed"]

    call = _client().calls.create(**create_kwargs)
    return call.sid
