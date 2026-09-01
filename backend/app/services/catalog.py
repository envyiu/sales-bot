from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping

from sqlalchemy import Select, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Inventory, Product, ProductSpec
from app.schemas.product import ProductFilters, ProductSort


@dataclass(frozen=True, slots=True)
class ProductSearchResult:
    items: list[Product]
    total: int


@dataclass(frozen=True, slots=True)
class AdvisorSearchCriteria:
    """Database-backed criteria used by the advisor tools."""

    brands: tuple[str, ...] = ()
    min_price: int | None = None
    max_price: int | None = None
    min_ram: int | None = None
    min_storage: int | None = None
    priority_weights: tuple[tuple[str, Decimal], ...] = ()
    limit: int = 3


@dataclass(frozen=True, slots=True)
class AdvisorProductCandidate:
    product: Product
    spec: ProductSpec
    inventory: Inventory
    ranking_score: Decimal | None


def _advisor_ranking_expression(
    priority_weights: Mapping[str, Decimal],
):
    total_weight = sum(priority_weights.values(), Decimal("0"))
    if total_weight <= 0:
        return None

    score_columns = {
        "gaming": ProductSpec.gaming_score,
        "camera": ProductSpec.camera_score,
        "battery": ProductSpec.battery_score,
        "performance": ProductSpec.performance_score,
        "display": ProductSpec.display_score,
    }
    expression = literal(Decimal("0"))
    for priority, weight in priority_weights.items():
        column = score_columns.get(priority)
        if column is not None and weight > 0:
            expression = expression + column * literal(weight / total_weight)
    return expression


async def search_products_for_advisor(
    session: AsyncSession,
    criteria: AdvisorSearchCriteria,
) -> list[AdvisorProductCandidate]:
    """Search active catalog products and rank them using stored DB scores."""

    conditions = [Product.is_active.is_(True)]
    normalized_brands = tuple(
        brand.strip().lower() for brand in criteria.brands if brand.strip()
    )
    if normalized_brands:
        conditions.append(func.lower(Product.brand).in_(normalized_brands))
    if criteria.min_price is not None:
        conditions.append(Product.price_vnd >= criteria.min_price)
    if criteria.max_price is not None:
        conditions.append(Product.price_vnd <= criteria.max_price)
    if criteria.min_ram is not None:
        conditions.append(ProductSpec.ram_gb >= criteria.min_ram)
    if criteria.min_storage is not None:
        conditions.append(ProductSpec.storage_gb >= criteria.min_storage)

    ranking_expression = _advisor_ranking_expression(dict(criteria.priority_weights))
    statement = (
        select(Product, ProductSpec, Inventory, ranking_expression)
        if ranking_expression is not None
        else select(Product, ProductSpec, Inventory)
    ).join(ProductSpec, ProductSpec.product_id == Product.id).join(
        Inventory, Inventory.product_id == Product.id
    ).where(*conditions)

    if ranking_expression is not None:
        statement = statement.order_by(
            ranking_expression.desc(),
            Product.release_year.desc().nulls_last(),
            Product.id.desc(),
        )
    else:
        statement = statement.order_by(
            Product.release_year.desc().nulls_last(),
            Product.id.desc(),
        )

    rows = (await session.execute(statement.limit(criteria.limit))).all()
    return [
        AdvisorProductCandidate(
            product=row[0],
            spec=row[1],
            inventory=row[2],
            ranking_score=row[3] if ranking_expression is not None else None,
        )
        for row in rows
    ]


def advisor_candidate_to_dict(candidate: AdvisorProductCandidate) -> dict[str, object]:
    """Convert a DB candidate into compact, JSON-compatible tool data."""

    product = candidate.product
    spec = candidate.spec
    return {
        "id": product.id,
        "slug": product.slug,
        "name": product.name,
        "brand": product.brand,
        "model": product.model,
        "price_vnd": product.price_vnd,
        "image_url": product.image_url,
        "ram_gb": spec.ram_gb,
        "storage_gb": spec.storage_gb,
        "chipset": spec.chipset,
        "battery_mah": spec.battery_mah,
        "gaming_score": float(spec.gaming_score),
        "battery_score": float(spec.battery_score),
        "performance_score": float(spec.performance_score),
        "stock_quantity": candidate.inventory.quantity,
        "ranking_score": (
            float(candidate.ranking_score)
            if candidate.ranking_score is not None
            else None
        ),
    }


def _apply_filters(statement: Select, filters: ProductFilters) -> Select:
    conditions = [Product.is_active.is_(True)]

    if filters.q and filters.q.strip():
        term = f"%{filters.q.strip()}%"
        conditions.append(
            or_(
                Product.name.ilike(term),
                Product.model.ilike(term),
                Product.brand.ilike(term),
            )
        )

    if filters.brand:
        brands = [brand.strip().lower() for brand in filters.brand if brand.strip()]
        if brands:
            conditions.append(func.lower(Product.brand).in_(brands))

    if filters.min_price is not None:
        conditions.append(Product.price_vnd >= filters.min_price)
    if filters.max_price is not None:
        conditions.append(Product.price_vnd <= filters.max_price)

    if filters.min_ram is not None or filters.min_storage is not None:
        statement = statement.join(ProductSpec, ProductSpec.product_id == Product.id)
        if filters.min_ram is not None:
            conditions.append(ProductSpec.ram_gb >= filters.min_ram)
        if filters.min_storage is not None:
            conditions.append(ProductSpec.storage_gb >= filters.min_storage)

    return statement.where(*conditions)


def _apply_sort(statement: Select, sort: ProductSort) -> Select:
    sort_expressions = {
        ProductSort.price_asc: (Product.price_vnd.asc(), Product.id.asc()),
        ProductSort.price_desc: (Product.price_vnd.desc(), Product.id.desc()),
        ProductSort.newest: (
            Product.release_year.desc().nulls_last(),
            Product.id.desc(),
        ),
        ProductSort.name_asc: (Product.name.asc(), Product.id.asc()),
    }
    return statement.order_by(*sort_expressions[sort])


async def list_products(
    session: AsyncSession,
    filters: ProductFilters,
) -> ProductSearchResult:
    count_statement = _apply_filters(
        select(func.count(Product.id)).select_from(Product),
        filters,
    )
    total = int((await session.scalar(count_statement)) or 0)

    products_statement = _apply_sort(
        _apply_filters(
            select(Product)
            .options(
                selectinload(Product.spec),
                selectinload(Product.inventory),
            ),
            filters,
        ),
        filters.sort,
    ).limit(filters.limit).offset(filters.offset)

    products = list((await session.scalars(products_statement)).all())
    return ProductSearchResult(items=products, total=total)


async def get_product_by_slug(
    session: AsyncSession,
    slug: str,
) -> Product | None:
    statement = (
        select(Product)
        .options(
            selectinload(Product.spec),
            selectinload(Product.inventory),
        )
        .where(Product.slug == slug, Product.is_active.is_(True))
    )
    return await session.scalar(statement)


async def get_product_by_id(
    session: AsyncSession,
    product_id: int,
) -> Product | None:
    statement = (
        select(Product)
        .options(
            selectinload(Product.spec),
            selectinload(Product.inventory),
        )
        .where(Product.id == product_id, Product.is_active.is_(True))
    )
    return await session.scalar(statement)
