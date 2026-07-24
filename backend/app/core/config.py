"""Application configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(
        default="Food Vision API",
        validation_alias="APP_NAME",
    )
    environment: str = Field(
        default="development",
        validation_alias="ENVIRONMENT",
    )
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    api_v1_prefix: str = Field(
        default="/api/v1",
        pattern=r"^/[^/].*[^/]$|^/[A-Za-z0-9_-]+$",
        validation_alias="API_V1_PREFIX",
    )

    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
    )
    openai_vision_model: str = Field(
        default="gpt-4o-mini",
        min_length=1,
        validation_alias="OPENAI_VISION_MODEL",
    )
    openai_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        validation_alias="OPENAI_TIMEOUT_SECONDS",
    )
    openai_max_retries: int = Field(
        default=2,
        ge=0,
        le=10,
        validation_alias="OPENAI_MAX_RETRIES",
    )

    max_image_size_mb: int = Field(
        default=10,
        ge=1,
        validation_alias="MAX_IMAGE_SIZE_MB",
    )
    max_image_dimension: int = Field(
        default=1600,
        ge=1,
        validation_alias="MAX_IMAGE_DIMENSION",
    )
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        validation_alias="CORS_ORIGINS",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            origins = value.split(",")
        elif isinstance(value, list):
            origins = value
        else:
            raise ValueError("CORS_ORIGINS deve ser uma lista ou texto.")

        cleaned = [str(origin).strip() for origin in origins if str(origin).strip()]
        if not cleaned:
            raise ValueError("CORS_ORIGINS não pode ser vazio.")
        return cleaned

    @model_validator(mode="after")
    def validate_production_cors(self) -> "Settings":
        if self.environment.lower() == "production" and "*" in self.cors_origins:
            raise ValueError("CORS_ORIGINS não pode conter '*' em produção.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
