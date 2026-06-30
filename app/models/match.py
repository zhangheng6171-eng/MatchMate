"""
Match 匹配关系模型
记录用户之间的滑动行为与双向匹配关系
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, UniqueConstraint, Index

from app.core.database import Base


class SwipeType(str, enum.Enum):
    like = "like"
    pass_ = "pass"
    super_like = "super_like"


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )

    # 标准化：确保 user1_id < user2_id (字典序)
    user1_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user2_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 双方决策
    user1_decision: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True, comment="user1 是否喜欢 user2"
    )
    user2_decision: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True, comment="user2 是否喜欢 user1"
    )

    # 是否形成双向匹配
    is_mutual: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否互相喜欢（双方都点了 like）"
    )
    matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="双向匹配形成时间"
    )

    # 滑动类型
    swipe_type: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="like / pass / super_like"
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
        UniqueConstraint("user1_id", "user2_id", name="uq_match_pair"),
        Index("idx_match_user1", "user1_id"),
        Index("idx_match_user2", "user2_id"),
        Index("idx_match_mutual", "is_mutual"),
    )

    def __repr__(self) -> str:
        return f"<Match({self.user1_id} ↔ {self.user2_id}, mutual={self.is_mutual})>"
