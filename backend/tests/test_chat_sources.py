import importlib

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.services.rag_service import RAGAnswer


client = TestClient(app)

chat_route = importlib.import_module(
    "app.api.routes.chat"
)


def test_exact_faq_returns_source() -> None:
    response = client.post(
        "/api/chat",
        json={
            "message": (
                "How can I cancel my bus ticket?"
            ),
            "tenant_key": "busnbox",
            "conversation_id": (
                "source-test-faq"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "faq"
    assert data["sources"]
    assert data["sources"][0]["kind"] == "faq"
    assert data["sources"][0]["id"]
    assert data["sources"][0]["title"]
    assert (
        data["grounding_confidence"]
        is not None
    )


def test_rag_answer_returns_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        chat_route.faq_service,
        "find_answer",
        lambda message: None,
    )

    async def fake_rag_answer(
        message: str,
    ) -> RAGAnswer:
        return RAGAnswer(
            answer=(
                "Passengers should arrive before "
                "the reporting time."
            ),
            source_ids=(
                "kb-boarding-time",
            ),
            source_titles=(
                "Boarding Time and Reporting",
            ),
            confidence=0.88,
        )

    monkeypatch.setattr(
        chat_route.rag_service,
        "answer",
        fake_rag_answer,
    )

    response = client.post(
        "/api/chat",
        json={
            "message": (
                "What happens if I arrive late?"
            ),
            "tenant_key": "busnbox",
            "conversation_id": (
                "source-test-rag"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "faq"
    assert data["sources"] == [
        {
            "id": "kb-boarding-time",
            "title": (
                "Boarding Time and Reporting"
            ),
            "kind": "knowledge_base",
        }
    ]

    assert (
        data["grounding_confidence"]
        == 0.88
    )
