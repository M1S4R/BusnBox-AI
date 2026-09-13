from datetime import date
from decimal import Decimal

import pytest

from app.integrations.inventory.mock import MockInventoryProvider
from app.schemas.inventory import (
    InventorySearchRequest,
    InventorySortBy,
)


@pytest.mark.asyncio
async def test_mock_provider_returns_multiple_trips() -> None:
    provider = MockInventoryProvider()

    result = await provider.search_trips(
        InventorySearchRequest(
            source="Chennai",
            destination="Bangalore",
            travel_date=date(2026, 7, 20),
        )
    )

    assert result.provider == "mock"
    assert result.total_results == 12
    assert len(result.trips) == 10
    assert result.total_pages == 2


@pytest.mark.asyncio
async def test_mock_provider_filters_bus_type() -> None:
    provider = MockInventoryProvider()

    result = await provider.search_trips(
        InventorySearchRequest(
            source="Chennai",
            destination="Bangalore",
            travel_date=date(2026, 7, 20),
            bus_type="AC Sleeper",
            page_size=50,
        )
    )

    assert result.total_results > 0
    assert all(
        trip.bus.bus_type == "AC Sleeper"
        for trip in result.trips
    )


@pytest.mark.asyncio
async def test_mock_provider_filters_operator() -> None:
    provider = MockInventoryProvider()

    result = await provider.search_trips(
        InventorySearchRequest(
            source="Chennai",
            destination="Bangalore",
            travel_date=date(2026, 7, 20),
            operator="BusNBox",
            page_size=50,
        )
    )

    assert result.total_results > 0
    assert all(
        "busnbox" in trip.operator.name.casefold()
        for trip in result.trips
    )


@pytest.mark.asyncio
async def test_mock_provider_filters_maximum_price() -> None:
    provider = MockInventoryProvider()

    result = await provider.search_trips(
        InventorySearchRequest(
            source="Chennai",
            destination="Bangalore",
            travel_date=date(2026, 7, 20),
            maximum_price=Decimal("700.00"),
            page_size=50,
        )
    )

    assert result.total_results > 0
    assert all(
        trip.price <= Decimal("700.00")
        for trip in result.trips
    )


@pytest.mark.asyncio
async def test_mock_provider_filters_minimum_seats() -> None:
    provider = MockInventoryProvider()

    result = await provider.search_trips(
        InventorySearchRequest(
            source="Chennai",
            destination="Bangalore",
            travel_date=date(2026, 7, 20),
            minimum_seats=20,
            page_size=50,
        )
    )

    assert result.total_results > 0
    assert all(
        trip.available_seats >= 20
        for trip in result.trips
    )


@pytest.mark.asyncio
async def test_mock_provider_sorts_by_price() -> None:
    provider = MockInventoryProvider()

    result = await provider.search_trips(
        InventorySearchRequest(
            source="Chennai",
            destination="Bangalore",
            travel_date=date(2026, 7, 20),
            sort_by=InventorySortBy.PRICE,
            page_size=50,
        )
    )

    prices = [trip.price for trip in result.trips]

    assert prices == sorted(prices)


@pytest.mark.asyncio
async def test_mock_provider_sorts_by_duration() -> None:
    provider = MockInventoryProvider()

    result = await provider.search_trips(
        InventorySearchRequest(
            source="Chennai",
            destination="Bangalore",
            travel_date=date(2026, 7, 20),
            sort_by=InventorySortBy.DURATION,
            page_size=50,
        )
    )

    durations = [
        trip.arrival_time - trip.departure_time
        for trip in result.trips
    ]

    assert durations == sorted(durations)


@pytest.mark.asyncio
async def test_mock_provider_paginates_results() -> None:
    provider = MockInventoryProvider()

    first_page = await provider.search_trips(
        InventorySearchRequest(
            source="Chennai",
            destination="Bangalore",
            travel_date=date(2026, 7, 20),
            page=1,
            page_size=5,
        )
    )

    second_page = await provider.search_trips(
        InventorySearchRequest(
            source="Chennai",
            destination="Bangalore",
            travel_date=date(2026, 7, 20),
            page=2,
            page_size=5,
        )
    )

    first_ids = {trip.id for trip in first_page.trips}
    second_ids = {trip.id for trip in second_page.trips}

    assert len(first_page.trips) == 5
    assert len(second_page.trips) == 5
    assert first_ids.isdisjoint(second_ids)
