from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(
    prefix="/api",
    tags=["Health"],
)


class HealthResponse(BaseModel):
    success: Literal[True] = True
    status: Literal["healthy"] = "healthy"
    service: str
    version: str


class ReadinessResponse(BaseModel):
    success: Literal[True] = True
    status: Literal["ready"] = "ready"
    service: str
    version: str
    checks: dict[str, str]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check backend health (legacy)",
)
@router.get(
    "/v1/health",
    response_model=HealthResponse,
    summary="Check backend health (v1)",
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        service=settings.app_name,
        version=settings.app_version,
    )


@router.get(
    "/v1/ready",
    response_model=ReadinessResponse,
    summary="Check backend readiness (v1)",
)
@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Check backend readiness",
)
async def readiness_check() -> ReadinessResponse:
    return ReadinessResponse(
        service=settings.app_name,
        version=settings.app_version,
        checks={
            "ai_provider": settings.ai_provider,
            "inventory_provider": settings.inventory_provider,
            "service": "operational",
        },
    )