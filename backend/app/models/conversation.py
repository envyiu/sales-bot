from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.tool_call import ToolCall


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Message.id",
    )
    tool_calls: Mapped[list["ToolCall"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ToolCall.id",
    )
