from pydantic import BaseModel, Field, field_validator
from langchain_core.tools import tool


class RetrieveProductKnowledgeInput(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    product_ids: list[int] | None = None
    top_k: int = Field(default=5, ge=1, le=8)

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        query = value.strip()
        if not query:
            raise ValueError("query must not be blank")
        return query

    @field_validator("product_ids")
    @classmethod
    def validate_product_ids(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        if not value:
            raise ValueError("product_ids must not be empty")
        if len(value) > 5:
            raise ValueError("product_ids must contain at most 5 IDs")
        if len(set(value)) != len(value):
            raise ValueError("product_ids must be unique")
        if any(product_id < 1 for product_id in value):
            raise ValueError("product_ids must be positive")
        return value


@tool(args_schema=RetrieveProductKnowledgeInput)
def retrieve_product_knowledge(
    query: str,
    product_ids: list[int] | None = None,
    top_k: int = 5,
) -> dict[str, object]:
    """Retrieve semantic product knowledge about gaming, camera, video, battery, thermals, strengths, weaknesses, and suitable users.

    Do not use this tool as the source of truth for current price, stock, or
    exact structured specifications. Those facts come from catalog tools.
    """

    raise RuntimeError(
        "retrieve_product_knowledge must be executed by the request-scoped tool dispatcher"
    )
