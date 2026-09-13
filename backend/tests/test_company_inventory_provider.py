from datetime import date

import httpx
import pytest

from app.integrations.inventory.base import (
    InventoryAuthenticationError,
    InventoryResponseError,
)
from app.integrations.inventory.company import (
    CompanyInventoryProvider,
)
from app.schemas.inventory import InventorySearchRequest


@pytest.mark.asyncio
async def test_company_provider_maps_valid_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["source"] == "Chennai"
        assert request.url.params["destination"] == "Bangalore"

        return httpx.Response(
            status_code=200,
            json={
                "source": "Chennai",
                "destination": "Bangalore",
                "travel_date": "2026-07-20",
                "trips": [
                    {
                        "id": "trip-101",
                        "source": "Chennai",
                        "destination": "Bangalore",
                        "departure_time": "2026-07-20T21:30:00",
                        "arrival_time": "2026-07-21T04:00:00",
                        "operator": {
                            "id": "operator-1",
                            "name": "Demo Travels",
                        },
                        "bus": {
                            "id": "bus-1",
                            "name": "Night Rider",
                            "bus_type": "AC Sleeper",
                            "amenities": [
                                "Charging Point",
                                "Blanket",
                            ],
                            "total_seats": 36,
                        },
                        "price": "899.00",
                        "available_seats": 12,
                        "boarding_point": "Koyambedu",
                        "dropping_point": "Majestic",
                        "booking_url": "https://example.com/book/trip-101",
                    }
                ],
            },
        )

    client = httpx.AsyncClient(
        base_url="https://inventory.test",
        transport=httpx.MockTransport(handler),
    )

    provider = CompanyInventoryProvider(client=client)

    try:
        result = await provider.search_trips(
            InventorySearchRequest(
                source="Chennai",
                destination="Bangalore",
                travel_date=date(2026, 7, 20),
            )
        )

        assert result.provider == "company"
        assert len(result.trips) == 1
        assert result.trips[0].operator.name == "Demo Travels"
        assert result.trips[0].available_seats == 12
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_company_provider_rejects_invalid_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "trips": [
                    {
                        "invalid": "missing required fields",
                    }
                ]
            },
        )

    client = httpx.AsyncClient(
        base_url="https://inventory.test",
        transport=httpx.MockTransport(handler),
    )

    provider = CompanyInventoryProvider(client=client)

    try:
        with pytest.raises(InventoryResponseError):
            await provider.search_trips(
                InventorySearchRequest(
                    source="Chennai",
                    destination="Bangalore",
                    travel_date=date(2026, 7, 20),
                )
            )
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_company_provider_handles_authentication_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=401,
            json={"detail": "Invalid API key"},
        )

    client = httpx.AsyncClient(
        base_url="https://inventory.test",
        transport=httpx.MockTransport(handler),
    )

    provider = CompanyInventoryProvider(client=client)

    try:
        with pytest.raises(InventoryAuthenticationError):
            await provider.search_trips(
                InventorySearchRequest(
                    source="Chennai",
                    destination="Bangalore",
                    travel_date=date(2026, 7, 20),
                )
            )
    finally:
        await client.aclose()
