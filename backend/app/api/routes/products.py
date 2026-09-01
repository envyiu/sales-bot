from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.product import (
    ProductDetailResponse,
    ProductFilters,
    ProductListItem,
    ProductListResponse,
    ProductSpecResponse,
    InventoryResponse,
)
from app.services.catalog import get_product_by_slug, list_products


router = APIRouter()


def _to_list_item(product) -> ProductListItem:
    return ProductListItem(
        id=product.id,
        slug=product.slug,
        name=product.name,
        brand=product.brand,
        model=product.model,
        price_vnd=product.price_vnd,
        image_url=product.image_url,
        release_year=product.release_year,
        ram_gb=product.spec.ram_gb,
        storage_gb=product.spec.storage_gb,
        stock_quantity=product.inventory.quantity,
    )


def _to_detail_response(product) -> ProductDetailResponse:
    spec = product.spec
    return ProductDetailResponse(
        id=product.id,
        slug=product.slug,
        name=product.name,
        brand=product.brand,
        model=product.model,
        price_vnd=product.price_vnd,
        description=product.description,
        image_url=product.image_url,
        release_year=product.release_year,
        is_active=product.is_active,
        spec=ProductSpecResponse(
            chipset=spec.chipset,
            ram_gb=spec.ram_gb,
            storage_gb=spec.storage_gb,
            screen_size_inches=float(spec.screen_size_inches),
            screen_type=spec.screen_type,
            refresh_rate_hz=spec.refresh_rate_hz,
            battery_mah=spec.battery_mah,
            charging_watt=spec.charging_watt,
            rear_camera=spec.rear_camera,
            front_camera=spec.front_camera,
            os=spec.os,
            gaming_score=float(spec.gaming_score),
            camera_score=float(spec.camera_score),
            battery_score=float(spec.battery_score),
            performance_score=float(spec.performance_score),
            display_score=float(spec.display_score),
        ),
        inventory=InventoryResponse(quantity=product.inventory.quantity),
    )


@router.get("", response_model=ProductListResponse, summary="List active catalog products")
async def list_catalog_products(
    filters: Annotated[ProductFilters, Query()],
    session: AsyncSession = Depends(get_db),
) -> ProductListResponse:
    result = await list_products(session, filters)
    return ProductListResponse(
        items=[_to_list_item(product) for product in result.items],
        total=result.total,
        limit=filters.limit,
        offset=filters.offset,
    )


@router.get(
    "/{slug}",
    response_model=ProductDetailResponse,
    summary="Get an active product by slug",
)
async def get_catalog_product(
    slug: str,
    session: AsyncSession = Depends(get_db),
) -> ProductDetailResponse:
    product = await get_product_by_slug(session, slug)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return _to_detail_response(product)
