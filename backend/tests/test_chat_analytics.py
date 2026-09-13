import importlib
from pathlib import Path

import pytest
from app.main import app
from app.services.chat_analytics_service import (
    ChatAnalyticsService,
)
from fastapi.testclient import TestClient

client = TestClient(app)

chat_route = importlib.import_module(
    "app.api.routes.chat"
)

analytics_route = importlib.import_module(
    "app.api.routes.analytics"
)


@pytest.fixture
def isolated_analytics_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> ChatAnalyticsService:
    service = ChatAnalyticsService(
        data_path=(
            tmp_path
            / "chat-analytics.jsonl"
        )
    )

    monkeypatch.setattr(
        chat_route,
        "chat_analytics_service",
        service,
    )

    monkeypatch.setattr(
        analytics_route,
        "chat_analytics_service",
        service,
    )

    return service


def test_chat_response_has_tracking_fields(
    isolated_analytics_service: (
        ChatAnalyticsService
    ),
) -> None:
    response = client.post(
        "/api/chat",
        json={
            "message": (
                "How can I cancel my ticket?"
            ),
            "tenant_key": "busnbox",
            "conversation_id": (
                "analytics-chat-test"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["response_id"]
    assert data["answer_source"] == "faq"
    assert data["response_time_ms"] >= 0
    assert data["intent"] == "faq"


def test_chat_analytics_summary(
    isolated_analytics_service: (
        ChatAnalyticsService
    ),
) -> None:
    client.post(
        "/api/chat",
        json={
            "message": (
                "How can I cancel my ticket?"
            ),
            "tenant_key": "busnbox",
            "conversation_id": (
                "analytics-summary-test"
            ),
        },
    )

    response = client.get(
        "/api/analytics/chat/summary"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_responses"] == 1
    assert data["by_answer_source"]["faq"] == 1
    assert data["by_intent"]["faq"] == 1
    assert data["grounded_responses"] == 1
    assert (
        data["average_response_time_ms"]
        is not None
    )
