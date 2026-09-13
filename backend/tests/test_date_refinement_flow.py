"""Regression tests for date parsing, multi-turn search refinement, and RAG ordering."""

import importlib
from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.chat import ChatIntent, ChatParameters
from app.services.ai_service import AIAnalysisResult
from app.services.date_service import (
    extract_date_reference,
    resolve_calendar_date,
)

client = TestClient(app)
chat_route = importlib.import_module("app.api.routes.chat")

REFERENCE_DATE = date(2026, 7, 22)  # Wednesday


def make_search_analysis(*, source=None, destination=None, travel_date=None, filters=None):
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


def test_date_service_unit_determinations():
    """Verify deterministic resolution for all 13 date patterns."""
    # 1. tomorrow -> 2026-07-23 (Thursday)
    assert resolve_calendar_date("tomorrow", reference_date=REFERENCE_DATE) == date(2026, 7, 23)

    # 2. today -> 2026-07-22 (Wednesday)
    assert resolve_calendar_date("today", reference_date=REFERENCE_DATE) == date(2026, 7, 22)

    # 3. day after tomorrow -> 2026-07-24 (Friday)
    assert resolve_calendar_date("day after tomorrow", reference_date=REFERENCE_DATE) == date(2026, 7, 24)

    # 4. next Friday -> 2026-07-31
    assert resolve_calendar_date("next Friday", reference_date=REFERENCE_DATE) == date(2026, 7, 31)

    # 5. this weekend -> Saturday 2026-07-25
    assert resolve_calendar_date("this weekend", reference_date=REFERENCE_DATE) == date(2026, 7, 25)

    # 6. next weekend -> Saturday 2026-08-01
    assert resolve_calendar_date("next weekend", reference_date=REFERENCE_DATE) == date(2026, 8, 1)

    # 7. 25/07/2026 -> 2026-07-25
    assert resolve_calendar_date("25/07/2026", reference_date=REFERENCE_DATE) == date(2026, 7, 25)

    # Extraction tests avoiding substring bugs (e.g. day after tomorrow not matching tomorrow)
    assert extract_date_reference("I want to leave day after tomorrow please") == "day after tomorrow"
    assert extract_date_reference("can I travel tomorrow") == "tomorrow"
    assert extract_date_reference("book for next Friday").lower() == "next friday"
    assert extract_date_reference("traveling this weekend") == "this weekend"
    assert extract_date_reference("traveling next weekend") == "next weekend"
    assert extract_date_reference("journey on 25/07/2026") == "25/07/2026"
    assert extract_date_reference("on 25-07-2026") == "25-07-2026"
    assert extract_date_reference("on 2026-07-25") == "2026-07-25"
    assert extract_date_reference("on 25 July").lower() == "25 july"
    assert extract_date_reference("on July 25").lower() == "july 25"


