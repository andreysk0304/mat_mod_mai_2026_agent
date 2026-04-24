from __future__ import annotations

from typing import Callable

from agent.types import JsonDict, ToolDefinition, ToolHandler


def tool(
    *,
    name: str,
    description: str,
    parameters: JsonDict,
) -> Callable[[ToolHandler], ToolDefinition]:
    def decorator(handler: ToolHandler) -> ToolDefinition:
        return ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
        )

    return decorator


__all__ = ["JsonDict", "ToolDefinition", "tool"]

