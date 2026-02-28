# pyright: basic, reportMissingImports=false

import httpx

from app.agents.types import AgentConfig, Message, ToolCall, ToolCallFunction
from app.config import settings


async def call_llm(messages: list[Message], config: AgentConfig) -> Message:
    api_key = settings.mistral_api_key
    if not api_key:
        raise ValueError("MISTRAL_API_KEY is required")

    base_url = settings.mistral_base_url
    model = config.model or settings.mistral_model

    payload: dict = {
        "model": model,
        "messages": [_message_to_dict(m) for m in messages],
    }

    if config.tools:
        payload["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in config.tools
        ]

    if config.temperature is not None:
        payload["temperature"] = config.temperature
    if config.max_tokens is not None:
        payload["max_tokens"] = config.max_tokens

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{base_url}/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json=payload,
            timeout=60.0,
        )

    if resp.status_code != 200:
        raise RuntimeError(f"LLM request failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})

    tool_calls = None
    if raw_tools := msg.get("tool_calls"):
        tool_calls = [
            ToolCall(
                id=tc.get("id", "unknown"),
                function=ToolCallFunction(
                    name=tc.get("function", {}).get("name", "unknown"),
                    arguments=tc.get("function", {}).get("arguments", "{}"),
                ),
            )
            for tc in raw_tools
        ]

    return Message(
        role="assistant",
        content=msg.get("content", ""),
        tool_calls=tool_calls,
    )


def _message_to_dict(m: Message) -> dict:
    payload: dict = {"role": m.role, "content": m.content}
    if m.tool_call_id:
        payload["tool_call_id"] = m.tool_call_id
    if m.tool_calls:
        payload["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in m.tool_calls
        ]
    return payload
