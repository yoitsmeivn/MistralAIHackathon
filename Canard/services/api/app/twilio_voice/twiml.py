# pyright: basic, reportMissingImports=false
from __future__ import annotations

from typing import Any, cast

from twilio.twiml.voice_response import VoiceResponse

from app.agent.prompts import STREAM_GREETING
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


def play_audio_and_gather(audio_url: str) -> str:
    """TwiML: play pre-generated audio and gather the caller's speech reply."""
    response = VoiceResponse()
    gather = response.gather(
        input="speech",
        action=f"{settings.public_base_url}/twilio/gather",
        method="POST",
        timeout=8,
        speech_timeout="auto",
    )
    cast(Any, gather).play(audio_url)
    response.say(
        "I didn't hear anything. Let me know if you're still there.", voice="alice"
    )
    gather2 = response.gather(
        input="speech",
        action=f"{settings.public_base_url}/twilio/gather",
        method="POST",
        timeout=8,
        speech_timeout="auto",
    )
    cast(Any, gather2).say("Are you still there?", voice="alice")
    return str(response)


def say_and_hangup(text: str) -> str:
    """TwiML: say a message and hang up."""
    response = VoiceResponse()
    response.say(text, voice="alice")
    response.hangup()
    return str(response)


def stream_response(call_id: str) -> str:
    """TwiML: play a greeting, then open a bidirectional Media Stream.

    Uses ``<Connect><Stream>`` with nested ``<Parameter>`` elements to pass
    metadata (call_id etc.) to the WebSocket handler.

    IMPORTANT per Twilio docs: the ``<Stream>`` ``url`` attribute does **not**
    support query-string parameters.  Custom key-value pairs must use the
    ``<Parameter>`` TwiML noun.  The values arrive in the WebSocket ``start``
    message under ``start.customParameters``.

    The ``<Say>`` executes first (caller hears the greeting), then Twilio opens
    the WebSocket to ``/twilio/stream``.  Twilio does **not** execute any TwiML
    after ``<Connect><Stream>`` while the WebSocket is open.  The call stays
    alive until the server closes the WebSocket (or the caller hangs up).

    Produces TwiML like::

        <Response>
          <Say voice="alice">Thank you for participating…</Say>
          <Connect>
            <Stream url="wss://host/twilio/stream">
              <Parameter name="call_id" value="…" />
            </Stream>
          </Connect>
        </Response>

    Refs:
        https://www.twilio.com/docs/voice/twiml/stream
        https://www.twilio.com/docs/voice/twiml/stream#custom-parameters
        https://www.twilio.com/docs/voice/media-streams/websocket-messages
    """
    response = VoiceResponse()
    # Caller hears this while the WebSocket connection is being established.
    response.say(STREAM_GREETING, voice="alice")

    connect = response.connect()
    stream = cast(Any, connect).stream(url=f"{_ws_base_url()}/twilio/stream")
    # Pass call metadata as <Parameter> — NOT as query-string parameters.
    cast(Any, stream).parameter(name="call_id", value=call_id)

    return str(response)
