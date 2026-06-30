"""基础 Repository 抽象"""
from typing import Any, Generic, TypeVar
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """通用 Repository 基类"""

    def __init__(self, model: type[T]):
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: str) -> T | None:
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, **kwargs) -> T:
        obj = self.model(**kwargs)
        db.add(obj)
        await db.flush()
        return obj

    async def delete(self, db: AsyncSession, id: str) -> bool:
        obj = await self.get_by_id(db, id)
        if obj is None:
            return False
        await db.delete(obj)
        await db.flush()
        return True

    async def count(self, db: AsyncSession) -> int:
        result = await db.execute(select(func.count()).select_from(self.model))
        return result.scalar() or 0
