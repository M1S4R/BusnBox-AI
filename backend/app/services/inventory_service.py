from app.integrations.inventory.base import (
    InventoryAuthenticationError,
    InventoryProvider,
    InventoryResponseError,
    InventoryUnavailableError,
)
from app.integrations.inventory.factory import (
    create_inventory_provider,
)
from app.schemas.inventory import (
    InventorySearchRequest,
    InventorySearchResult,
)


class InventoryServiceError(Exception):
    """Base exception raised by the inventory service."""


class InventoryServiceUnavailableError(InventoryServiceError):
    """Raised when inventory data cannot currently be retrieved."""


class InventoryServiceConfigurationError(InventoryServiceError):
    """Raised when inventory integration is incorrectly configured."""


class InventoryService:
    def __init__(
        self,
        provider: InventoryProvider | None = None,
    ) -> None:
        self.provider = provider or create_inventory_provider()

    async def search_trips(
        self,
        search: InventorySearchRequest,
    ) -> InventorySearchResult:
        self._validate_search(search)

        try:
            return await self.provider.search_trips(search)

        except InventoryAuthenticationError as exc:
            raise InventoryServiceConfigurationError(
                "Inventory provider authentication failed."
            ) from exc

        except InventoryResponseError as exc:
            raise InventoryServiceUnavailableError(
                "Inventory provider returned unusable data."
            ) from exc

        except InventoryUnavailableError as exc:
            raise InventoryServiceUnavailableError(
                "Inventory provider is currently unavailable."
            ) from exc

    @staticmethod
    def _validate_search(
        search: InventorySearchRequest,
    ) -> None:
        source = search.source.strip().casefold()
        destination = search.destination.strip().casefold()

        if source == destination:
            raise ValueError(
                "Source and destination must be different."
            )

    async def close(self) -> None:
        await self.provider.close()


inventory_service = InventoryService()
