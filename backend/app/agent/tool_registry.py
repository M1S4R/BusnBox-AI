from app.agent.tool_dispatcher import ToolDispatcher
from app.agent.tools.inventory_tool import InventoryTool
from app.services.inventory_service import (
    inventory_service,
)


def create_tool_dispatcher() -> ToolDispatcher:
    dispatcher = ToolDispatcher()

    dispatcher.register(
        InventoryTool(
            inventory_service=inventory_service,
        )
    )

    return dispatcher


tool_dispatcher = create_tool_dispatcher()