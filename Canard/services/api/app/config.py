# pyright: basic
from __future__ import annotations

from pydantic_settings import BaseSettings


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

    # ElevenLabs
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # Safety
    store_raw_transcripts: bool = False

    # Server
    port: int = 8000

    model_config = {"env_file": "../../.env", "env_file_encoding": "utf-8"}


settings = Settings()
