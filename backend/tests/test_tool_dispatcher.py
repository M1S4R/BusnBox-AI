import pytest
from app.agent.tool_dispatcher import (
    DuplicateToolError,
    ToolDispatcher,
    ToolNotFoundError,
)
from app.agent.tools.test_tool import (
    TestTool,
)


@pytest.mark.asyncio
async def test_dispatcher_executes_tool() -> None:
    dispatcher = ToolDispatcher()
    dispatcher.register(TestTool())

    result = await dispatcher.dispatch(
        tool_name="test",
        context={
            "message": "hello",
        },
    )

    assert result.success is True
    assert result.tool_name == "test"
    assert (
        result.data["received_context"]
        ["message"]
        == "hello"
    )


def test_dispatcher_rejects_duplicate_tool() -> None:
    dispatcher = ToolDispatcher()
    dispatcher.register(TestTool())

    with pytest.raises(
        DuplicateToolError
    ):
        dispatcher.register(
            TestTool()
        )


def test_dispatcher_raises_for_unknown_tool() -> None:
    dispatcher = ToolDispatcher()

    with pytest.raises(
        ToolNotFoundError
    ):
        dispatcher.get_tool(
            "missing_tool"
        )


def test_dispatcher_lists_registered_tools() -> None:
    dispatcher = ToolDispatcher()
    dispatcher.register(TestTool())

    tools = dispatcher.list_tools()

    assert len(tools) == 1
    assert tools[0]["name"] == "test"