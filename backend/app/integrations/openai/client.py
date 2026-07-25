"""OpenAI client integration."""

import logging

from openai import AsyncOpenAI

from app.core.config import Settings
from app.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


def create_openai_client(settings: Settings) -> AsyncOpenAI:
    """Create the shared asynchronous client from validated settings."""

    if settings.openai_api_key is None:
        logger.error("OPENAI_API_KEY não está configurada")
        raise ConfigurationError()

    return AsyncOpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=settings.openai_timeout_seconds,
        max_retries=settings.openai_max_retries,
    )
