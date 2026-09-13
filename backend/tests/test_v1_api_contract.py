from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes import chat as chat_route
from app.core.config import settings
from app.main import app
from app.schemas.chat import ChatIntent, ChatParameters
from app.services.ai_service import AIAnalysisResult

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_ai_service_for_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_analyze_message(
        message: str,
        current_parameters: ChatParameters | None = None,
    ) -> AIAnalysisResult:
        msg = message.strip().lower()
        if "cancel" in msg or "ticket" in msg:
            return AIAnalysisResult(
                intent=ChatIntent.FAQ,
                reply="Tickets can be cancelled up to 2 hours before departure.",
                parameters=current_parameters or ChatParameters(),
            )
        if "start over" in msg or "new search" in msg:
            return AIAnalysisResult(
                intent=ChatIntent.CLEAR_SEARCH,
                reply="Sure — where would you like to travel?",
                parameters=ChatParameters(),
            )
        src = None
        dst = None
        if "chennai" in msg:
            src = "Chennai"
        elif "mumbai" in msg:
            src = "Mumbai"

        if "bangalore" in msg:
            dst = "Bangalore"
        elif "hyderabad" in msg:
            dst = "Hyderabad"
        elif "pune" in msg:
            dst = "Pune"

        if src and dst:
            return AIAnalysisResult(
                intent=ChatIntent.SEARCH_BUS,
                reply=f"Checking buses from {src} to {dst}...",
                parameters=ChatParameters(
                    source=src,
                    destination=dst,
                    travel_date="tomorrow" if "tomorrow" in msg else None,
                ),
            )

        return AIAnalysisResult(
            intent=ChatIntent.UPDATE_SEARCH if current_parameters and current_parameters.source else ChatIntent.SEARCH_BUS,
            reply="Updated search parameters.",
            parameters=current_parameters or ChatParameters(),
        )

    monkeypatch.setattr(chat_route.ai_service, "analyze_message", fake_analyze_message)


def test_v1_health_check() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


def test_v1_readiness_check() -> None:
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "ready"
    assert "checks" in data
    assert "ai_provider" in data["checks"]
    assert "inventory_provider" in data["checks"]


