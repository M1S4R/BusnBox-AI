from typing import Any

from app.agent.tool_result import ToolResult
from app.agent.tools.base_tool import BaseTool
from app.schemas.inventory import InventorySearchRequest
from app.services.inventory_service import InventoryService


class InventoryTool(BaseTool):
    name = "inventory"
    description = (
        "Search available bus trips through "
        "the configured inventory provider."
    )

    def __init__(
        self,
        inventory_service: InventoryService,
    ) -> None:
        self.inventory_service = inventory_service

    async def execute(
        self,
        context: dict[str, Any],
    ) -> ToolResult:
        search_request = context.get(
            "search_request"
        )

        if not isinstance(
            search_request,
            InventorySearchRequest,
        ):
            return ToolResult.fail(
                tool_name=self.name,
                message=(
                    "The inventory tool requires "
                    "a valid InventorySearchRequest."
                ),
            )

        search_result = (
            await self.inventory_service.search_trips(
                search_request
            )
        )

        return ToolResult.ok(
            tool_name=self.name,
            message="Inventory search completed.",
            data={
                "search_result": search_result,
            },
        )