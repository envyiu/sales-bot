from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class ToolCall(Base):
    __tablename__ = "tool_calls"
    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'error')",
            name="ck_tool_calls_status_allowed",
        ),
        CheckConstraint(
            "duration_ms >= 0",
            name="ck_tool_calls_duration_non_negative",
        ),
        Index("ix_tool_calls_conversation_id", "conversation_id"),
        Index("ix_tool_calls_tool_name", "tool_name"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_call_id: Mapped[str] = mapped_column(String(255), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    arguments: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="tool_calls")
