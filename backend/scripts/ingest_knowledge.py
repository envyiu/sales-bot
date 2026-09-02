import asyncio
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import delete, select

from app.db.session import AsyncSessionLocal, engine
from app.models import Product, ProductDocument
from app.rag.embeddings import embed_documents
from app.rag.splitter import KnowledgeChunk, split_markdown_document


SOURCE_TYPE = "seed_knowledge"
KNOWLEDGE_DIRECTORY = Path(__file__).resolve().parents[1] / "data" / "knowledge"


@dataclass(frozen=True, slots=True)
class ProductIdentity:
    id: int
    slug: str
    name: str


async def _load_product_identities() -> dict[str, ProductIdentity]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product.id, Product.slug, Product.name))
        identities = {
            slug: ProductIdentity(id=product_id, slug=slug, name=name)
            for product_id, slug, name in result.all()
        }
        await session.rollback()
        return identities


def _read_and_split_documents(
    identities: dict[str, ProductIdentity],
) -> list[tuple[ProductIdentity, list[KnowledgeChunk]]]:
    files = sorted(KNOWLEDGE_DIRECTORY.glob("*.md"))
    if not files:
        raise RuntimeError(f"No markdown knowledge files found in {KNOWLEDGE_DIRECTORY}")

    missing_products = sorted(set(identities) - {file.stem for file in files})
    unknown_slugs = sorted(file.stem for file in files if file.stem not in identities)
    if missing_products:
        raise RuntimeError(
            "Missing knowledge files for products: " + ", ".join(missing_products)
        )
    if unknown_slugs:
        raise RuntimeError(
            "Knowledge files reference unknown product slugs: "
            + ", ".join(unknown_slugs)
        )

    documents: list[tuple[ProductIdentity, list[KnowledgeChunk]]] = []
    for file in files:
        identity = identities[file.stem]
        chunks = split_markdown_document(
            file.read_text(encoding="utf-8"),
            source_name=file.name,
            product_name=identity.name,
        )
        documents.append((identity, chunks))
    return documents


async def ingest_knowledge() -> tuple[int, int]:
    identities = await _load_product_identities()
    documents = _read_and_split_documents(identities)
    all_chunks = [chunk for _, chunks in documents for chunk in chunks]

    # Generate the complete replacement corpus before deleting any existing data.
    vectors = await embed_documents([chunk.embedding_text for chunk in all_chunks])
    if len(vectors) != len(all_chunks):
        raise RuntimeError("Embedding provider returned an unexpected document count")

    rows: list[ProductDocument] = []
    for (identity, chunks), chunk_vectors in zip(
        documents,
        _group_vectors(vectors, documents),
        strict=True,
    ):
        for chunk, vector in zip(chunks, chunk_vectors, strict=True):
            rows.append(
                ProductDocument(
                    product_id=identity.id,
                    source_name=chunk.source_name,
                    source_type=SOURCE_TYPE,
                    topic=chunk.topic,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    content_hash=chunk.content_hash,
                    document_metadata=chunk.metadata,
                    embedding=vector,
                )
            )

    async with AsyncSessionLocal.begin() as session:
        await session.execute(
            delete(ProductDocument).where(ProductDocument.source_type == SOURCE_TYPE)
        )
        session.add_all(rows)

    return len(identities), len(rows)


def _group_vectors(
    vectors: list[list[float]],
    documents: list[tuple[ProductIdentity, list[KnowledgeChunk]]],
) -> list[list[list[float]]]:
    grouped: list[list[list[float]]] = []
    offset = 0
    for _, chunks in documents:
        next_offset = offset + len(chunks)
        grouped.append(vectors[offset:next_offset])
        offset = next_offset
    if offset != len(vectors):
        raise RuntimeError("Embedding grouping did not consume all vectors")
    return grouped


async def main() -> None:
    products, chunks = await ingest_knowledge()
    print(f"Ingested {chunks} knowledge chunks for {products} products")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
