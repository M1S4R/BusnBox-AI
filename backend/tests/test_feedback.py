import importlib
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.services.feedback_service import (
    FeedbackService,
)


client = TestClient(app)

feedback_route = importlib.import_module(
    "app.api.routes.feedback"
)


@pytest.fixture
def isolated_feedback_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> FeedbackService:
    service = FeedbackService(
        data_path=(
            tmp_path
            / "feedback-events.jsonl"
        )
    )

    monkeypatch.setattr(
        feedback_route,
        "feedback_service",
        service,
    )

    return service


def test_submit_thumbs_up_feedback(
    isolated_feedback_service: (
        FeedbackService
    ),
) -> None:
    response = client.post(
        "/api/feedback",
        json={
            "message_id": (
                "assistant-message-001"
            ),
            "conversation_id": (
                "conversation-001"
            ),
            "rating": "up",
            "intent": "search_bus",
            "metadata": {
                "screen": "chat-widget"
            },
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["success"] is True
    assert data["feedback_id"]
    assert data["rating"] == "up"
    assert (
        data["message_id"]
        == "assistant-message-001"
    )


def test_submit_thumbs_down_feedback(
    isolated_feedback_service: (
        FeedbackService
    ),
) -> None:
    response = client.post(
        "/api/feedback",
        json={
            "message_id": (
                "assistant-message-002"
            ),
            "conversation_id": (
                "conversation-001"
            ),
            "rating": "down",
            "reason": "inaccurate",
            "comment": (
                "The departure time was incorrect."
            ),
            "intent": "search_bus",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["rating"] == "down"
    assert data["reason"] == "inaccurate"


def test_feedback_can_be_changed(
    isolated_feedback_service: (
        FeedbackService
    ),
) -> None:
    first_response = client.post(
        "/api/feedback",
        json={
            "message_id": "assistant-message-003",
            "conversation_id": "conversation-002",
            "rating": "up",
        },
    )

    second_response = client.post(
        "/api/feedback",
        json={
            "message_id": "assistant-message-003",
            "conversation_id": "conversation-002",
            "rating": "down",
            "reason": "irrelevant",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_data = first_response.json()
    second_data = second_response.json()

    assert (
        first_data["feedback_id"]
        == second_data["feedback_id"]
    )

    assert second_data["rating"] == "down"


def test_feedback_summary(
    isolated_feedback_service: (
        FeedbackService
    ),
) -> None:
    client.post(
        "/api/feedback",
        json={
            "message_id": "summary-message-1",
            "rating": "up",
            "intent": "faq",
        },
    )

    client.post(
        "/api/feedback",
        json={
            "message_id": "summary-message-2",
            "rating": "down",
            "reason": "unclear",
            "intent": "search_bus",
        },
    )

    response = client.get(
        "/api/feedback/summary"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert data["thumbs_up"] == 1
    assert data["thumbs_down"] == 1
    assert data["approval_rate"] == 0.5
    assert data["reasons"]["unclear"] == 1
