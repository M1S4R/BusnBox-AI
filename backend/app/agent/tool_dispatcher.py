from typing import Any

from app.agent.tool_result import ToolResult
from app.agent.tools.base_tool import BaseTool


class ToolDispatcherError(Exception):
    pass


class ToolNotFoundError(ToolDispatcherError):
    pass


class DuplicateToolError(ToolDispatcherError):
    pass


class ToolDispatcher:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(
        self,
        tool: BaseTool,
    ) -> None:
        tool_name = self._normalize_tool_name(
            tool.name
        )

        if not tool_name:
            raise ValueError(
                "Tool name cannot be empty."
            )

        if tool_name in self._tools:
            raise DuplicateToolError(
                f"Tool '{tool_name}' is already registered."
            )

        self._tools[tool_name] = tool

    def unregister(
        self,
        tool_name: str,
    ) -> None:
        normalized_name = (
            self._normalize_tool_name(
                tool_name
            )
        )

        self._tools.pop(
            normalized_name,
            None,
        )

    def get_tool(
        self,
        tool_name: str,
    ) -> BaseTool:
        normalized_name = (
            self._normalize_tool_name(
                tool_name
            )
        )

        tool = self._tools.get(
            normalized_name
        )

        if tool is None:
            raise ToolNotFoundError(
                f"Tool '{normalized_name}' "
                "is not registered."
            )

        return tool

    def has_tool(
        self,
        tool_name: str,
    ) -> bool:
        normalized_name = (
            self._normalize_tool_name(
                tool_name
            )
        )

        return normalized_name in self._tools

    def list_tools(
        self,
    ) -> list[dict[str, str]]:
        return [
            {
                "name": tool.name,
                "description": (
                    tool.description
                ),
            }
            for tool in self._tools.values()
        ]

    async def dispatch(
        self,
        *,
        tool_name: str,
        context: dict[str, Any],
    ) -> ToolResult:
        tool = self.get_tool(
            tool_name
        )

        try:
            return await tool.execute(
                context
            )

        except ToolDispatcherError:
            raise

        except Exception as exc:
            raise ToolDispatcherError(
                f"Tool '{tool.name}' failed: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

    @staticmethod
    def _normalize_tool_name(
        tool_name: str,
    ) -> str:
        return (
            tool_name
            .strip()
            .casefold()
            .replace("-", "_")
            .replace(" ", "_")
        )


tool_dispatcher = ToolDispatcher()