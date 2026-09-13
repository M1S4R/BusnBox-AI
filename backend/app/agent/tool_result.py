from typing import Any

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    success: bool
    tool_name: str
    message: str | None = None
    data: dict[str, Any] = Field(
        default_factory=dict
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    @classmethod
    def ok(
        cls,
        *,
        tool_name: str,
        message: str | None = None,
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ToolResult":
        return cls(
            success=True,
            tool_name=tool_name,
            message=message,
            data=data or {},
            metadata=metadata or {},
        )

    @classmethod
    def fail(
        cls,
        *,
        tool_name: str,
        message: str,
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ToolResult":
        return cls(
            success=False,
            tool_name=tool_name,
            message=message,
            data=data or {},
            metadata=metadata or {},
        )