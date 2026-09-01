from dataclasses import dataclass

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Product, ProductSpec
from app.schemas.product import ProductFilters, ProductSort


@dataclass(frozen=True, slots=True)
class ProductSearchResult:
    items: list[Product]
    total: int


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
