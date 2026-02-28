# pyright: basic

import uuid
from typing import Any, Awaitable, Callable

from app.agents.types import ToolCallResult, ToolDefinition

ToolHandler = Callable[[dict[str, Any]], Awaitable[str]]


class ToolRegistry:
    def __init__(self, definitions: list[ToolDefinition] | None = None):
        self._handlers: dict[str, ToolHandler] = {}
        self._definitions: dict[str, ToolDefinition] = {}
        for defn in definitions or []:
            self._definitions[defn.name] = defn

    def register(self, name: str, handler: ToolHandler) -> None:
        self._handlers[name] = handler
        if name not in self._definitions:
            self._definitions[name] = ToolDefinition(
                name=name,
                description=f"Tool: {name}",
            )

    async def execute(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        handler = self._handlers.get(name)
        if not handler:
            return ToolCallResult(
                tool_call_id=str(uuid.uuid4()),
                result=f"No handler registered for tool '{name}'.",
                is_error=True,
            )

        try:
            result = await handler(args)
            return ToolCallResult(tool_call_id=str(uuid.uuid4()), result=result)
        except Exception as exc:
            return ToolCallResult(
                tool_call_id=str(uuid.uuid4()),
                result=str(exc),
                is_error=True,
            )

    def get_definitions(self) -> list[ToolDefinition]:
        return list(self._definitions.values())
