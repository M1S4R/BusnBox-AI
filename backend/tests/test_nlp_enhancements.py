import importlib
from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.chat import ChatIntent, ChatParameters
from app.services.ai_service import AIAnalysisResult
from app.services.date_service import extract_date_reference, resolve_calendar_date
from app.services.query_refinement_service import query_refinement_service
from app.services.route_service import route_service

chat_route = importlib.import_module("app.api.routes.chat")

REFERENCE_DATE = date(2026, 7, 22)  # Wednesday


# =====================================================================
# PART 2 & PART 10: ROUTE EXTRACTION & TYPO TOLERANCE
# =====================================================================


def test_route_natural_phrasing_from_to() -> None:
    route = route_service.extract_route("I want to go from Chennai to Bangalore")
    assert route.source == "Chennai"
    assert route.destination == "Bangalore"


def test_route_inverted_to_from() -> None:
    route = route_service.extract_route("Can you find buses to Bangalore from Chennai?")
    assert route.source == "Chennai"
    assert route.destination == "Bangalore"


def test_route_arrow_and_dash() -> None:
    route1 = route_service.extract_route("Chennai → Bangalore")
    assert route1.source == "Chennai"
    assert route1.destination == "Bangalore"

    route2 = route_service.extract_route("Chennai -> Bangalore")
    assert route2.source == "Chennai"
    assert route2.destination == "Bangalore"

    route3 = route_service.extract_route("Chennai - Bangalore")
    assert route3.source == "Chennai"
    assert route3.destination == "Bangalore"


def test_route_city_pair_bus() -> None:
    route = route_service.extract_route("Chennai Bangalore bus")
    assert route.source == "Chennai"
    assert route.destination == "Bangalore"


def test_route_single_endpoints() -> None:
    route_src = route_service.extract_route("I am travelling from Chennai")
    assert route_src.source == "Chennai"
    assert route_src.destination is None

    route_dest = route_service.extract_route("I want to go to Bangalore")
    assert route_dest.destination == "Bangalore"
    assert route_dest.source is None


def test_route_typo_tolerance() -> None:
    assert route_service.normalize_city("Bangaluru") == "Bengaluru"
    assert route_service.normalize_city("Banglore") == "Bangalore"
    assert route_service.normalize_city("Chennaii") == "Chennai"
    assert route_service.normalize_city("Hydrabad") == "Hyderabad"
    assert route_service.normalize_city("Coimbator") == "Coimbatore"
    assert route_service.normalize_city("Mysur") == "Mysore"
    assert route_service.normalize_city("Bombay") == "Mumbai"

    route = route_service.extract_route("Banglore to Hydrabad")
    assert route.source == "Bangalore"
    assert route.destination == "Hyderabad"


def test_route_does_not_overmatch_arbitrary_words() -> None:
    assert route_service.extract_route("Find me a bus").source is None
    assert route_service.extract_route("Only AC bus").source is None
    assert route_service.extract_route("Cheapest option please").source is None
    assert route_service.extract_route("Hello how are you").source is None


# =====================================================================
# PART 3: DATE NLP (ORDINALS, IN A WEEK, STANDALONE WEEKDAYS, CORRECTIONS)
# =====================================================================


def test_date_ordinals() -> None:
    # 25th September, September 25th
    ref = extract_date_reference("Can I get a bus for 25th September?")
    assert ref is not None
    assert "25th september" in ref.lower()

    resolved = resolve_calendar_date("25th September", reference_date=REFERENCE_DATE)
    assert resolved == date(2026, 9, 25)

    resolved2 = resolve_calendar_date("September 25th", reference_date=REFERENCE_DATE)
    assert resolved2 == date(2026, 9, 25)


def test_date_in_a_week() -> None:
    ref = extract_date_reference("I need a bus in a week")
    assert ref == "in a week"

    resolved = resolve_calendar_date("in a week", reference_date=REFERENCE_DATE)
    assert resolved == date(2026, 7, 29)


def test_date_standalone_weekday() -> None:
    # REFERENCE_DATE is Wednesday (2026-07-22)
    # Friday is +2 days (2026-07-24)
    ref = extract_date_reference("I need a bus for Friday")
    assert ref == "friday"

    resolved = resolve_calendar_date("friday", reference_date=REFERENCE_DATE)
    assert resolved == date(2026, 7, 24)

    # Next occurrence if same day: Wednesday -> +7 days
    resolved_wed = resolve_calendar_date("wednesday", reference_date=REFERENCE_DATE)
    assert resolved_wed == date(2026, 7, 29)


def test_date_conversational_corrections_and_phrases() -> None:
    ref1 = extract_date_reference("How about Saturday instead?")
    assert ref1 == "saturday"

    ref2 = extract_date_reference("Make that tomorrow")
    assert ref2 == "tomorrow"

    ref3 = extract_date_reference("Change the date to Friday")
    assert ref3 == "friday"

    ref4 = extract_date_reference("I meant tomorrow, not Friday")
    assert ref4 == "tomorrow"


# =====================================================================
# PART 4 & PART 6: FILTERS, NEGATIONS & PRICE RANGES
# =====================================================================