@pytest.mark.parametrize(
    "date_input, expected_date_str",
    [
        ("tomorrow", "tomorrow"),
        ("today", "today"),
        ("day after tomorrow", "day after tomorrow"),
        ("next Friday", "next friday"),
        ("this weekend", "this weekend"),
        ("next weekend", "next weekend"),
        ("25/07/2026", "25/07/2026"),
    ],
)
def test_chennai_to_bangalore_date_variations(monkeypatch, date_input, expected_date_str):
    """Tests 1-7: Chennai -> Bangalore followed by date variations."""
    conv_id = f"test-date-{date_input.replace(' ', '-').replace('/', '-')}"
    chat_route.conversation_service.clear_context(conv_id)

    # Turn 1: User says "I want to travel from Chennai to Bangalore"
    async def fake_ai_turn1(message: str = "", current_parameters: ChatParameters | None = None, **kwargs):
        return make_search_analysis(source="Chennai", destination="Bangalore")

    monkeypatch.setattr(chat_route.ai_service, "analyze_message", fake_ai_turn1)
    monkeypatch.setattr(chat_route.faq_service, "find_answer", lambda _: None)

    async def fake_rag(_):
        return None

    monkeypatch.setattr(chat_route.rag_service, "answer", fake_rag)

    res1 = client.post(
        "/api/chat",
        json={"message": "I want to travel from Chennai to Bangalore", "conversation_id": conv_id},
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["parameters"]["source"] == "Chennai"
    assert data1["parameters"]["destination"] == "Bangalore"
    assert data1["parameters"]["travel_date"] is None
    assert len(data1["trips"]) == 0

    # Turn 2: User provides date variation
    async def fake_ai_turn2(message: str = "", current_parameters: ChatParameters | None = None, **kwargs):
        return AIAnalysisResult(
            intent=ChatIntent.UNKNOWN,
            reply="Sure, looking up buses for you.",
            parameters=ChatParameters(travel_date=message),
        )

    monkeypatch.setattr(chat_route.ai_service, "analyze_message", fake_ai_turn2)

    res2 = client.post(
        "/api/chat",
        json={"message": date_input, "conversation_id": conv_id},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["parameters"]["source"] == "Chennai"
    assert data2["parameters"]["destination"] == "Bangalore"
    assert data2["parameters"]["travel_date"].lower() == expected_date_str.lower()
    # Inventory search executed!
    assert len(data2["trips"]) > 0


def test_date_only_follow_up_preserves_search_intent(monkeypatch):
    """Test 8: Date-only follow-up must be treated as a valid continuation."""
    conv_id = "test-date-only-continuation"
    chat_route.conversation_service.clear_context(conv_id)

    async def fake_ai(message: str = "", current_parameters: ChatParameters | None = None, **kwargs):
        if "Chennai" in message:
            return make_search_analysis(source="Chennai", destination="Bangalore")
        # Simulating AI classifying "tomorrow" as unknown with no parameters
        return AIAnalysisResult(
            intent=ChatIntent.UNKNOWN,
            reply="Okay",
            parameters=ChatParameters(),
        )

    monkeypatch.setattr(chat_route.ai_service, "analyze_message", fake_ai)
    monkeypatch.setattr(chat_route.faq_service, "find_answer", lambda _: None)

    async def fake_rag(_):
        return None

    monkeypatch.setattr(chat_route.rag_service, "answer", fake_rag)

    r1 = client.post("/api/chat", json={"message": "Buses from Chennai to Bangalore", "conversation_id": conv_id})
    assert r1.status_code == 200

    r2 = client.post("/api/chat", json={"message": "tomorrow", "conversation_id": conv_id})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["parameters"]["source"] == "Chennai"
    assert d2["parameters"]["destination"] == "Bangalore"
    assert d2["parameters"]["travel_date"] == "tomorrow"
    assert len(d2["trips"]) > 0


def test_filter_follow_up(monkeypatch):
    """Test 9: Filter follow-ups ("only AC", "cheapest")."""
    conv_id = "test-filter-followup"
    chat_route.conversation_service.clear_context(conv_id)

    async def fake_ai(message: str = "", current_parameters: ChatParameters | None = None, **kwargs):
        if "Chennai" in message:
            return make_search_analysis(source="Chennai", destination="Bangalore", travel_date="tomorrow")
        elif "AC" in message or "ac" in message:
            return make_search_analysis(filters={"bus_type": "AC"})
        elif "cheap" in message:
            return make_search_analysis(filters={"sort_by": "price"})
        return make_search_analysis()

    monkeypatch.setattr(chat_route.ai_service, "analyze_message", fake_ai)
    monkeypatch.setattr(chat_route.faq_service, "find_answer", lambda _: None)

    async def fake_rag(_):
        return None

    monkeypatch.setattr(chat_route.rag_service, "answer", fake_rag)

    # Initial search
    r1 = client.post("/api/chat", json={"message": "Chennai to Bangalore tomorrow", "conversation_id": conv_id})
    assert r1.status_code == 200
    all_trips = r1.json()["trips"]
    assert len(all_trips) > 0

    # Filter follow-up: "only AC"
    r2 = client.post("/api/chat", json={"message": "only AC", "conversation_id": conv_id})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["parameters"]["source"] == "Chennai"
    assert d2["parameters"]["destination"] == "Bangalore"
    assert d2["parameters"]["travel_date"] == "tomorrow"
    # All returned trips must have bus_type AC
    for trip in d2["trips"]:
        assert "ac" in trip["bus"]["bus_type"].lower()

    # Filter follow-up: "cheapest"
    r3 = client.post("/api/chat", json={"message": "cheapest", "conversation_id": conv_id})
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["parameters"]["source"] == "Chennai"
    prices = [t["price"] for t in d3["trips"]]
    assert prices == sorted(prices)
    assert len(d3["recommendations"]) > 0


def test_new_search_replacing_old_search(monkeypatch):
    """Test 10: New route search replaces old search in the same conversation."""
    conv_id = "test-new-search-replace"
    chat_route.conversation_service.clear_context(conv_id)

    async def fake_ai(message: str = "", current_parameters: ChatParameters | None = None, **kwargs):
        if "Chennai" in message:
            return make_search_analysis(source="Chennai", destination="Bangalore", travel_date="tomorrow")
        else:
            return make_search_analysis(source="Mumbai", destination="Pune", travel_date="today")

    monkeypatch.setattr(chat_route.ai_service, "analyze_message", fake_ai)
    monkeypatch.setattr(chat_route.faq_service, "find_answer", lambda _: None)

    async def fake_rag(_):
        return None

    monkeypatch.setattr(chat_route.rag_service, "answer", fake_rag)

    r1 = client.post("/api/chat", json={"message": "Chennai to Bangalore tomorrow", "conversation_id": conv_id})
    assert r1.json()["parameters"]["source"] == "Chennai"

    r2 = client.post("/api/chat", json={"message": "Mumbai to Pune today", "conversation_id": conv_id})
    d2 = r2.json()
    assert d2["parameters"]["source"] == "Mumbai"
    assert d2["parameters"]["destination"] == "Pune"
    assert d2["parameters"]["travel_date"] == "today"


def test_conversation_reset():
    """Test 11: Conversation context isolation & reset."""
    conv_id = "test-reset-conv"
    chat_route.conversation_service.update_context(
        conv_id,
        ChatParameters(source="Delhi", destination="Jaipur", travel_date="tomorrow"),
    )
    ctx = chat_route.conversation_service.get_context(conv_id)
    assert ctx.parameters.source == "Delhi"

    chat_route.conversation_service.clear_context(conv_id)
    ctx_cleared = chat_route.conversation_service.get_context(conv_id)
    assert ctx_cleared.parameters.source is None


def test_rag_faq_question():
    """Test 12: RAG / FAQ question handling."""
    conv_id = "test-rag-cancellation"
    chat_route.conversation_service.clear_context(conv_id)

    res = client.post(
        "/api/chat",
        json={"message": "How can I cancel my ticket?", "conversation_id": conv_id},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] in ["faq", "rag_answer", "general_chat"]
    assert "cancel" in data["reply"].lower()
    # Trip search is not triggered
    assert len(data["trips"]) == 0


def test_bus_search_containing_faq_keywords_not_hijacked_by_rag(monkeypatch):
    """Test 13: Bus search containing keywords like 'book', 'ticket' must not be hijacked by RAG."""
    conv_id = "test-keywords-not-hijacked"
    chat_route.conversation_service.clear_context(conv_id)

    async def fake_ai(message: str = "", current_parameters: ChatParameters | None = None, **kwargs):
        return make_search_analysis(
            source="Chennai",
            destination="Bangalore",
            travel_date="tomorrow",
        )

    monkeypatch.setattr(chat_route.ai_service, "analyze_message", fake_ai)

    res = client.post(
        "/api/chat",
        json={"message": "I want to book a ticket from Chennai to Bangalore tomorrow", "conversation_id": conv_id},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "search_bus"
    assert data["parameters"]["source"] == "Chennai"
    assert data["parameters"]["destination"] == "Bangalore"
    assert len(data["trips"]) > 0
