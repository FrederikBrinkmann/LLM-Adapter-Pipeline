from __future__ import annotations

import hashlib
from textwrap import shorten

from .base import BaseLLM


class MockLLM:
    """Simple mock adapter that simulates structured output."""

    supports_streaming = False

    def __init__(self, model_id: str, display_name: str) -> None:
        self.model_id = model_id
        self.display_name = display_name

    async def generate_structured(self, *, text: str) -> dict:
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
        preview = shorten(text, width=120, placeholder="…")
        return {
            "model_id": self.model_id,
            "summary": preview,
            "hash": digest,
            "length": len(text),
        }


__all__ = ["MockLLM"]
