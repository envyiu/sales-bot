import json
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Awaitable, Callable
from uuid import uuid4

from langchain_core.messages import ToolMessage
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools.inventory import InventoryInput
from app.agent.tools.product_detail import ProductDetailInput
from app.agent.tools.retrieve_product_knowledge import RetrieveProductKnowledgeInput
from app.agent.tools.search_products import ProductPriorities, SearchProductsInput
from app.models import Product
from app.rag.retriever import document_to_retrieval_hit, retrieve_product_knowledge
from app.services.catalog import (
    AdvisorSearchCriteria,
    advisor_candidate_to_dict,
    get_product_by_id,
    search_products_for_advisor,
)


@dataclass(frozen=True, slots=True)
class ToolExecution:
    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    status: str
    duration_ms: int

    def to_message(self) -> ToolMessage:
        return ToolMessage(
            content=json.dumps(self.result, ensure_ascii=False, separators=(",", ":")),
            tool_call_id=self.tool_call_id,
            name=self.tool_name,
        )

    @property
    def products(self) -> list[dict[str, Any]]:
        if self.tool_name != "search_products" or self.status != "success":
            return []
        products = self.result.get("products", [])
        return products if isinstance(products, list) else []


ToolHandler = Callable[[AsyncSession, BaseModel], Awaitable[dict[str, Any]]]


async def _run_search_products(
    session: AsyncSession,
    arguments: BaseModel,
) -> dict[str, Any]:
    payload = arguments  # validated by the dispatcher before this function runs
    assert isinstance(payload, SearchProductsInput)
    priority_values = payload.priorities or ProductPriorities()
    priority_weights = tuple(
        (name, value)
        for name, value in priority_values.model_dump().items()
        if value > 0
    )
    criteria = AdvisorSearchCriteria(
        brands=tuple(payload.brands or ()),
        min_price=payload.min_price,
        max_price=payload.max_price,
        min_ram=payload.min_ram,
        min_storage=payload.min_storage,
        priority_weights=tuple(
            (name, Decimal(str(value)))
            for name, value in priority_weights
        ),
        limit=payload.limit,
    )
    candidates = await search_products_for_advisor(session, criteria)
    return {
        "products": [
            {
                "result_position": position,
                **advisor_candidate_to_dict(candidate),
            }
            for position, candidate in enumerate(candidates, start=1)
        ],
    }


def _product_detail_payload(product: Product) -> dict[str, Any]:
    if product.spec is None or product.inventory is None:
        return {"found": False, "product_id": product.id}

    spec = product.spec
    return {
        "found": True,
        "id": product.id,
        "slug": product.slug,
        "name": product.name,
        "brand": product.brand,
        "model": product.model,
        "price_vnd": product.price_vnd,
        "description": product.description,
        "image_url": product.image_url,
        "release_year": product.release_year,
        "chipset": spec.chipset,
        "ram_gb": spec.ram_gb,
        "storage_gb": spec.storage_gb,
        "screen_size_inches": float(spec.screen_size_inches),
        "screen_type": spec.screen_type,
        "refresh_rate_hz": spec.refresh_rate_hz,
        "battery_mah": spec.battery_mah,
        "charging_watt": spec.charging_watt,
        "rear_camera": spec.rear_camera,
        "front_camera": spec.front_camera,
        "os": spec.os,
        "gaming_score": float(spec.gaming_score),
        "camera_score": float(spec.camera_score),
        "battery_score": float(spec.battery_score),
        "performance_score": float(spec.performance_score),
        "display_score": float(spec.display_score),
    }


async def _run_product_detail(
    session: AsyncSession,
    arguments: BaseModel,
) -> dict[str, Any]:
    payload = arguments
    assert isinstance(payload, ProductDetailInput)
    product = await get_product_by_id(session, payload.product_id)
    if product is None:
        return {"found": False, "product_id": payload.product_id}
    return _product_detail_payload(product)


async def _run_inventory(
    session: AsyncSession,
    arguments: BaseModel,
) -> dict[str, Any]:
    payload = arguments
    assert isinstance(payload, InventoryInput)
    product = await get_product_by_id(session, payload.product_id)
    if product is None or product.inventory is None:
        return {"found": False, "product_id": payload.product_id}
    return {
        "found": True,
        "product_id": product.id,
        "name": product.name,
        "quantity": product.inventory.quantity,
        "in_stock": product.inventory.quantity > 0,
    }


async def _run_retrieve_product_knowledge(
    session: AsyncSession,
    arguments: BaseModel,
) -> dict[str, Any]:
    payload = arguments
    assert isinstance(payload, RetrieveProductKnowledgeInput)
    documents = await retrieve_product_knowledge(
        session=session,
        query=payload.query,
        product_ids=payload.product_ids,
        top_k=payload.top_k,
    )
    hits = [
        document_to_retrieval_hit(document)
        for document in documents
    ]
    return {"query": payload.query, "hits": hits}


TOOL_HANDLERS: dict[str, tuple[type[BaseModel], ToolHandler]] = {
    "search_products": (SearchProductsInput, _run_search_products),
    "get_product_detail": (ProductDetailInput, _run_product_detail),
    "check_inventory": (InventoryInput, _run_inventory),
    "retrieve_product_knowledge": (
        RetrieveProductKnowledgeInput,
        _run_retrieve_product_knowledge,
    ),
}


def _error_execution(
    *,
    tool_call_id: str,
    tool_name: str,
    arguments: dict[str, Any],
    result: dict[str, Any],
    started_at: float,
) -> ToolExecution:
    return ToolExecution(
        tool_call_id=tool_call_id,
        tool_name=tool_name,
        arguments=arguments,
        result=result,
        status="error",
        duration_ms=max(0, int(round((time.perf_counter() - started_at) * 1000))),
    )


async def execute_tool(
    tool_call: dict[str, Any],
    session: AsyncSession,
) -> ToolExecution:
    """Validate and execute exactly one whitelisted model tool call."""

    started_at = time.perf_counter()
    raw_name = tool_call.get("name") if isinstance(tool_call, dict) else None
    tool_name = str(raw_name or "unknown")
    raw_id = tool_call.get("id") if isinstance(tool_call, dict) else None
    tool_call_id = str(raw_id or f"invalid-{uuid4()}")
    raw_arguments = tool_call.get("args", {}) if isinstance(tool_call, dict) else {}
    arguments = raw_arguments if isinstance(raw_arguments, dict) else {}

    definition = TOOL_HANDLERS.get(tool_name)
    if definition is None:
        return _error_execution(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            arguments=arguments,
            result={
                "error": "unknown_tool",
                "message": "This tool is not available.",
            },
            started_at=started_at,
        )

    input_schema, handler = definition
    try:
        validated = input_schema.model_validate(raw_arguments)
    except (ValidationError, TypeError, ValueError):
        return _error_execution(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            arguments=arguments,
            result={
                "error": "invalid_arguments",
                "message": "Tool arguments failed validation.",
            },
            started_at=started_at,
        )

    safe_arguments = validated.model_dump(mode="json")
    try:
        result = await handler(session, validated)
        json.dumps(result, ensure_ascii=False)
    except Exception:
        await session.rollback()
        return _error_execution(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            arguments=safe_arguments,
            result={
                "error": "tool_execution_failed",
                "message": "Catalog lookup is temporarily unavailable.",
            },
            started_at=started_at,
        )

    return ToolExecution(
        tool_call_id=tool_call_id,
        tool_name=tool_name,
        arguments=safe_arguments,
        result=result,
        status="success",
        duration_ms=max(0, int(round((time.perf_counter() - started_at) * 1000))),
    )
