from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load application settings from local .env file."""

    openai_base_url: str = "placeholder"
    openai_api_key: str = "placeholder"
    openai_model_name: str = "placeholder"

    host: str = "0.0.0.0"
    port: int = 8081

    model_config = SettingsConfigDict(env_file=".env")
