import importlib
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.chat import (
    ChatIntent,
    ChatParameters,
)
from app.services.ai_service import (
    AIAnalysisResult,
)


client = TestClient(app)

chat_route = importlib.import_module(
    "app.api.routes.chat"
)


@pytest.fixture(autouse=True)
def isolate_chat_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None, None, None]:
    """
    Prevent FAQ and RAG from intercepting search-flow tests.

    Each test controls the AI analysis result directly, so these
    tests do not require Ollama to be running.
    """

    monkeypatch.setattr(
        chat_route.faq_service,
        "find_answer",
        lambda message: None,
    )

    async def no_rag_answer(
        message: str,
    ) -> None:
        return None

    monkeypatch.setattr(
        chat_route.rag_service,
        "answer",
        no_rag_answer,
    )

    yield


def make_analysis(
    *,
    intent: ChatIntent = ChatIntent.SEARCH_BUS,
    reply: str = "I will help you search for buses.",
    source: str | None = None,
    destination: str | None = None,
    travel_date: str | None = None,
    filters: dict | None = None,
) -> AIAnalysisResult:
    return AIAnalysisResult(
        intent=intent,
        reply=reply,
        parameters=ChatParameters(
            source=source,
            destination=destination,
            travel_date=travel_date,
            filters=filters or {},
        ),
    )


def assert_valid_suggestions(
    suggestions: list[dict],
) -> None:
    for suggestion in suggestions:
        assert set(suggestion) == {
            "id",
            "label",
            "message",
            "action",
        }

        assert suggestion["id"]
        assert suggestion["label"]
        assert suggestion["message"]
        assert suggestion["action"]


def test_greeting_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_analyze_message(
        message: str,
        current_parameters: ChatParameters | None = None,
    ) -> AIAnalysisResult:
        return make_analysis(
            intent=ChatIntent.GREETING,
            reply=(
                "Hello! How can I help with "
                "your bus journey?"
            ),
        )

    monkeypatch.setattr(
        chat_route.ai_service,
        "analyze_message",
        fake_analyze_message,
    )

    response = client.post(
        "/api/chat",
        json={
            "message": "Hello",
            "tenant_key": "busnbox",
            "conversation_id": (
                "chat-search-greeting"
            ),
        },
    )
    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["intent"] == "greeting"
    assert data["answer_source"] == "ai"
    assert data["trips"] == []
    assert data["recommendations"] == []
    assert data["suggestions"] == []


