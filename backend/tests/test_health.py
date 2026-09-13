from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


client = TestClient(app)


def test_health_endpoint_returns_success() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


def test_unknown_endpoint_returns_not_found() -> None:
    response = client.get("/api/unknown")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Not Found",
    }


def test_cors_allows_frontend_origin() -> None:
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )