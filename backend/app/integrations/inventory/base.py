from abc import ABC, abstractmethod

from app.schemas.inventory import (
    InventorySearchRequest,
    InventorySearchResult,
)


class InventoryProviderError(Exception):
    """Base exception for inventory provider failures."""


class InventoryAuthenticationError(InventoryProviderError):
    """Raised when the inventory provider rejects authentication."""


class InventoryUnavailableError(InventoryProviderError):
    """Raised when the provider cannot currently be reached."""


class InventoryResponseError(InventoryProviderError):
    """Raised when the provider returns invalid or unexpected data."""


class InventoryProvider(ABC):
    """Interface implemented by every inventory provider."""

    @abstractmethod
    async def search_trips(
        self,
        search: InventorySearchRequest,
    ) -> InventorySearchResult:
        raise NotImplementedError

    async def close(self) -> None:
        """Release provider resources when required."""
