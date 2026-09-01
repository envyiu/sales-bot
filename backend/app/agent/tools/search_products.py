from pydantic import BaseModel, Field
from langchain_core.tools import tool


class ProductPriorities(BaseModel):
    gaming: float = Field(default=0, ge=0, le=1)
    camera: float = Field(default=0, ge=0, le=1)
    battery: float = Field(default=0, ge=0, le=1)
    performance: float = Field(default=0, ge=0, le=1)
    display: float = Field(default=0, ge=0, le=1)


class SearchProductsInput(BaseModel):
    brands: list[str] | None = None
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    min_ram: int | None = Field(default=None, ge=0)
    min_storage: int | None = Field(default=None, ge=0)
    priorities: ProductPriorities | None = None
    limit: int = Field(default=3, ge=1, le=5)


@tool(args_schema=SearchProductsInput)
def search_products(
    brands: list[str] | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    min_ram: int | None = None,
    min_storage: int | None = None,
    priorities: ProductPriorities | None = None,
    limit: int = 3,
) -> dict[str, object]:
    """Search active store smartphones using budget, specs, and weighted priorities."""

    raise RuntimeError("search_products must be executed by the request-scoped tool dispatcher")
