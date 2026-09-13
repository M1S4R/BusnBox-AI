import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

# Import models so SQLAlchemy registers all table mappings.
import application.models  # noqa: F401
from application.api.routes.debug import router as debug_router
from application.api.routes.health import router as health_router
from application.api.routes.inventory import router as inventory_router
from application.core.config import settings
from application.database.session import (
    AsyncSessionFactory,
    close_database,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    application: FastAPI,
) -> AsyncIterator[None]:
    del application

    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))

        logger.info("Connected to MariaDB successfully.")

    except Exception:
        logger.exception("Could not connect to MariaDB.")
        raise

    yield

    await close_database()


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Development-only API that simulates the "
            "BusNBox client inventory service."
        ),
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    application.include_router(health_router)
    application.include_router(debug_router)
    application.include_router(inventory_router)

    return application


app = create_application()