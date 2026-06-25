import logging
import sys

from pythonjsonlogger.json import JsonFormatter

from app.core.config import settings


def configure_logging() -> None:
    """Configure process-wide structured logging.

    JSON logs are friendlier to production log aggregators than plain text logs.
    Clearing handlers prevents duplicate logs when tests create multiple apps.
    """
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    formatter = JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level.upper())


def get_logger(name: str) -> logging.Logger:
    """Return a named logger so log lines show the source module."""
    return logging.getLogger(name)
