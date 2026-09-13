from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_faq_refund_question() -> None:
    response = client.post(
        "/api/chat",
        json={
            "message": (
                "When will I receive my refund?"
            ),
            "tenant_key": "busnbox",
            "conversation_id": "faq-test-refund",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["intent"] == "faq"
    assert "refund" in data["reply"].lower()
    assert data["trips"] == []
    assert data["recommendations"] == []


def test_faq_pet_question() -> None:
    response = client.post(
        "/api/chat",
        json={
            "message": (
                "Can I travel with my pet?"
            ),
            "tenant_key": "busnbox",
            "conversation_id": "faq-test-pet",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["intent"] == "faq"
    assert "pet" in data["reply"].lower()
    assert data["trips"] == []
    assert data["recommendations"] == []


def test_faq_cancellation_question() -> None:
    response = client.post(
        "/api/chat",
        json={
            "message": (
                "How can I cancel my ticket?"
            ),
            "tenant_key": "busnbox",
            "conversation_id": (
                "faq-test-cancellation"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["intent"] == "faq"
    assert "cancel" in data["reply"].lower()
    assert data["trips"] == []
    assert data["suggestions"] == []
