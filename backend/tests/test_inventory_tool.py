from datetime import date
from unittest.mock import AsyncMock

import pytest
from app.agent.tool_registry import create_tool_dispatcher
from app.agent.tools.inventory_tool import InventoryTool
from app.schemas.inventory import (
    InventorySearchRequest,
    InventorySearchResult,
)


@pytest.mark.asyncio
async def test_inventory_tool_searches_trips() -> None:
    mock_inventory_service = AsyncMock()

    search_request = InventorySearchRequest(
        source="Chennai",
        destination="Bengaluru",
        travel_date=date(2026, 8, 1),
    )

    expected_result = InventorySearchResult(
        source="Chennai",
        destination="Bengaluru",
        travel_date=date(2026, 8, 1),
        provider="mock",
        total_results=0,
        page=1,
        page_size=10,
        total_pages=0,
        trips=[],
    )

    mock_inventory_service.search_trips.return_value = expected_result

    tool = InventoryTool(
        inventory_service=mock_inventory_service,
    )

    result = await tool.execute(
        {
            "search_request": search_request,
        }
    )

    assert result.success is True
    assert result.tool_name == "inventory"
    assert result.message == "Inventory search completed."
    assert result.data["search_result"] == expected_result

    mock_inventory_service.search_trips.assert_awaited_once_with(
        search_request
    )


@pytest.mark.asyncio
async def test_inventory_tool_rejects_missing_request() -> None:
    mock_inventory_service = AsyncMock()

    tool = InventoryTool(
        inventory_service=mock_inventory_service,
    )

    result = await tool.execute({})

    assert result.success is False
    assert result.tool_name == "inventory"
    assert result.message is not None
    assert "InventorySearchRequest" in result.message

    mock_inventory_service.search_trips.assert_not_awaited()


@pytest.mark.asyncio
async def test_inventory_tool_rejects_invalid_request_type() -> None:
    mock_inventory_service = AsyncMock()

    tool = InventoryTool(
        inventory_service=mock_inventory_service,
    )

    result = await tool.execute(
        {
            "search_request": {
                "source": "Chennai",
                "destination": "Bengaluru",
                "travel_date": "2026-08-01",
            }
        }
    )

    assert result.success is False
    assert result.tool_name == "inventory"
    assert result.message is not None

    mock_inventory_service.search_trips.assert_not_awaited()


def test_inventory_tool_is_registered() -> None:
    dispatcher = create_tool_dispatcher()

    assert dispatcher.has_tool("inventory") is True

    tool = dispatcher.get_tool("inventory")

    assert isinstance(tool, InventoryTool)
    assert tool.name == "inventory"