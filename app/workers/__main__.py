from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


def main() -> None:
    configure_logging()
    logger.info("worker_started")


if __name__ == "__main__":
    main()
