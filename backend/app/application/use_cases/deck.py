"""
Deck 用例 —— 约会候选推荐
来源：Connectly (dating-platform-api) application/use_cases/deck.py
许可证：MIT（适配改编）
适配变更：
  - telegram_id → user_id (UUID)
  - Redis 缓存可选（支持纯 DB 模式）
  - 添加兼容性排序
"""
from uuid import UUID

from app.domain.entities.user import UserEntity, UserDistanceEntity
from app.domain.exceptions import NoCandidatesFound
from app.domain.services.bounding_box import bounding_box
from app.domain.services.haversine import haversine
from app.domain.services.compatibility import calculate_compatibility


class UserDeckUseCase:
    """
    用户约会推荐列表用例。

    流程：
    1. 尝试从 Redis 缓存获取候选
    2. 缓存未命中 → 从数据库查询：
        a. 计算边界框
        b. 按偏好 + 边界框查询候选
        c. 排除已滑动用户
        d. 地理距离计算和过滤
        e. 计算兼容性评分
        f. 按评分降序排列
    3. 返回下一个候选
    """

    MAX_DECK_SIZE = 20
    RADIUS_STEPS_KM = [5, 10, 15, 20, 30]

    def __init__(self, candidate_repo, swipe_repo, cache=None):
        self.candidate_repo = candidate_repo
        self.swipe_repo = swipe_repo
        self.cache = cache  # 可选：Redis 缓存

    async def next(self, user: UserEntity) -> UserDistanceEntity:
        """获取下一个候选用户"""
        cache_key = f"deck:{user.id}"

        # 1. 尝试从缓存获取
        if self.cache:
            cached = await self.cache.lpop(cache_key)
            if cached:
                return cached

        # 2. 缓存未命中 → 重建 Deck
        candidates = await self._build_deck(user)

        if not candidates:
            raise NoCandidatesFound()

        # 3. 写入缓存
        if self.cache:
            await self.cache.delete(cache_key)
            await self.cache.rpush(cache_key, candidates)

        return candidates[0]

    async def _build_deck(self, user: UserEntity) -> list[UserDistanceEntity]:
        """构建候选推荐列表"""
        bbox = bounding_box(
            user.latitude, user.longitude, self.RADIUS_STEPS_KM[-1]
        )

        # 查询候选用户
        raw_candidates = await self.candidate_repo.find_by_preferences_and_bbox(
            user, bbox
        )

        # 排除已滑动用户
        swiped_ids = await self.swipe_repo.get_swiped_user_ids(user.id)
        candidates = [c for c in raw_candidates if c.id not in swiped_ids]

        if not candidates:
            return []

        # 计算地理距离 + 兼容性评分
        results = []
        for c in candidates:
            distance_km = haversine(
                user.latitude, user.longitude,
                c.latitude, c.longitude,
            )
            # 按半径步进过滤
            within_radius = any(distance_km <= r for r in self.RADIUS_STEPS_KM)
            if not within_radius:
                continue

            compat_score = calculate_compatibility(
                user.to_dict(), c.to_dict(),
            )

            results.append(
                UserDistanceEntity.from_user(c, distance_km, compat_score)
            )

        # 按兼容性评分降序排列
        results.sort(key=lambda x: x.compatibility_score, reverse=True)

        return results[:self.MAX_DECK_SIZE]
