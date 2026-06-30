"""
Swipe 领域实体
来源：Connectly (dating-platform-api) domain/entities/swipe.py
许可证：MIT（适配改编）
适配变更：
  - telegram_id → user_id (UUID)
  - 新增 swipe_type 字段（like/pass/super_like）
"""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class SwipeEntity:
    """滑动行为实体"""
    liker_id: UUID
    liked_id: UUID
    decision: bool           # True=like, False=pass
    swipe_type: str = "like"  # "like" | "pass" | "super_like"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class NormalizedSwipeEntity:
    """
    标准化滑动实体（确保 user1_id < user2_id）
    避免同一对用户产生两条记录
    """
    user1_id: UUID
    user2_id: UUID
    decision: bool
    liker_is_user1: bool
    swipe_type: str = "like"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FullSwipeEntity:
    """完整滑动记录（含双向决策）"""
    id: UUID
    user1_id: UUID
    user2_id: UUID
    user1_decision: bool | None = None
    user2_decision: bool | None = None
    is_match: bool = False
    matched_at: datetime | None = None


@dataclass
class InboxSwipe:
    """收件箱通知实体（某人喜欢了你）"""
    from_user_id: UUID
    from_user_id_decision: bool
    to_user_id: UUID
    to_user_id_decision: bool | None
    created_at: datetime = field(default_factory=datetime.utcnow)
