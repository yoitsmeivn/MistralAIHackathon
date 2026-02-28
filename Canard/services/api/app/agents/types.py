# pyright: basic

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

MessageRole = Literal["system", "user", "assistant", "tool"]


@dataclass
class Message:
    role: MessageRole
    content: str
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None


@dataclass
class ToolCall:
    id: str
    function: ToolCallFunction


@dataclass
class ToolCallFunction:
    name: str
    arguments: str


@dataclass
class AgentConfig:
    system_prompt: str
    model: str | None = None
    tools: list[ToolDefinition] | None = None
    max_messages: int = 20
    max_tokens: int | None = None
    temperature: float = 0.7


@dataclass
class ConversationState:
    messages: list[Message] = field(default_factory=list)
    summary: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCallResult:
    tool_call_id: str
    result: str
    is_error: bool = False


@dataclass
class AgentTurnResult:
    output: str
    updated_state: ConversationState
    tool_calls_made: list[dict[str, str]] | None = None
