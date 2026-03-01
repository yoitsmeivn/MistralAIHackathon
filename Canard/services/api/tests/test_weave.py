# pyright: reportMissingImports=false
from __future__ import annotations

import asyncio


def test_chat_completion_decorated_without_weave() -> None:
    """The @_op decorator should be a no-op when weave is not initialized.
    chat_completion must remain callable regardless of weave state."""
    from app.integrations.mistral import chat_completion

    assert callable(chat_completion)


def test_app_loads_without_wandb_key() -> None:
    """Importing app.main should succeed even without WANDB_API_KEY.
    The lifespan (which calls weave.init) does not run during import."""
    from app.main import app  # noqa: F401

    assert app is not None


def test_op_fallback_is_identity() -> None:
    """When weave is not initialized, _op from app.agent.loop should be
    an identity decorator — the wrapped function must still work correctly."""
    from app.agent.loop import _op

    @_op
    def add_one(x: int) -> int:
        return x + 1

    assert add_one(41) == 42


def test_op_fallback_works_with_lambda() -> None:
    """_op applied to a lambda must return a callable that returns the expected value."""
    from app.agent.loop import _op

    fn = _op(lambda: 42)
    assert callable(fn)
    assert fn() == 42
