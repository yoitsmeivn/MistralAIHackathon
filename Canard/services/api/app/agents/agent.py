# pyright: basic

import json

from app.agents.memory import trim_messages
from app.agents.tools import ToolRegistry
from app.agents.types import (
    AgentConfig,
    AgentTurnResult,
    ConversationState,
    Message,
)
from app.lib.mistral import call_llm


async def run_agent_turn(
    input_text: str,
    state: ConversationState,
    config: AgentConfig,
) -> AgentTurnResult:
    has_system = any(message.role == "system" for message in state.messages)
    messages = (
        list(state.messages)
        if has_system
        else [Message(role="system", content=config.system_prompt), *state.messages]
    )

    messages.append(Message(role="user", content=input_text))

    tool_registry = ToolRegistry(config.tools or [])
    tool_calls_made: list[dict[str, str]] = []
    output = ""

    for _ in range(3):
        assistant_msg = await call_llm(messages, config)

        if not assistant_msg.tool_calls:
            messages.append(assistant_msg)
            output = assistant_msg.content
            break

        messages.append(assistant_msg)

        for tool_call in assistant_msg.tool_calls:
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                args = {}

            result = await tool_registry.execute(tool_call.function.name, args)
            tool_calls_made.append(
                {
                    "name": tool_call.function.name,
                    "args": tool_call.function.arguments,
                    "result": result.result,
                }
            )
            messages.append(
                Message(
                    role="tool",
                    content=result.result,
                    tool_call_id=tool_call.id,
                )
            )

    updated_state = ConversationState(messages=messages)
    updated_state = trim_messages(updated_state, config.max_messages)

    return AgentTurnResult(
        output=output,
        updated_state=updated_state,
        tool_calls_made=tool_calls_made if tool_calls_made else None,
    )
