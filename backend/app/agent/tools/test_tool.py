from typing import Any

from app.agent.tool_result import ToolResult
from app.agent.tools.base_tool import BaseTool


class TestTool(BaseTool):
    name = "test"
    description = (
        "Temporary tool used to verify "
        "the dispatcher."
    )

    async def execute(
        self,
        context: dict[str, Any],
    ) -> ToolResult:
        return ToolResult.ok(
            tool_name=self.name,
            message="Test tool executed successfully.",
            data={
                "received_context": context,
            },
        )