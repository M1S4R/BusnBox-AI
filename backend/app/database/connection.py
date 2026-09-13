from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_recycle=settings.database_pool_recycle,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
)


async def dispose_database_engine() -> None:
    """Close all pooled database connections."""

    await engine.dispose()