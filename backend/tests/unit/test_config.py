"""Tests for environment-backed settings."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_cors_origins_accept_comma_separated_environment_value() -> None:
    settings = Settings(CORS_ORIGINS="http://localhost:3000, https://example.com")

    assert settings.cors_origins == [
        "http://localhost:3000",
        "https://example.com",
    ]


def test_production_rejects_wildcard_cors() -> None:
    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="production", CORS_ORIGINS="*")
