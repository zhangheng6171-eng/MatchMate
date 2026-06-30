"""
Swipe 用例 —— 滑动匹配业务编排
来源：Connectly (dating-platform-api) application/use_cases/swipe.py
许可证：MIT（适配改编）
适配变更：
  - telegram_id → user_id (UUID)
  - 新增 swipe_type 支持
  - 新增双向匹配检测
  - InboxService 移除（改为事件钩子）
"""
from uuid import UUID

from app.domain.entities.swipe import (
    FullSwipeEntity,
    InboxSwipe,
    NormalizedSwipeEntity,
    SwipeEntity,
)


class SwipeUserUseCase:
    """
    处理用户滑动行为的用例。

    流程：
    1. 标准化滑动方向（确保 user1_id < user2_id）
    2. 检查是否存在之前的滑动记录
    3. 创建或更新滑动记录
    4. 如果是 like，触发收件箱通知
    5. 检测双向匹配
    """

    def __init__(self, swipe_repo: "ISwipeRepository", inbox_observer=None):
        self.swipe_repo = swipe_repo
        self.inbox_observer = inbox_observer  # 观察者模式替代硬编码

    async def _normalize(self, swipe: SwipeEntity) -> NormalizedSwipeEntity:
        """将滑动标准化：确保 user1_id < user2_id"""
        if swipe.liker_id > swipe.liked_id:
            return NormalizedSwipeEntity(
                user1_id=swipe.liked_id,
                user2_id=swipe.liker_id,
                decision=swipe.decision,
                liker_is_user1=False,
                swipe_type=swipe.swipe_type,
                created_at=swipe.created_at,
            )
        return NormalizedSwipeEntity(
            user1_id=swipe.liker_id,
            user2_id=swipe.liked_id,
            decision=swipe.decision,
            liker_is_user1=True,
            swipe_type=swipe.swipe_type,
            created_at=swipe.created_at,
        )

    async def execute(self, swipe: SwipeEntity) -> FullSwipeEntity:
        normalized = await self._normalize(swipe)

        # 检查是否存在之前的滑动记录
        existing = await self.swipe_repo.get_by_user_ids(
            normalized.user1_id, normalized.user2_id
        )

        if existing is None:
            result = await self.swipe_repo.create(normalized)
        else:
            result = await self.swipe_repo.update(existing, normalized)

        # 确定被滑用户对此用户的决策
        to_user_decision = (
            result.user2_decision
            if result.user2_id == swipe.liked_id
            else result.user1_decision
        )

        # 发送收件箱通知
        if swipe.decision and self.inbox_observer:
            await self.inbox_observer.on_like(
                InboxSwipe(
                    from_user_id=swipe.liker_id,
                    from_user_id_decision=swipe.decision,
                    to_user_id=swipe.liked_id,
                    to_user_id_decision=to_user_decision,
                )
            )

        # 检测双向匹配（互 like）
        is_mutual = await self._check_mutual_match(result, swipe.liker_id)

        return FullSwipeEntity(
            id=result.id,
            user1_id=result.user1_id,
            user2_id=result.user2_id,
            user1_decision=result.user1_decision,
            user2_decision=result.user2_decision,
            is_match=is_mutual,
        )

    async def _check_mutual_match(
        self, result: FullSwipeEntity, liker_id: UUID
    ) -> bool:
        """检查是否形成双向匹配（双方都点了 like）"""
        return (
            result.user1_decision is True
            and result.user2_decision is True
        )
