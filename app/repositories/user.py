"""用户认证 Repository"""
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_phone(self, db: AsyncSession, phone: str) -> User | None:
        result = await db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def get_by_login(self, db: AsyncSession, login: str) -> User | None:
        """通过手机号或邮箱查找用户"""
        result = await db.execute(
            select(User).where(or_(User.email == login, User.phone == login))
        )
        return result.scalar_one_or_none()

    async def update_refresh_token_version(
        self, db: AsyncSession, user: User
    ) -> None:
        user.refresh_token_version += 1
        await db.flush()


user_repo = UserRepository()
