"""Application entrypoint."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.api.v1.routes.health import router as health_router
from app.core.config import Settings, get_settings
from app.core.exceptions import ApplicationError, application_error_handler
from app.core.logging import configure_logging
from app.dependencies.services import close_services

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Aplicação iniciada")
    try:
        yield
    finally:
        await close_services()
        logger.info("Aplicação encerrada")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_exception_handler(
        ApplicationError,
        application_error_handler,
    )

    allow_credentials = "*" not in settings.cors_origins
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health_router)
    application.include_router(
        api_v1_router,
        prefix=settings.api_v1_prefix,
    )
    return application


app = create_app()
