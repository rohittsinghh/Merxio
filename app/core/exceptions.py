from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """Base exception for expected application errors.

    Services should raise this for known business failures. The handler below
    converts it into a stable API response instead of leaking Python internals.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "application_error",
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for consistent API errors."""

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        # Expected business errors are warnings, not server crashes.
        logger.warning(
            "application_exception",
            extra={
                "path": request.url.path,
                "error_code": exc.error_code,
                "status_code": exc.status_code,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.error_code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        # Validation errors are client input problems, so they return 422.
        logger.info("request_validation_failed", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed.",
                    "details": exc.errors(),
                }
            },
        )
