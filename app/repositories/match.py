"""匹配关系 Repository"""
from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.models.match import Match
from app.repositories.base import BaseRepository


class MatchRepository(BaseRepository[Match]):
    def __init__(self):
        super().__init__(Match)

    async def get_by_user_pair(
        self, db: AsyncSession, user1_id: str, user2_id: str
    ) -> Match | None:
        """查找两个用户之间的匹配记录（标准化顺序）"""
        u1, u2 = sorted([user1_id, user2_id])
        result = await db.execute(
            select(Match).where(
                and_(Match.user1_id == u1, Match.user2_id == u2)
            )
        )
        return result.scalar_one_or_none()

    async def find_or_create(
        self, db: AsyncSession, user1_id: str, user2_id: str
    ) -> Match:
        uuid = __import__("uuid").uuid4()
        u1, u2 = sorted([user1_id, user2_id])
        existing = await self.get_by_user_pair(db, u1, u2)
        if existing:
            return existing
        match = Match(id=str(uuid), user1_id=u1, user2_id=u2)
        db.add(match)
        await db.flush()
        return match

    async def get_swiped_user_ids(
        self, db: AsyncSession, user_id: str
    ) -> list[str]:
        """获取用户已滑过的所有用户 ID"""
        result = await db.execute(
            select(Match.user1_id, Match.user2_id).where(
                or_(Match.user1_id == user_id, Match.user2_id == user_id)
            )
        )
        swiped = set()
        for row in result:
            swiped.add(row[0])
            swiped.add(row[1])
        swiped.discard(user_id)
        return list(swiped)

    async def find_mutual_matches(
        self, db: AsyncSession, user_id: str
    ) -> list[Match]:
        """查询用户的所有双向匹配"""
        result = await db.execute(
            select(Match).where(
                and_(
                    Match.is_mutual == True,
                    or_(Match.user1_id == user_id, Match.user2_id == user_id),
                )
            )
        )
        return list(result.scalars().all())


match_repo = MatchRepository()
