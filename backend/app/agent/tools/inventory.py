from pydantic import BaseModel, Field
from langchain_core.tools import tool


class InventoryInput(BaseModel):
    product_id: int = Field(gt=0)


@tool(args_schema=InventoryInput)
def check_inventory(product_id: int) -> dict[str, object]:
    """Check current database inventory for one active product by ID."""

    raise RuntimeError(
        "check_inventory must be executed by the request-scoped tool dispatcher"
    )
