from collections.abc import Sequence
from functools import lru_cache
from math import isfinite
from typing import Literal

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import get_settings


EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSION = 768
DOCUMENT_TASK_TYPE = "RETRIEVAL_DOCUMENT"
QUERY_TASK_TYPE = "RETRIEVAL_QUERY"
EmbeddingTaskType = Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]


class EmbeddingError(RuntimeError):
    """Base error for embedding configuration, provider, or shape failures."""


class EmbeddingConfigurationError(EmbeddingError):
    """Raised when embeddings cannot be configured locally."""


class EmbeddingProviderError(EmbeddingError):
    """Raised when Gemini Embedding 2 cannot answer the request."""


class EmbeddingDimensionError(EmbeddingError):
    """Raised when the provider returns a vector of an unexpected shape."""


@lru_cache(maxsize=2)
def get_embeddings(task_type: EmbeddingTaskType) -> GoogleGenerativeAIEmbeddings:
    settings = get_settings()
    if not settings.google_api_key:
        raise EmbeddingConfigurationError("Google API key is not configured")

    try:
        return GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model or EMBEDDING_MODEL,
            api_key=settings.google_api_key,
            task_type=task_type,
            output_dimensionality=EMBEDDING_DIMENSION,
        )
    except Exception as exc:
        raise EmbeddingConfigurationError(
            "Gemini embedding client configuration is invalid"
        ) from exc


def validate_embedding(vector: Sequence[float]) -> list[float]:
    if len(vector) != EMBEDDING_DIMENSION:
        raise EmbeddingDimensionError(
            f"Expected {EMBEDDING_DIMENSION} embedding values, got {len(vector)}"
        )
    if not all(isinstance(value, (int, float)) and isfinite(float(value)) for value in vector):
        raise EmbeddingDimensionError("Embedding contains a non-finite value")
    return [float(value) for value in vector]


def validate_embeddings(vectors: Sequence[Sequence[float]]) -> list[list[float]]:
    return [validate_embedding(vector) for vector in vectors]


async def embed_documents(texts: Sequence[str]) -> list[list[float]]:
    if not texts:
        return []
    try:
        vectors = await get_embeddings(DOCUMENT_TASK_TYPE).aembed_documents(list(texts))
        return validate_embeddings(vectors)
    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingProviderError("Gemini document embedding failed") from exc


async def embed_query(query: str) -> list[float]:
    try:
        vector = await get_embeddings(QUERY_TASK_TYPE).aembed_query(query)
        return validate_embedding(vector)
    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingProviderError("Gemini query embedding failed") from exc
