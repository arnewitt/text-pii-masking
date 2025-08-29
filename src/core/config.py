from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load application settings from local .env file."""

    openai_base_url: str
    openai_api_key: str
    openai_model_name: str

    host: str = "0.0.0.0"
    port: int = 8081

    model_config = SettingsConfigDict(env_file=".env")
