from app.api.routes.chat import (
    should_start_new_search,
)
from app.schemas.chat import ChatParameters


def make_parameters(
    *,
    source: str | None = None,
    destination: str | None = None,
    travel_date: str | None = None,
    filters: dict | None = None,
) -> ChatParameters:
    return ChatParameters(
        source=source,
        destination=destination,
        travel_date=travel_date,
        filters=filters or {},
    )


def test_same_route_does_not_start_new_search() -> None:
    current = make_parameters(
        source="Chennai",
        destination="Bangalore",
        travel_date="tomorrow",
    )

    incoming = make_parameters(
        source="Chennai",
        destination="Bangalore",
        travel_date="2026-07-25",
    )

    result = should_start_new_search(
        current=current,
        incoming=incoming,
    )

    assert result is False


def test_route_comparison_is_case_insensitive() -> None:
    current = make_parameters(
        source="Chennai",
        destination="Bangalore",
    )

    incoming = make_parameters(
        source="chennai",
        destination="bangalore",
    )

    result = should_start_new_search(
        current=current,
        incoming=incoming,
    )

    assert result is False


def test_changed_source_starts_new_search() -> None:
    current = make_parameters(
        source="Chennai",
        destination="Bangalore",
    )

    incoming = make_parameters(
        source="Hyderabad",
        destination="Bangalore",
    )

    result = should_start_new_search(
        current=current,
        incoming=incoming,
    )

    assert result is True


def test_changed_destination_starts_new_search() -> None:
    current = make_parameters(
        source="Chennai",
        destination="Bangalore",
    )

    incoming = make_parameters(
        source="Chennai",
        destination="Coimbatore",
    )

    result = should_start_new_search(
        current=current,
        incoming=incoming,
    )

    assert result is True


def test_partial_incoming_route_does_not_reset_context() -> None:
    current = make_parameters(
        source="Chennai",
        destination="Bangalore",
    )

    incoming = make_parameters(
        destination="Hyderabad",
    )

    result = should_start_new_search(
        current=current,
        incoming=incoming,
    )

    assert result is False


def test_incomplete_current_route_does_not_reset_context() -> None:
    current = make_parameters(
        source="Chennai",
    )

    incoming = make_parameters(
        source="Hyderabad",
        destination="Vizag",
    )

    result = should_start_new_search(
        current=current,
        incoming=incoming,
    )

    assert result is False
