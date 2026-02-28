# pyright: basic, reportMissingImports=false

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mistral_api_key: str = ""
    mistral_base_url: str = "https://api.mistral.ai"
    mistral_model: str = "mistral-small-latest"
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    port: int = 3001

    model_config = {"env_file": "../../.env", "env_file_encoding": "utf-8"}


settings = Settings()
