from app.agents.types import ConversationState, Message


def create_initial_state(system_prompt: str | None = None) -> ConversationState:
    messages: list[Message] = []
    if system_prompt:
        messages.append(Message(role="system", content=system_prompt))
    return ConversationState(messages=messages)


def trim_messages(state: ConversationState, max_messages: int) -> ConversationState:
    if max_messages <= 0 or len(state.messages) <= max_messages:
        return state

    if state.messages and state.messages[0].role == "system":
        system_msg = state.messages[0]
        rest = state.messages[1:]
        return ConversationState(
            messages=[system_msg] + rest[-max_messages:],
            summary=state.summary,
            metadata=state.metadata,
        )

    return ConversationState(
        messages=state.messages[-max_messages:],
        summary=state.summary,
        metadata=state.metadata,
    )
