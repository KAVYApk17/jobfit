from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    llm_model: str = "claude-opus-5-5"

    jwt_secret: str = "change-me"
    jwt_ttl_minutes: int = 60

    database_url: str = "postgresql+psycopg://jobfit:jobfit@localhost:5432/jobfit"
    broker_url: str = "amqp://guest:guest@localhost:5672//"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    daily_analysis_limit: int = 20

    max_upload_bytes: int = 5 * 1024 * 1024
    cors_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