def test_v1_chat_new_search_contract() -> None:
    payload = {
        "message": "Chennai to Bangalore tomorrow",
        "conversation_id": "v1-test-search-1",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["conversation_id"] == "v1-test-search-1"
    assert "response_id" in data
    assert data["intent"] == "search_bus"
    assert data["parameters"]["source"] == "Chennai"
    assert data["parameters"]["destination"] == "Bangalore"
    assert isinstance(data["trips"], list)
    assert isinstance(data["reply"], str) and len(data["reply"]) > 0


def test_v1_chat_missing_date_contract() -> None:
    payload = {
        "message": "Find buses from Chennai to Bangalore",
        "conversation_id": "v1-test-missing-date",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["parameters"]["source"] == "Chennai"
    assert data["parameters"]["destination"] == "Bangalore"
    assert data["parameters"]["travel_date"] is None
    assert "when would you like to travel" in data["reply"].lower()


def test_v1_chat_multi_turn_follow_up_contract() -> None:
    cid = "v1-test-multi-turn"

    # Turn 1: Route without date
    r1 = client.post("/api/v1/chat", json={"message": "Chennai to Bangalore", "conversation_id": cid}).json()
    assert r1["parameters"]["source"] == "Chennai"
    assert r1["parameters"]["travel_date"] is None

    # Turn 2: Follow up with date
    r2 = client.post("/api/v1/chat", json={"message": "tomorrow", "conversation_id": cid}).json()
    assert r2["parameters"]["source"] == "Chennai"
    assert r2["parameters"]["destination"] == "Bangalore"
    assert r2["parameters"]["travel_date"] == "tomorrow"
    assert len(r2["trips"]) > 0

    # Turn 3: Follow up with filter
    r3 = client.post("/api/v1/chat", json={"message": "only AC", "conversation_id": cid}).json()
    assert r3["parameters"]["filters"]["bus_type"] == "AC"
    assert len(r3["trips"]) > 0
    assert all("AC" in t.get("bus", {}).get("bus_type", "") for t in r3["trips"])

    # Turn 4: Follow up with sorting
    r4 = client.post("/api/v1/chat", json={"message": "cheapest", "conversation_id": cid}).json()
    assert len(r4["trips"]) > 0
    prices = [float(t["price"]) for t in r4["trips"]]
    assert prices == sorted(prices)


def test_v1_chat_route_correction_contract() -> None:
    cid = "v1-test-correction"

    # Initial search
    r1 = client.post(
        "/api/v1/chat",
        json={"message": "Chennai to Bangalore tomorrow", "conversation_id": cid},
    ).json()
    assert r1["parameters"]["destination"] == "Bangalore"

    # Correction of destination preserves date
    r2 = client.post(
        "/api/v1/chat",
        json={"message": "Wait, change Bangalore to Hyderabad", "conversation_id": cid},
    ).json()
    assert r2["parameters"]["source"] == "Chennai"
    assert r2["parameters"]["destination"] == "Hyderabad"
    assert r2["parameters"]["travel_date"] == "tomorrow"
    assert len(r2["trips"]) > 0


def test_v1_chat_clear_search_contract() -> None:
    cid = "v1-test-clear"

    # Populate search
    client.post("/api/v1/chat", json={"message": "Chennai to Bangalore tomorrow", "conversation_id": cid})

    # Clear search
    r2 = client.post("/api/v1/chat", json={"message": "New Search", "conversation_id": cid}).json()
    assert r2["intent"] == "clear_search"
    assert r2["parameters"]["source"] is None
    assert r2["parameters"]["destination"] is None
    assert len(r2["trips"]) == 0


def test_v1_chat_faq_contract() -> None:
    payload = {
        "message": "How can I cancel my ticket?",
        "conversation_id": "v1-test-faq",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "faq"
    assert data["answer_source"] in ("faq", "rag")
    assert len(data["trips"]) == 0
    assert len(data["sources"]) > 0


def test_v1_chat_invalid_request_error_contract() -> None:
    # Empty message should yield structured INVALID_REQUEST
    response = client.post("/api/v1/chat", json={"message": "   "})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "INVALID_REQUEST"
    assert "message" in data["error"]
    assert data["detail"] == data["error"]["message"]


def test_v1_chat_missing_body_error_contract() -> None:
    # Malformed / missing required field
    response = client.post("/api/v1/chat", json={})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_REQUEST"


def test_v1_chat_service_to_service_auth_contract() -> None:
    # When busnbox_api_key is set, verify unauthorized without key and success with key
    with patch.object(settings, "busnbox_api_key", "secret-token-123"):
        # Request without header
        res_no_auth = client.post("/api/v1/chat", json={"message": "Hi"})
        assert res_no_auth.status_code == 401
        data_no_auth = res_no_auth.json()
        assert data_no_auth["success"] is False
        assert data_no_auth["error"]["code"] == "UNAUTHORIZED"

        # Request with wrong header
        res_wrong_auth = client.post(
            "/api/v1/chat",
            json={"message": "Hi"},
            headers={"X-BusNBox-Key": "wrong-key"},
        )
        assert res_wrong_auth.status_code == 401

        # Request with correct header
        res_ok = client.post(
            "/api/v1/chat",
            json={"message": "Hi"},
            headers={"X-BusNBox-Key": "secret-token-123"},
        )
        assert res_ok.status_code == 200

        # Request with Bearer auth
        res_bearer = client.post(
            "/api/v1/chat",
            json={"message": "Hi"},
            headers={"Authorization": "Bearer secret-token-123"},
        )
        assert res_bearer.status_code == 200


def test_v1_chat_conversation_isolation_contract() -> None:
    cid_a = "isolation-session-A"
    cid_b = "isolation-session-B"

    # User A searches Chennai to Bangalore
    res_init_a = client.post(
        "/api/v1/chat",
        json={"message": "Chennai to Bangalore tomorrow", "conversation_id": cid_a},
    )
    assert res_init_a.status_code == 200

    # User B searches Mumbai to Pune
    res_init_b = client.post(
        "/api/v1/chat",
        json={"message": "Mumbai to Pune tomorrow", "conversation_id": cid_b},
    )
    assert res_init_b.status_code == 200

    # Turn 2: User A applies filter
    res_a = client.post("/api/v1/chat", json={"message": "only AC", "conversation_id": cid_a}).json()
    assert res_a["parameters"]["source"] == "Chennai"
    assert res_a["parameters"]["destination"] == "Bangalore"

    # Turn 2: User B asks for cheapest
    res_b = client.post("/api/v1/chat", json={"message": "cheapest", "conversation_id": cid_b}).json()
    assert res_b["parameters"]["source"] == "Mumbai"
    assert res_b["parameters"]["destination"] == "Pune"
