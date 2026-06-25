from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.health import router as health_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run application-level startup and shutdown work.

    FastAPI's lifespan hook is the right place for process-wide setup such as
    logging, metrics, connection checks, and graceful cleanup.
    """
    configure_logging()
    logger.info("application_starting", extra={"environment": settings.app_env})
    yield
    logger.info("application_stopping")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Keeping app construction in a function makes testing easier because tests
    can create a fresh app instance without importing global side effects.
    """
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS is centralized here so every API version gets the same browser policy.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Cross-cutting behavior is registered once at the application boundary.
    register_exception_handlers(app)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(health_router, prefix="/api/v1", tags=["health"])
    return app


# ASGI servers such as Uvicorn import this variable to serve the application.
app = create_app()
