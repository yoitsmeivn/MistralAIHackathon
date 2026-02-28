# pyright: basic, reportMissingImports=false
from __future__ import annotations

from twilio.twiml.voice_response import VoiceResponse

from app.agent.prompts import CONSENT_CONFIRMED, CONSENT_INTRO
from app.config import settings


def consent_gather_response() -> str:
    response = VoiceResponse()
    gather = response.gather(
        input="speech dtmf",
        action=f"{settings.public_base_url}/twilio/gather",
        method="POST",
        timeout=10,
        num_digits=1,
        speech_timeout="auto",
    )
    gather.say(CONSENT_INTRO, voice="alice")
    response.say("We didn't receive a response. Goodbye.", voice="alice")
    return str(response)


def play_audio_and_gather(audio_url: str) -> str:
    response = VoiceResponse()
    gather = response.gather(
        input="speech",
        action=f"{settings.public_base_url}/twilio/gather",
        method="POST",
        timeout=8,
        speech_timeout="auto",
    )
    gather.play(audio_url)
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
    gather2.say("Are you still there?", voice="alice")
    return str(response)


def say_and_hangup(text: str) -> str:
    response = VoiceResponse()
    response.say(text, voice="alice")
    response.hangup()
    return str(response)


def consent_confirmed_and_first_turn(audio_url: str) -> str:
    response = VoiceResponse()
    response.say(CONSENT_CONFIRMED, voice="alice")
    gather = response.gather(
        input="speech",
        action=f"{settings.public_base_url}/twilio/gather",
        method="POST",
        timeout=8,
        speech_timeout="auto",
    )
    gather.play(audio_url)
    return str(response)
