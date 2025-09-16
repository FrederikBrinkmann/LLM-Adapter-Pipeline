from __future__ import annotations

from typing import Protocol


class BaseLLM(Protocol):
    """Interface that all LLM adapters must implement."""

    model_id: str
    display_name: str
    supports_streaming: bool

    async def generate_structured(self, *, text: str) -> dict:
        """Return a structured representation derived from free text."""


class LLMError(RuntimeError):
    """Raised when the adapter cannot satisfy the request."""


__all__ = ["BaseLLM", "LLMError"]
