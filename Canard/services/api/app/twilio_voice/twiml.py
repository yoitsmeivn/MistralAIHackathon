# pyright: basic, reportMissingImports=false
from __future__ import annotations

from typing import Any, cast

from twilio.twiml.voice_response import VoiceResponse

from app.config import settings


def _ws_base_url() -> str:
    """Convert the public HTTP(S) base URL to WS(S) for Twilio Media Streams.

    Examples:
        https://abc.ngrok.io  → wss://abc.ngrok.io
        http://localhost:8000  → ws://localhost:8000
    """
    base = settings.public_base_url.rstrip("/")
    if base.startswith("https://"):
        return "wss://" + base[8:]
    if base.startswith("http://"):
        return "ws://" + base[7:]
    return base


# ---------------------------------------------------------------------------
# TwiML response builders
# ---------------------------------------------------------------------------


def stream_response(call_id: str) -> str:
    """TwiML: open a bidirectional Media Stream immediately.

    NO <Say> element — the greeting is delivered as ElevenLabs TTS audio
    directly over the WebSocket after the stream starts.  This ensures
    the callee's FIRST audible experience is the ElevenLabs voice, not
    Twilio's built-in TTS engine.

    Uses ``<Connect><Stream>`` with nested ``<Parameter>`` elements to
    pass metadata (call_id) to the WebSocket handler.

    IMPORTANT per Twilio docs: the ``<Stream>`` ``url`` attribute does
    **not** support query-string parameters.  Custom key-value pairs
    must use the ``<Parameter>`` TwiML noun.

    Produces TwiML like::

        <Response>
          <Connect>
            <Stream url="wss://host/twilio/stream">
              <Parameter name="call_id" value="…" />
            </Stream>
          </Connect>
        </Response>

    Refs:
        https://www.twilio.com/docs/voice/twiml/stream
        https://www.twilio.com/docs/voice/twiml/stream#custom-parameters
    """
    response = VoiceResponse()

    connect = response.connect()
    stream = cast(Any, connect).stream(url=f"{_ws_base_url()}/twilio/stream")
    # Pass call metadata as <Parameter> — NOT as query-string parameters.
    cast(Any, stream).parameter(name="call_id", value=call_id)

    return str(response)


def error_hangup(text: str) -> str:
    """TwiML: say an error message and hang up.

    This is used ONLY for unrecoverable error conditions (e.g. call record
    not found).  It is NOT used for agent speech — all agent speech goes
    through ElevenLabs TTS over the Media Stream WebSocket.
    """
    response = VoiceResponse()
    response.say(text, voice="alice")
    response.hangup()
    return str(response)
