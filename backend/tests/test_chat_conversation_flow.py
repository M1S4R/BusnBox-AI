import importlib

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


def make_analysis(
    *,
    source=None,
    destination=None,
    travel_date=None,
    filters=None,
):
    return AIAnalysisResult(
        intent=ChatIntent.SEARCH_BUS,
        reply="Searching buses...",
        parameters=ChatParameters(
            source=source,
            destination=destination,
            travel_date=travel_date,
            filters=filters or {},
        ),
    )


def disable_faq_and_rag(
    monkeypatch,
):
    monkeypatch.setattr(
        chat_route.faq_service,
        "find_answer",
        lambda _: None,
    )

    async def fake_rag(_):
        return None

    monkeypatch.setattr(
        chat_route.rag_service,
        "answer",
        fake_rag,
    )


def test_multi_turn_search(
    monkeypatch,
):
    conversation_id = "conversation-flow-1"

    chat_route.conversation_service.clear_context(
        conversation_id
    )

    responses = [
        make_analysis(
            source="Chennai",
        ),
        make_analysis(
            destination="Bangalore",
        ),
        make_analysis(
            travel_date="tomorrow",
        ),
        make_analysis(),
    ]

    async def fake_ai(
        message: str,
        current_parameters: ChatParameters | None = None,
    ) -> AIAnalysisResult:
        del message, current_parameters
        return responses.pop(0)

    monkeypatch.setattr(
        chat_route.ai_service,
        "analyze_message",
        fake_ai,
    )

    disable_faq_and_rag(
        monkeypatch
    )

    first_response = client.post(
        "/api/chat",
        json={
            "message": "From Chennai",
            "tenant_key": "busnbox",
            "conversation_id": conversation_id,
        },
    )

    second_response = client.post(
        "/api/chat",
        json={
            "message": "To Bangalore",
            "tenant_key": "busnbox",
            "conversation_id": conversation_id,
        },
    )

    third_response = client.post(
        "/api/chat",
        json={
            "message": "Tomorrow",
            "tenant_key": "busnbox",
            "conversation_id": conversation_id,
        },
    )

    final_response = client.post(
        "/api/chat",
        json={
            "message": "Search buses",
            "tenant_key": "busnbox",
            "conversation_id": conversation_id,
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert third_response.status_code == 200
    assert final_response.status_code == 200

    data = final_response.json()

    assert (
        data["parameters"]["source"]
        == "Chennai"
    )

    assert (
        data["parameters"]["destination"]
        == "Bangalore"
    )

    assert (
        data["parameters"]["travel_date"]
        == "tomorrow"
    )

    assert len(data["trips"]) > 0


def test_conversations_do_not_share_context(
    monkeypatch,
):
    conversation_a = "conversation-isolation-a"
    conversation_b = "conversation-isolation-b"

    chat_route.conversation_service.clear_context(
        conversation_a
    )

    chat_route.conversation_service.clear_context(
        conversation_b
    )

    analysis_results = {
        "From Chennai": make_analysis(
            source="Chennai",
        ),
        "To Bangalore": make_analysis(
            destination="Bangalore",
        ),
        "From Mumbai": make_analysis(
            source="Mumbai",
        ),
        "To Pune": make_analysis(
            destination="Pune",
        ),
    }

    async def fake_ai(
        message: str,
        current_parameters: ChatParameters | None = None,
    ) -> AIAnalysisResult:
        del current_parameters
        return analysis_results[message]

    monkeypatch.setattr(
        chat_route.ai_service,
        "analyze_message",
        fake_ai,
    )

    disable_faq_and_rag(
        monkeypatch
    )

    first_a_response = client.post(
        "/api/chat",
        json={
            "message": "From Chennai",
            "tenant_key": "busnbox",
            "conversation_id": conversation_a,
        },
    )

    second_a_response = client.post(
        "/api/chat",
        json={
            "message": "To Bangalore",
            "tenant_key": "busnbox",
            "conversation_id": conversation_a,
        },
    )

    first_b_response = client.post(
        "/api/chat",
        json={
            "message": "From Mumbai",
            "tenant_key": "busnbox",
            "conversation_id": conversation_b,
        },
    )

    second_b_response = client.post(
        "/api/chat",
        json={
            "message": "To Pune",
            "tenant_key": "busnbox",
            "conversation_id": conversation_b,
        },
    )

    assert first_a_response.status_code == 200
    assert second_a_response.status_code == 200
    assert first_b_response.status_code == 200
    assert second_b_response.status_code == 200

    data_a = second_a_response.json()
    data_b = second_b_response.json()

    assert (
        data_a["parameters"]["source"]
        == "Chennai"
    )

    assert (
        data_a["parameters"]["destination"]
        == "Bangalore"
    )

    assert (
        data_b["parameters"]["source"]
        == "Mumbai"
    )

    assert (
        data_b["parameters"]["destination"]
        == "Pune"
    )

    assert (
        data_a["parameters"]["source"]
        != data_b["parameters"]["source"]
    )

    assert (
        data_a["parameters"]["destination"]
        != data_b["parameters"]["destination"]
    )