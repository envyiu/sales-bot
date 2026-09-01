from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import get_settings
from app.agent.tools import TOOLS


class LLMConfigurationError(RuntimeError):
    """Raised when the configured Gemini client cannot be constructed."""


@lru_cache(maxsize=1)
def get_llm() -> ChatGoogleGenerativeAI:
    settings = get_settings()
    if not settings.google_api_key:
        raise LLMConfigurationError("Google API key is not configured")

    try:
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            api_key=settings.google_api_key,
            temperature=0.3,
            max_retries=2,
        )
    except Exception as exc:
        raise LLMConfigurationError("Gemini client configuration is invalid") from exc


@lru_cache(maxsize=1)
def get_llm_with_tools():
    """Return the cached Gemini client bound to the exact advisor tool set."""

    try:
        return get_llm().bind_tools(TOOLS)
    except Exception as exc:
        raise LLMConfigurationError("Gemini tool configuration is invalid") from exc
