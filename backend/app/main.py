import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)


from app.api.routes.agent_debug import router as agent_debug_router
from app.api.routes.ai_debug import router as ai_debug_router
from app.api.routes.analytics import (
    router as analytics_router,
)
from app.api.routes.chat import (
    router as chat_router,
)
from app.api.routes.feedback import (
    router as feedback_router,
)
from app.api.routes.health import (
    router as health_router,
)
from app.api.routes.inventory import (
    router as inventory_router,
)
from app.core.config import settings


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Backend API for the BusNBox "
            "bus-search platform and AI "
            "chat assistant."
        ),
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    @application.exception_handler(HTTPException)
    async def custom_http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            return JSONResponse(
                status_code=404,
                content={"detail": str(exc.detail)},
            )

        code = "INTERNAL_ERROR"
        if exc.status_code == status.HTTP_400_BAD_REQUEST:
            code = "INVALID_REQUEST"
        elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = "UNAUTHORIZED"
        elif exc.status_code == status.HTTP_408_REQUEST_TIMEOUT:
            code = "TIMEOUT"
        elif exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            detail_lower = str(exc.detail).lower()
            if "inventory" in detail_lower:
                code = "INVENTORY_UNAVAILABLE"
            elif any(k in detail_lower for k in ("ai", "gemini", "model", "provider")):
                code = "AI_PROVIDER_UNAVAILABLE"
            elif any(k in detail_lower for k in ("knowledge", "rag", "faq")):
                code = "KNOWLEDGE_BASE_UNAVAILABLE"
            else:
                code = "SERVICE_UNAVAILABLE"
        elif exc.status_code >= 500:
            code = "INTERNAL_ERROR"

        message = str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": code,
                    "message": message,
                },
                "detail": message,
            },
        )

    @application.exception_handler(RequestValidationError)
    async def custom_validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        message = "Request validation failed."
        if exc.errors():
            first = exc.errors()[0]
            loc = " -> ".join(str(x) for x in first.get("loc", []))
            message = f"Field {loc}: {first.get('msg', 'invalid')}"

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": message,
                },
                "detail": message,
            },
        )

    @application.exception_handler(Exception)
    async def custom_general_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled application error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred.",
                },
                "detail": "An internal error occurred.",
            },
        )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=(
            settings.cors_origins
        ),
        allow_origin_regex=(
            r"^https://.*\.trycloudflare\.com$"
            if settings.debug
            else None
        ),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(
        health_router
    )

    application.include_router(
        inventory_router
    )

    application.include_router(
        chat_router
    )

    application.include_router(
        feedback_router
    )

    application.include_router(
        analytics_router
    )

    application.include_router(
        ai_debug_router
    )

    application.include_router(agent_debug_router)

    frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            application.mount(
                "/assets",
                StaticFiles(directory=str(assets_dir)),
                name="static_assets",
            )

        @application.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            if full_path.startswith(("api/", "docs", "redoc", "openapi.json")):
                raise HTTPException(status_code=404, detail="Not Found")
            file_path = (frontend_dist / full_path).resolve()
            if not file_path.is_relative_to(frontend_dist):
                raise HTTPException(status_code=404, detail="Not Found")
            if full_path and file_path.is_file():
                return FileResponse(file_path)
            index_path = frontend_dist / "index.html"
            if index_path.is_file():
                return FileResponse(index_path)
            raise HTTPException(status_code=404, detail="Frontend build not found")

    return application


app = create_application()
