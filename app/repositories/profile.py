"""用户资料 Repository"""
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[Profile]):
    def __init__(self):
        super().__init__(Profile)

    async def get_by_user_id(self, db: AsyncSession, user_id: str) -> Profile | None:
        result = await db.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def find_nearby(
        self,
        db: AsyncSession,
        exclude_user_id: str,
        exclude_swiped_ids: list[str] | None = None,
        limit: int = 20,
    ) -> list[Profile]:
        """查询附近公开的用户资料"""
        query = select(Profile).where(
            and_(
                Profile.user_id != exclude_user_id,
                Profile.is_profile_public == True,
            )
        )
        if exclude_swiped_ids:
            query = query.where(Profile.user_id.notin_(exclude_swiped_ids))

        query = query.limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


profile_repo = ProfileRepository()
