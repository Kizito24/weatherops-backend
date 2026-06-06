"""
FastAPI application factory.
Creates and configures the main application instance.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.exceptions import ApplicationException
from app.core.logging import setup_logging
from app.core.responses import ErrorResponse
from app.core.redis import RedisClient
from app.database import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting WeatherOps application")
    try:
        await RedisClient.connect()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")

    yield

    # Shutdown
    logger.info("Shutting down WeatherOps application")
    try:
        await RedisClient.disconnect()
        await engine.dispose()
        logger.info("Resources cleaned up")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI instance.
    """
    setup_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description="Production-grade weather monitoring and alerting system. Monitor weather conditions across multiple locations, create intelligent rules, and receive real-time alerts via email, SMS, and webhooks.",
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(ApplicationException)
    async def application_exception_handler(
        request: Request, exc: ApplicationException
    ) -> JSONResponse:
        """Handle custom application exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                message=exc.message,
                error_code=exc.error_code,
                details=[],
            ).model_dump(),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, exc: ValueError
    ) -> JSONResponse:
        """Handle validation errors."""
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                message="Validation error",
                error_code="VALIDATION_ERROR",
                details=[],
            ).model_dump(),
        )

    # Include routers
    app.include_router(api_v1_router)

    logger.info(f"Application created. Environment: {settings.ENVIRONMENT}")

    return app


app = create_app()
