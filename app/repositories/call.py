"""通话记录 Repository"""
from sqlalchemy import select, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.call import Call, CallStatus
from app.repositories.base import BaseRepository


class CallRepository(BaseRepository[Call]):
    def __init__(self):
        super().__init__(Call)

    async def get_active_call(
        self, db: AsyncSession, user_id: str
    ) -> Call | None:
        """查找用户当前活跃的通话"""
        result = await db.execute(
            select(Call).where(
                or_(Call.caller_id == user_id, Call.callee_id == user_id),
                Call.status.in_([CallStatus.ringing, CallStatus.in_progress]),
            )
        )
        return result.scalar_one_or_none()

    async def get_call_history(
        self, db: AsyncSession, user_id: str, limit: int = 20
    ) -> list[Call]:
        """获取通话历史"""
        result = await db.execute(
            select(Call)
            .where(or_(Call.caller_id == user_id, Call.callee_id == user_id))
            .order_by(desc(Call.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())


call_repo = CallRepository()
