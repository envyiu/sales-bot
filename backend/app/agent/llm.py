from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import get_settings


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
