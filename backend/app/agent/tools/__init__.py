"""Business tools exposed to the Gemini model."""

from app.agent.tools.inventory import InventoryInput, check_inventory
from app.agent.tools.product_detail import ProductDetailInput, get_product_detail
from app.agent.tools.search_products import (
    ProductPriorities,
    SearchProductsInput,
    search_products,
)

TOOLS = [search_products, get_product_detail, check_inventory]

__all__ = [
    "InventoryInput",
    "ProductDetailInput",
    "ProductPriorities",
    "SearchProductsInput",
    "TOOLS",
    "check_inventory",
    "get_product_detail",
    "search_products",
]
