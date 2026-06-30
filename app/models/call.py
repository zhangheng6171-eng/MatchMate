"""
Call 通话记录模型
存储音视频通话的完整记录
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Boolean, DateTime, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Index

from app.core.database import Base


class CallType(str, enum.Enum):
    voice = "voice"
    video = "video"


class CallStatus(str, enum.Enum):
    ringing = "ringing"        # 呼叫中
    in_progress = "in_progress"  # 通话中
    ended = "ended"            # 正常结束
    missed = "missed"          # 未接听
    rejected = "rejected"      # 已拒绝
    busy = "busy"              # 对方忙


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )
    caller_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="主叫方"
    )
    callee_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="被叫方"
    )

    call_type: Mapped[CallType] = mapped_column(
        SAEnum(CallType, name="call_type_enum", create_type=False),
        nullable=False,
        comment="voice / video"
    )
    status: Mapped[CallStatus] = mapped_column(
        SAEnum(CallStatus, name="call_status_enum", create_type=False),
        default=CallStatus.ringing,
    )

    # 通话时长（秒）
    duration_seconds: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=0
    )

    # 时间节点
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="通话开始时间"
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="通话结束时间"
    )

    # 通话质量
    quality_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="通话质量评分 0-100"
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
        Index("idx_call_caller", "caller_id"),
        Index("idx_call_callee", "callee_id"),
        Index("idx_call_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Call({self.caller_id} → {self.callee_id}, {self.call_type})>"
