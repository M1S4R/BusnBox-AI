"""
Simulation of the Spring Boot gateway interacting with the BusNBox AI module.

In production:
  Company React -> Company Spring Boot Gateway -> BusNBox FastAPI (/api/v1/chat)

This test verifies the exact sequence, ensuring proper conversation_id ownership,
state retention, filter handling, route corrections, new search reset, and FAQ isolation.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.routes import chat as chat_route
from app.main import app
from app.schemas.chat import ChatIntent, ChatParameters
from app.services.ai_service import AIAnalysisResult

client = TestClient(app)


def test_spring_boot_gateway_simulation(monkeypatch: pytest.MonkeyPatch) -> None:
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
        if "chennai" in msg and "bangalore" in msg:
            return AIAnalysisResult(
                intent=ChatIntent.SEARCH_BUS,
                reply="Checking buses from Chennai to Bangalore...",
                parameters=ChatParameters(
                    source="Chennai",
                    destination="Bangalore",
                    travel_date="tomorrow" if "tomorrow" in msg else None,
                ),
            )
        return AIAnalysisResult(
            intent=ChatIntent.UPDATE_SEARCH if current_parameters and current_parameters.source else ChatIntent.SEARCH_BUS,
            reply="Updated search parameters.",
            parameters=current_parameters or ChatParameters(),
        )

    monkeypatch.setattr(chat_route.ai_service, "analyze_message", fake_analyze_message)

    # 1. Spring Boot gateway initializes or receives a conversation_id from React
    conversation_id = "sb-gw-session-98765"

    # Step 1: User says: "Find buses from Chennai to Bangalore" (missing date)
    req1 = {
        "message": "Find buses from Chennai to Bangalore",
        "conversation_id": conversation_id,
    }
    res1 = client.post("/api/v1/chat", json=req1)
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["success"] is True
    assert d1["conversation_id"] == conversation_id
    assert d1["parameters"]["source"] == "Chennai"
    assert d1["parameters"]["destination"] == "Bangalore"
    assert d1["parameters"]["travel_date"] is None
    assert len(d1["trips"]) == 0
    assert "when would you like to travel" in d1["reply"].lower()

    # Step 2: User responds with: "tomorrow" (Spring Boot forwards with same conversation_id)
    req2 = {
        "message": "tomorrow",
        "conversation_id": conversation_id,
    }
    res2 = client.post("/api/v1/chat", json=req2)
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["success"] is True
    assert d2["conversation_id"] == conversation_id
    assert d2["parameters"]["source"] == "Chennai"
    assert d2["parameters"]["destination"] == "Bangalore"
    assert d2["parameters"]["travel_date"] == "tomorrow"
    assert len(d2["trips"]) > 0

    # Step 3: User filters: "only AC"
    req3 = {
        "message": "only AC",
        "conversation_id": conversation_id,
    }
    res3 = client.post("/api/v1/chat", json=req3)
    assert res3.status_code == 200
    d3 = res3.json()
    assert d3["success"] is True
    assert d3["parameters"]["filters"]["bus_type"] == "AC"
    assert len(d3["trips"]) > 0
    assert all("AC" in t.get("bus", {}).get("bus_type", "") for t in d3["trips"])

    # Step 4: User sorts: "cheapest"
    req4 = {
        "message": "cheapest",
        "conversation_id": conversation_id,
    }
    res4 = client.post("/api/v1/chat", json=req4)
    assert res4.status_code == 200
    d4 = res4.json()
    assert d4["success"] is True
    assert len(d4["trips"]) > 0
    prices = [float(t["price"]) for t in d4["trips"]]
    assert prices == sorted(prices)

    # Step 5: User makes a route correction: "Wait, change Bangalore to Hyderabad"
    req5 = {
        "message": "Wait, change Bangalore to Hyderabad",
        "conversation_id": conversation_id,
    }
    res5 = client.post("/api/v1/chat", json=req5)
    assert res5.status_code == 200
    d5 = res5.json()
    assert d5["success"] is True
    assert d5["parameters"]["source"] == "Chennai"
    assert d5["parameters"]["destination"] == "Hyderabad"
    assert d5["parameters"]["travel_date"] == "tomorrow"
    assert len(d5["trips"]) > 0

    # Step 6: User clicks New Search / says "start over"
    req6 = {
        "message": "start over",
        "conversation_id": conversation_id,
    }
    res6 = client.post("/api/v1/chat", json=req6)
    assert res6.status_code == 200
    d6 = res6.json()
    assert d6["intent"] == "clear_search"
    assert d6["parameters"]["source"] is None
    assert d6["parameters"]["destination"] is None
    assert len(d6["trips"]) == 0

    # Step 7: User asks an FAQ question: "How can I cancel my ticket?"
    req7 = {
        "message": "How can I cancel my ticket?",
        "conversation_id": conversation_id,
    }
    res7 = client.post("/api/v1/chat", json=req7)
    assert res7.status_code == 200
    d7 = res7.json()
    assert d7["intent"] == "faq"
    assert len(d7["trips"]) == 0
    assert len(d7["sources"]) > 0