def test_filter_not_ac_maps_to_non_ac() -> None:
    current = ChatParameters()
    result = query_refinement_service.refine("not AC", current, ChatParameters())
    assert result.parameters.filters.get("bus_type") == "Non-AC"

    result2 = query_refinement_service.refine("without AC", current, ChatParameters())
    assert result2.parameters.filters.get("bus_type") == "Non-AC"


def test_filter_negation_does_not_add_positive_volvo() -> None:
    current = ChatParameters(filters={"bus_type": "Volvo"})
    # don't show Volvo
    res1 = query_refinement_service.refine("don't show Volvo", current, ChatParameters())
    assert "bus_type" not in res1.parameters.filters

    # anything except Volvo
    res2 = query_refinement_service.refine("anything except Volvo", current, ChatParameters())
    assert "bus_type" not in res2.parameters.filters

    # remove Volvo
    res3 = query_refinement_service.refine("remove Volvo", current, ChatParameters())
    assert "bus_type" not in res3.parameters.filters


def test_filter_remove_ac() -> None:
    current = ChatParameters(filters={"bus_type": "AC"})
    res1 = query_refinement_service.refine("remove AC", current, ChatParameters())
    assert "bus_type" not in res1.parameters.filters

    res2 = query_refinement_service.refine("don't filter by AC anymore", current, ChatParameters())
    assert "bus_type" not in res2.parameters.filters


def test_filter_price_ranges() -> None:
    current = ChatParameters()
    res = query_refinement_service.refine("between 500 and 800", current, ChatParameters())
    assert res.parameters.filters.get("minimum_price") == 500
    assert res.parameters.filters.get("maximum_price") == 800

    res2 = query_refinement_service.refine("show buses under 700", current, ChatParameters())
    assert res2.parameters.filters.get("maximum_price") == 700


def test_filter_sorting_phrases() -> None:
    current = ChatParameters()
    res1 = query_refinement_service.refine("what's the cheapest option?", current, ChatParameters())
    assert res1.sort_by == "price"
    assert res1.sort_order == "asc"

    res2 = query_refinement_service.refine("which one is fastest?", current, ChatParameters())
    assert res2.sort_by == "departure_time"
    assert res2.sort_order == "asc"


# =====================================================================
# PART 7: CORRECTIONS
# =====================================================================


def test_route_correction_reversal() -> None:
    route = route_service.extract_route("Actually Bangalore to Chennai")
    assert route.source == "Bangalore"
    assert route.destination == "Chennai"
    assert route.is_correction is True


def test_route_correction_single_field() -> None:
    route = route_service.extract_route(
        "Sorry, destination is Hyderabad",
        current_source="Chennai",
        current_destination="Bangalore",
    )
    assert route.destination == "Hyderabad"
    assert route.source == "Chennai"
    assert route.is_correction is True


def test_route_change_x_to_y() -> None:
    route = route_service.extract_route(
        "Change Bangalore to Coimbatore",
        current_source="Chennai",
        current_destination="Bangalore",
    )
    assert route.destination == "Coimbatore"
    assert route.source == "Chennai"
    assert route.is_correction is True


# =====================================================================
# PART 8 & PART 11: INTEGRATION TESTS WITH CLIENT (CLEAR_SEARCH & AMBIGUITY)
# =====================================================================


client = TestClient(app)


def test_ambiguous_date_only_without_route_prompts_for_route(monkeypatch) -> None:
    async def fake_ai(message: str = "", **kwargs):
        return AIAnalysisResult(
            intent=ChatIntent.SEARCH_BUS,
            reply="Sure — where would you like to travel from and to?",
            parameters=ChatParameters(travel_date="tomorrow"),
        )

    monkeypatch.setattr(chat_route.ai_service, "analyze_message", fake_ai)

    # New conversation, user only says "tomorrow"
    response = client.post(
        "/api/chat",
        json={"message": "tomorrow", "conversation_id": "test-ambiguous-conv"},
    )
    assert response.status_code == 200
    data = response.json()
    # Must ask where to travel, not invent a route
    assert "where would you like to travel" in data["reply"].lower()
    assert data["parameters"]["source"] is None
    assert data["parameters"]["destination"] is None
    assert data["parameters"]["travel_date"] == "tomorrow"


def test_clear_search_resets_context(monkeypatch) -> None:
    conv_id = "test-clear-search-conv"
    chat_route.conversation_service.clear_context(conv_id)

    async def fake_ai(message: str = "", **kwargs):
        if "New Search" in message:
            return AIAnalysisResult(
                intent=ChatIntent.CLEAR_SEARCH,
                reply="Search has been reset.",
                parameters=ChatParameters(),
            )
        return AIAnalysisResult(
            intent=ChatIntent.SEARCH_BUS,
            reply="Found buses.",
            parameters=ChatParameters(
                source="Chennai",
                destination="Bangalore",
                travel_date="tomorrow",
            ),
        )

    monkeypatch.setattr(chat_route.ai_service, "analyze_message", fake_ai)

    # Turn 1: Search route
    client.post(
        "/api/chat",
        json={"message": "Chennai to Bangalore tomorrow", "conversation_id": conv_id},
    )

    # Turn 2: Clear search
    response = client.post(
        "/api/chat",
        json={"message": "New Search", "conversation_id": conv_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "clear_search"
    assert data["parameters"]["source"] is None
    assert data["parameters"]["destination"] is None
    assert data["parameters"]["travel_date"] is None
    assert len(data["trips"]) == 0
