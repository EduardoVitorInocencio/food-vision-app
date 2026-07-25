"""Tests for environment-backed settings."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_cors_origins_accept_comma_separated_environment_value() -> None:
    """Parse and trim comma-separated CORS origins."""

    settings = Settings(CORS_ORIGINS="http://localhost:3000, https://example.com")

    assert settings.cors_origins == [
        "http://localhost:3000",
        "https://example.com",
    ]


def test_production_rejects_wildcard_cors() -> None:
    """Reject wildcard CORS when the environment is production."""

    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="production", CORS_ORIGINS="*")
