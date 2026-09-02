"""add product knowledge documents and embeddings

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-09-02 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql


revision: str = "e9f0a1b2c3d4"
down_revision: Union[str, None] = "d8e9f0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_documents",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("topic", sa.String(length=100), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "chunk_index >= 0",
            name="ck_product_documents_chunk_index_non_negative",
        ),
        sa.CheckConstraint(
            "length(btrim(content)) > 0",
            name="ck_product_documents_content_not_blank",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_product_documents_product_id_products",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_id",
            "source_name",
            "chunk_index",
            name="uq_product_documents_product_source_chunk",
        ),
    )
    op.create_index(
        "ix_product_documents_product_id",
        "product_documents",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_product_documents_topic",
        "product_documents",
        ["topic"],
        unique=False,
    )
    op.create_index(
        "ix_product_documents_embedding_hnsw",
        "product_documents",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index(
        "ix_product_documents_embedding_hnsw",
        table_name="product_documents",
    )
    op.drop_index("ix_product_documents_topic", table_name="product_documents")
    op.drop_index("ix_product_documents_product_id", table_name="product_documents")
    op.drop_table("product_documents")
