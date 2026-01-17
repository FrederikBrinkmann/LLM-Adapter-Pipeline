from .ollama import OLLAMA_HANDLER
from .openai import OPENAI_HANDLER

PROVIDER_HANDLERS = {
    "openai": OPENAI_HANDLER,
    "ollama": OLLAMA_HANDLER,
}

__all__ = ["PROVIDER_HANDLERS"]
