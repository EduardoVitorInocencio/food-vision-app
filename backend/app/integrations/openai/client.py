"""OpenAI client integration."""

import logging

from openai import AsyncOpenAI

from app.core.config import Settings
from app.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


def create_openai_client(settings: Settings) -> AsyncOpenAI:
    """Create the shared asynchronous client from validated settings."""

    if settings.openai_api_key is None:
        # Fail fast here instead of letting the first request discover the
        # missing credential deep inside the OpenAI SDK.
        logger.error("OPENAI_API_KEY não está configurada")
        raise ConfigurationError()

    # SecretStr keeps the raw key out of reprs and logs; extract it only at
    # the SDK boundary where the credential is actually needed.
    return AsyncOpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=settings.openai_timeout_seconds,
        max_retries=settings.openai_max_retries,
    )
