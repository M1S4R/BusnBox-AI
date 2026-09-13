from app.core.config import settings
from app.integrations.inventory.base import InventoryProvider
from app.integrations.inventory.company import CompanyInventoryProvider
from app.integrations.inventory.mock import MockInventoryProvider


def create_inventory_provider(
    provider_name: str | None = None,
) -> InventoryProvider:
    """Create the configured inventory provider."""

    resolved_provider = (
        provider_name or settings.inventory_provider
    ).strip().lower()

    if resolved_provider == "mock":
        return MockInventoryProvider()

    if resolved_provider == "company":
        return CompanyInventoryProvider()

    raise ValueError(
        f"Unsupported inventory provider: {resolved_provider!r}. "
        "Expected 'mock' or 'company'."
    )