def test_help_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_analyze_message(
        message: str,
        current_parameters: ChatParameters | None = None,
    ) -> AIAnalysisResult:
        return make_analysis(
            intent=ChatIntent.HELP,
            reply=(
                "I can help search and refine "
                "bus journeys."
            ),
        )

    monkeypatch.setattr(
        chat_route.ai_service,
        "analyze_message",
        fake_analyze_message,
    )

    response = client.post(
        "/api/chat",
        json={
            "message": "What can you do?",
            "tenant_key": "busnbox",
            "conversation_id": (
                "chat-search-help"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "help"
    assert data["answer_source"] == "ai"
    assert data["reply"]


def test_missing_source_returns_serialized_suggestions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_analyze_message(
        message: str,
        current_parameters: ChatParameters | None = None,
    ) -> AIAnalysisResult:
        return make_analysis(
            destination="Bangalore",
            travel_date="tomorrow",
        )

    monkeypatch.setattr(
        chat_route.ai_service,
        "analyze_message",
        fake_analyze_message,
    )

    conversation_id = "chat-search-missing-source"

    chat_route.conversation_service.clear_context(
        conversation_id
    )

    response = client.post(
        "/api/chat",
        json={
            "message": (
                "I want to travel to Bangalore "
                "tomorrow"
            ),
            "tenant_key": "busnbox",
            "conversation_id": conversation_id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "search_bus"
    assert data["answer_source"] == "inventory"
    assert data["parameters"]["source"] is None
    assert (
        data["parameters"]["destination"]
        == "Bangalore"
    )
    assert data["trips"] == []
    assert data["suggestions"]

    assert_valid_suggestions(
        data["suggestions"]
    )

    assert any(
        suggestion["action"] == "set_source"
        for suggestion in data["suggestions"]
    )


def test_missing_destination_returns_serialized_suggestions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_analyze_message(
        message: str,
        current_parameters: ChatParameters | None = None,
    ) -> AIAnalysisResult:
        return make_analysis(
            source="Chennai",
            travel_date="tomorrow",
        )

    monkeypatch.setattr(
        chat_route.ai_service,
        "analyze_message",
        fake_analyze_message,
    )

    conversation_id = (
        "chat-search-missing-destination"
    )

    chat_route.conversation_service.clear_context(
        conversation_id
    )

    response = client.post(
        "/api/chat",
        json={
            "message": (
                "I am travelling from Chennai "
                "tomorrow"
            ),
            "tenant_key": "busnbox",
            "conversation_id": conversation_id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["parameters"]["source"] == "Chennai"
    assert (
        data["parameters"]["destination"]
        is None
    )
    assert data["suggestions"]

    assert_valid_suggestions(
        data["suggestions"]
    )

    assert any(
        suggestion["action"]
        == "set_destination"
        for suggestion in data["suggestions"]
    )


def test_missing_date_returns_serialized_suggestions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_analyze_message(
        message: str,
        current_parameters: ChatParameters | None = None,
    ) -> AIAnalysisResult:
        return make_analysis(
            source="Chennai",
            destination="Bangalore",
        )

    monkeypatch.setattr(
        chat_route.ai_service,
        "analyze_message",
        fake_analyze_message,
    )

    conversation_id = "chat-search-missing-date"

    chat_route.conversation_service.clear_context(
        conversation_id
    )

    response = client.post(
        "/api/chat",
        json={
            "message": (
                "Find buses from Chennai "
                "to Bangalore"
            ),
            "tenant_key": "busnbox",
            "conversation_id": conversation_id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["parameters"]["source"] == "Chennai"
    assert (
        data["parameters"]["destination"]
        == "Bangalore"
    )
    assert (
        data["parameters"]["travel_date"]
        is None
    )

    assert data["suggestions"]

    assert_valid_suggestions(
        data["suggestions"]
    )

    assert any(
        suggestion["action"]
        == "set_travel_date"
        for suggestion in data["suggestions"]
    )


def test_complete_search_serializes_full_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_analyze_message(
        message: str,
        current_parameters: ChatParameters | None = None,
    ) -> AIAnalysisResult:
        return make_analysis(
            source="Chennai",
            destination="Bangalore",
            travel_date="tomorrow",
        )

    monkeypatch.setattr(
        chat_route.ai_service,
        "analyze_message",
        fake_analyze_message,
    )

    conversation_id = "chat-search-complete"

    chat_route.conversation_service.clear_context(
        conversation_id
    )

    response = client.post(
        "/api/chat",
        json={
            "message": (
                "Find buses from Chennai "
                "to Bangalore tomorrow"
            ),
            "tenant_key": "busnbox",
            "conversation_id": conversation_id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["response_id"]
    assert data["response_time_ms"] >= 0
    assert data["intent"] == "search_bus"
    assert data["answer_source"] == "inventory"
    assert data["conversation_id"] == conversation_id

    assert data["parameters"]["source"] == "Chennai"
    assert (
        data["parameters"]["destination"]
        == "Bangalore"
    )
    assert (
        data["parameters"]["travel_date"]
        == "tomorrow"
    )

    assert data["trips"]
    assert data["recommendations"]
    assert data["suggestions"]

    assert_valid_suggestions(
        data["suggestions"]
    )

    for recommendation in data["recommendations"]:
        assert isinstance(
            recommendation,
            dict,
        )

        assert recommendation["id"]
        assert recommendation["type"]
        assert recommendation["title"]
        assert recommendation["reason"]


def test_complete_ac_search_preserves_filter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_analyze_message(
        message: str,
        current_parameters: ChatParameters | None = None,
    ) -> AIAnalysisResult:
        return make_analysis(
            source="Chennai",
            destination="Bangalore",
            travel_date="tomorrow",
            filters={
                "bus_type": "AC Sleeper",
            },
        )

    monkeypatch.setattr(
        chat_route.ai_service,
        "analyze_message",
        fake_analyze_message,
    )

    conversation_id = "chat-search-ac-filter"

    chat_route.conversation_service.clear_context(
        conversation_id
    )

    response = client.post(
        "/api/chat",
        json={
            "message": (
                "Find AC sleeper buses from "
                "Chennai to Bangalore tomorrow"
            ),
            "tenant_key": "busnbox",
            "conversation_id": conversation_id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["parameters"]["filters"]["bus_type"].casefold()
        == "ac sleeper"
    )

    assert data["trips"]

    for trip in data["trips"]:
        bus = trip.get("bus", {})

        assert (
            bus.get("bus_type").casefold()
            == "ac sleeper"
        )


def test_empty_message_is_rejected() -> None:
    response = client.post(
        "/api/chat",
        json={
            "message": "   ",
            "tenant_key": "busnbox",
            "conversation_id": (
                "chat-search-empty-message"
            ),
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert (
        data["detail"]
        == "Message cannot be empty."
    )