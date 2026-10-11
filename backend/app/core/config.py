from functools import lru_cache
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "InsightFlow Backend"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite:///./insightflow.db"

    # CORS
    FRONTEND_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    ]

    # Limits
    MAX_UPLOAD_MB: int = 25
    MAX_CSV_ROWS: int = 50000

    # Priority Scoring Defaults
    PRIORITY_WEIGHT_IMPACT: float = 0.30
    PRIORITY_WEIGHT_URGENCY: float = 0.25
    PRIORITY_WEIGHT_TREND: float = 0.20
    PRIORITY_WEIGHT_EVIDENCE: float = 0.15
    PRIORITY_WEIGHT_RECENCY: float = 0.10

    # AI Provider
    AI_PROVIDER: str = "template"
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o-mini"

    # Adaption Labs
    ADAPTION_ENABLED: bool = False
    ADAPTION_API_KEY: str = ""

    @field_validator("FRONTEND_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in ("production", "prod")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
