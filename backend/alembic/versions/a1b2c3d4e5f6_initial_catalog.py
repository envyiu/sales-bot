"""create initial smartphone catalog schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-09-01 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "products",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("brand", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("price_vnd", sa.BigInteger(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("release_year", sa.SmallInteger(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("price_vnd >= 0", name="ck_products_price_non_negative"),
        sa.CheckConstraint(
            "release_year IS NULL OR release_year BETWEEN 2000 AND 2100",
            name="ck_products_release_year_reasonable",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_products_slug"),
    )
    op.create_index("ix_products_brand", "products", ["brand"], unique=False)
    op.create_index("ix_products_is_active", "products", ["is_active"], unique=False)

    op.create_table(
        "product_specs",
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("chipset", sa.String(length=255), nullable=False),
        sa.Column("ram_gb", sa.SmallInteger(), nullable=False),
        sa.Column("storage_gb", sa.Integer(), nullable=False),
        sa.Column("screen_size_inches", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("screen_type", sa.String(length=100), nullable=False),
        sa.Column("refresh_rate_hz", sa.SmallInteger(), nullable=False),
        sa.Column("battery_mah", sa.Integer(), nullable=False),
        sa.Column("charging_watt", sa.SmallInteger(), nullable=False),
        sa.Column("rear_camera", sa.String(length=255), nullable=False),
        sa.Column("front_camera", sa.String(length=255), nullable=False),
        sa.Column("os", sa.String(length=100), nullable=False),
        sa.Column("gaming_score", sa.Numeric(precision=3, scale=1), nullable=False),
        sa.Column("camera_score", sa.Numeric(precision=3, scale=1), nullable=False),
        sa.Column("battery_score", sa.Numeric(precision=3, scale=1), nullable=False),
        sa.Column("performance_score", sa.Numeric(precision=3, scale=1), nullable=False),
        sa.Column("display_score", sa.Numeric(precision=3, scale=1), nullable=False),
        sa.CheckConstraint("ram_gb >= 0", name="ck_product_specs_ram_non_negative"),
        sa.CheckConstraint("storage_gb >= 0", name="ck_product_specs_storage_non_negative"),
        sa.CheckConstraint(
            "screen_size_inches > 0",
            name="ck_product_specs_screen_size_positive",
        ),
        sa.CheckConstraint(
            "refresh_rate_hz > 0",
            name="ck_product_specs_refresh_rate_positive",
        ),
        sa.CheckConstraint("battery_mah >= 0", name="ck_product_specs_battery_non_negative"),
        sa.CheckConstraint(
            "charging_watt >= 0",
            name="ck_product_specs_charging_non_negative",
        ),
        sa.CheckConstraint(
            "gaming_score >= 0 AND gaming_score <= 10",
            name="ck_product_specs_gaming_score_range",
        ),
        sa.CheckConstraint(
            "camera_score >= 0 AND camera_score <= 10",
            name="ck_product_specs_camera_score_range",
        ),
        sa.CheckConstraint(
            "battery_score >= 0 AND battery_score <= 10",
            name="ck_product_specs_battery_score_range",
        ),
        sa.CheckConstraint(
            "performance_score >= 0 AND performance_score <= 10",
            name="ck_product_specs_performance_score_range",
        ),
        sa.CheckConstraint(
            "display_score >= 0 AND display_score <= 10",
            name="ck_product_specs_display_score_range",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_product_specs_product_id_products",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("product_id"),
    )

    op.create_table(
        "inventory",
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("quantity >= 0", name="ck_inventory_quantity_non_negative"),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_inventory_product_id_products",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("product_id"),
    )


def downgrade() -> None:
    op.drop_table("inventory")
    op.drop_table("product_specs")
    op.drop_index("ix_products_is_active", table_name="products")
    op.drop_index("ix_products_brand", table_name="products")
    op.drop_table("products")
    op.execute("DROP EXTENSION IF EXISTS vector")
