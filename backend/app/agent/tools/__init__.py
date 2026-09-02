"""Business tools exposed to the Gemini model."""

from app.agent.tools.inventory import InventoryInput, check_inventory
from app.agent.tools.product_detail import ProductDetailInput, get_product_detail
from app.agent.tools.retrieve_product_knowledge import (
    RetrieveProductKnowledgeInput,
    retrieve_product_knowledge,
)
from app.agent.tools.search_products import (
    ProductPriorities,
    SearchProductsInput,
    search_products,
)

TOOLS = [
    search_products,
    get_product_detail,
    check_inventory,
    retrieve_product_knowledge,
]

__all__ = [
    "InventoryInput",
    "ProductDetailInput",
    "ProductPriorities",
    "RetrieveProductKnowledgeInput",
    "SearchProductsInput",
    "TOOLS",
    "check_inventory",
    "get_product_detail",
    "retrieve_product_knowledge",
    "search_products",
]
