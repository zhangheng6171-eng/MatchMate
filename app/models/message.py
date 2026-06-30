"""
Message 聊天消息模型
存储好友间的即时通讯消息
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Text, Boolean, DateTime, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Index

from app.core.database import Base


class MessageType(str, enum.Enum):
    text = "text"
    image = "image"
    system = "system"


class MessageStatus(str, enum.Enum):
    sent = "sent"
    delivered = "delivered"
    read = "read"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )
    sender_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    receiver_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 消息内容
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="消息内容"
    )
    message_type: Mapped[MessageType] = mapped_column(
        SAEnum(MessageType, name="message_type_enum", create_type=False),
        default=MessageType.text,
    )

    # 消息状态
    status: Mapped[MessageStatus] = mapped_column(
        SAEnum(MessageStatus, name="message_status_enum", create_type=False),
        default=MessageStatus.sent,
        comment="sent / delivered / read"
    )
    is_recalled: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否已撤回"
    )
    is_deleted_by_sender: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="发送方是否已删除"
    )
    is_deleted_by_receiver: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="接收方是否已删除"
    )

    # 时间戳
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="已读时间"
    )
    recalled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="撤回时间"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("idx_message_conversation", "sender_id", "receiver_id"),
        Index("idx_message_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Message({self.sender_id} → {self.receiver_id}: {self.content[:20]})>"
