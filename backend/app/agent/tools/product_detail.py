from pydantic import BaseModel, Field
from langchain_core.tools import tool


class ProductDetailInput(BaseModel):
    product_id: int = Field(gt=0)


@tool(args_schema=ProductDetailInput)
def get_product_detail(product_id: int) -> dict[str, object]:
    """Get authoritative catalog specifications and price for one active product by ID."""

    raise RuntimeError(
        "get_product_detail must be executed by the request-scoped tool dispatcher"
    )
