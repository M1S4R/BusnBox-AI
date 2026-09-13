from datetime import date

import pytest

from app.integrations.inventory.base import (
    InventoryAuthenticationError,
    InventoryProvider,
    InventoryUnavailableError,
)
from app.integrations.inventory.factory import (
    create_inventory_provider,
)
from app.integrations.inventory.mock import MockInventoryProvider
from app.schemas.inventory import (
    InventorySearchRequest,
    InventorySearchResult,
)
from app.services.inventory_service import (
    InventoryService,
    InventoryServiceConfigurationError,
    InventoryServiceUnavailableError,
)


class UnavailableProvider(InventoryProvider):
    async def search_trips(
        self,
        search: InventorySearchRequest,
    ) -> InventorySearchResult:
        raise InventoryUnavailableError("Provider offline")


class AuthenticationFailureProvider(InventoryProvider):
    async def search_trips(
        self,
        search: InventorySearchRequest,
    ) -> InventorySearchResult:
        raise InventoryAuthenticationError("Invalid API key")


def make_search() -> InventorySearchRequest:
    return InventorySearchRequest(
        source="Chennai",
        destination="Bangalore",
        travel_date=date(2026, 7, 20),
    )


def test_factory_creates_mock_provider() -> None:
    provider = create_inventory_provider("mock")
    assert isinstance(provider, MockInventoryProvider)


def test_factory_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError):
        create_inventory_provider("unknown")


@pytest.mark.asyncio
async def test_inventory_service_returns_mock_results() -> None:
    service = InventoryService(
        provider=MockInventoryProvider()
    )

    result = await service.search_trips(make_search())

    assert result.provider == "mock"
    assert result.total_results == 12
    assert result.page == 1
    assert result.page_size == 10
    assert result.total_pages == 2
    assert len(result.trips) == 10

    assert result.trips[0].operator.name == (
        "BusNBox Demo Travels"
    )


@pytest.mark.asyncio
async def test_inventory_service_rejects_same_city() -> None:
    service = InventoryService(
        provider=MockInventoryProvider()
    )

    with pytest.raises(ValueError):
        await service.search_trips(
            InventorySearchRequest(
                source="Chennai",
                destination=" chennai ",
                travel_date=date(2026, 7, 20),
            )
        )


@pytest.mark.asyncio
async def test_inventory_service_maps_unavailable_error() -> None:
    service = InventoryService(
        provider=UnavailableProvider()
    )

    with pytest.raises(InventoryServiceUnavailableError):
        await service.search_trips(make_search())


@pytest.mark.asyncio
async def test_inventory_service_maps_auth_error() -> None:
    service = InventoryService(
        provider=AuthenticationFailureProvider()
    )

    with pytest.raises(
        InventoryServiceConfigurationError
    ):
        await service.search_trips(make_search())
