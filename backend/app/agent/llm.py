from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from app.agent.tools import TOOLS
from app.core.config import get_settings


class LLMConfigurationError(RuntimeError):
    """Raised when a Gemini client cannot be constructed from configuration."""


@lru_cache(maxsize=4)
def get_llm(model_id: str) -> ChatGoogleGenerativeAI:
    """Return one cached Gemini client per configured model ID."""

    settings = get_settings()
    if not settings.google_api_key:
        raise LLMConfigurationError("Google API key is not configured")

    try:
        return ChatGoogleGenerativeAI(
            model=model_id,
            api_key=settings.google_api_key,
            temperature=0.3,
            # Fallback policy belongs to model_router, not LangChain retries.
            max_retries=0,
        )
    except Exception as exc:
        raise LLMConfigurationError("Gemini client configuration is invalid") from exc


@lru_cache(maxsize=4)
def get_llm_with_tools(model_id: str):
    """Return a cached model client bound to the Task 006 advisor tools."""

    try:
        return get_llm(model_id).bind_tools(TOOLS)
    except Exception as exc:
        raise LLMConfigurationError("Gemini tool configuration is invalid") from exc
