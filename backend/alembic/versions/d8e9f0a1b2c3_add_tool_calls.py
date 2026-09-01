"""add tool call observability

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-09-02 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d8e9f0a1b2c3"
down_revision: Union[str, None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tool_calls",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_call_id", sa.String(length=255), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column(
            "arguments",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "result",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('success', 'error')",
            name="ck_tool_calls_status_allowed",
        ),
        sa.CheckConstraint(
            "duration_ms >= 0",
            name="ck_tool_calls_duration_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name="fk_tool_calls_conversation_id_conversations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tool_calls_conversation_id",
        "tool_calls",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        "ix_tool_calls_tool_name",
        "tool_calls",
        ["tool_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_tool_calls_tool_name", table_name="tool_calls")
    op.drop_index("ix_tool_calls_conversation_id", table_name="tool_calls")
    op.drop_table("tool_calls")
