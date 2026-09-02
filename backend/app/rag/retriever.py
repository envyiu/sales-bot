from collections.abc import Sequence

from langchain_core.documents import Document
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, ProductDocument
from app.rag.embeddings import embed_query


def document_to_retrieval_hit(
    document: Document,
) -> dict[str, object]:
    metadata = document.metadata
    return {
        "product_id": int(metadata["product_id"]),
        "slug": str(metadata["slug"]),
        "name": str(metadata["name"]),
        "topic": metadata.get("topic"),
        "content": document.page_content,
        "source_name": str(metadata["source_name"]),
        "chunk_index": int(metadata["chunk_index"]),
        "cosine_distance": float(metadata["cosine_distance"]),
    }


async def retrieve_product_knowledge(
    session: AsyncSession,
    query: str,
    product_ids: Sequence[int] | None = None,
    top_k: int = 5,
) -> list[Document]:
    query_vector = await embed_query(query)
    distance = ProductDocument.embedding.cosine_distance(query_vector).label(
        "cosine_distance"
    )
    statement: Select = (
        select(ProductDocument, Product, distance)
        .join(Product, Product.id == ProductDocument.product_id)
        .where(Product.is_active.is_(True))
    )
    if product_ids is not None:
        if not product_ids:
            raise ValueError("product_ids must not be empty")
        statement = statement.where(ProductDocument.product_id.in_(product_ids))

    statement = statement.order_by(distance.asc(), ProductDocument.id.asc()).limit(top_k)
    rows = (await session.execute(statement)).all()
    return [
        Document(
            page_content=document.content,
            metadata={
                "product_id": product.id,
                "slug": product.slug,
                "name": product.name,
                "topic": document.topic,
                "source_name": document.source_name,
                "chunk_index": document.chunk_index,
                "cosine_distance": float(cosine_distance),
            },
        )
        for document, product, cosine_distance in rows
    ]
