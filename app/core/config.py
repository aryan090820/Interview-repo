from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="KARA_", extra="ignore")

    app_name: str = "Healthcare.ai"
    api_prefix: str = "/api/v1"
    database_url: str
    allowed_origins: list[str] = ["http://localhost:5173"]
    embedding_dim: int = 256
    slot_duration_minutes: int = 30
    clinic_open_hour: int = 9
    clinic_close_hour: int = 17
    max_query_retries: int = 2
    notification_poll_seconds: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
