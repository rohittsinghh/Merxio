from collections.abc import AsyncIterator
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# The engine owns the database connection pool for this process.
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
)

# The session factory creates short-lived units of work for requests/services.
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Provide one database session per request.

    FastAPI dependencies can inject this into repositories or services. The
    context manager guarantees the session is closed after the request finishes.
    """
    async with AsyncSessionFactory() as session:
        yield session


@dataclass(frozen=True)
class DatabaseHealth:
    status: str


async def check_database_health() -> DatabaseHealth:
    """Run the smallest useful database query for readiness checks."""
    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        return DatabaseHealth(status="unavailable")
    return DatabaseHealth(status="ok")
