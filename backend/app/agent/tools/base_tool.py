from abc import ABC, abstractmethod
from typing import Any

from app.agent.tool_result import ToolResult


class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    async def execute(
        self,
        context: dict[str, Any],
    ) -> ToolResult:
        """
        Execute the tool using the supplied context.

        Every tool must return a ToolResult.
        """
        raise NotImplementedError