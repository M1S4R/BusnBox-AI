from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException, status

from application.core.config import settings
from application.database.session import get_database_session


router = APIRouter(
    prefix="/api/v1/health",
    tags=["Health"],
)


@router.get("")
async def health_check(
    session: AsyncSession = Depends(get_database_session),
) -> dict[str, object]:
    try:
        await session.execute(text("SELECT 1"))

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed.",
        ) from exc

    return {
        "success": True,
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "database": "connected",
    }