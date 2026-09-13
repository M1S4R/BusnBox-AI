from typing import Any

from app.integrations.inventory.factory import create_inventory_provider
from app.schemas.ai_intent import IntentExtractionResult


class ToolDispatcher:
    """Dispatch extracted AI intents to the correct backend tool."""

    def __init__(self) -> None:
        self.inventory_provider = create_inventory_provider()

    async def dispatch(
        self,
        intent: IntentExtractionResult,
    ) -> Any:
        """
        Execute the correct backend tool based on the extracted intent.

        Returns:
            Inventory search results for supported intents.
            None when the intent is unsupported or required fields are missing.
        """

        if intent.intent != "search_trip":
            return None

        if intent.missing_fields:
            return None

        parameters = intent.parameters

        if (
            parameters.source is None
            or parameters.destination is None
            or parameters.travel_date is None
        ):
            return None

        return await self.inventory_provider.search(
            source=parameters.source,
            destination=parameters.destination,
            travel_date=parameters.travel_date,
            bus_type=parameters.bus_type,
            max_fare=parameters.max_fare,
        )