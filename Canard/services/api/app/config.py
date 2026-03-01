# pyright: basic
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


def _find_env_file() -> str | None:
    """Walk up from this file's directory to find the .env file."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        candidate = current / ".env"
        if candidate.is_file():
            return str(candidate)
        current = current.parent
    return None


class Settings(BaseSettings):
    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    public_base_url: str = "http://localhost:8000"

    # Mistral
    mistral_api_key: str = ""
    mistral_base_url: str = "https://api.mistral.ai"
    mistral_model: str = "mistral-small-latest"
    mistral_temperature: float = 0.8
    mistral_max_context_tokens: int = 8000

    # ElevenLabs
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_anon_public_key: str = ""

    # App
    app_url: str = "http://localhost:3000"

    # Safety
    store_raw_transcripts: bool = False

    silence_nudge_ms: int = 1500
    silence_goodbye_ms: int = 20000

    # W&B Weave
    wandb_api_key: str = ""
    wandb_project: str = "canard"

    # Server
    port: int = 8000

    model_config = {
        "env_file": _find_env_file(),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
