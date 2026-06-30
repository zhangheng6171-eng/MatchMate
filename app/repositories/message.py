"""消息 Repository"""
from sqlalchemy import select, or_, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message, MessageStatus
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self):
        super().__init__(Message)

    async def get_conversation(
        self, db: AsyncSession, user_id: str, other_id: str, limit: int = 50
    ) -> list[Message]:
        """获取两人之间的聊天记录"""
        result = await db.execute(
            select(Message)
            .where(
                and_(
                    or_(
                        and_(Message.sender_id == user_id, Message.receiver_id == other_id),
                        and_(Message.sender_id == other_id, Message.receiver_id == user_id),
                    ),
                    # 不显示双方都已删除的消息
                    ~and_(
                        Message.is_deleted_by_sender == True,
                        Message.is_deleted_by_receiver == True,
                    ),
                )
            )
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def mark_as_read(
        self, db: AsyncSession, message_ids: list[str]
    ) -> int:
        """标记消息为已读"""
        from datetime import datetime, timezone
        result = await db.execute(
            select(Message).where(
                and_(
                    Message.id.in_(message_ids),
                    Message.status != MessageStatus.read,
                )
            )
        )
        msg_list = result.scalars().all()
        now = datetime.now(timezone.utc)
        count = 0
        for msg in msg_list:
            msg.status = MessageStatus.read
            msg.read_at = now
            count += 1
        await db.flush()
        return count

    async def get_unread_count(
        self, db: AsyncSession, user_id: str
    ) -> int:
        """获取未读消息数"""
        result = await db.execute(
            select(func.count()).select_from(Message).where(
                and_(
                    Message.receiver_id == user_id,
                    Message.status == MessageStatus.sent,
                )
            )
        )
        return result.scalar() or 0

    async def recall_message(
        self, db: AsyncSession, message_id: str, user_id: str
    ) -> Message | None:
        """撤回消息（仅发送方）"""
        from datetime import datetime, timezone
        result = await db.execute(
            select(Message).where(
                and_(Message.id == message_id, Message.sender_id == user_id)
            )
        )
        msg = result.scalar_one_or_none()
        if msg:
            msg.is_recalled = True
            msg.recalled_at = datetime.now(timezone.utc)
            await db.flush()
        return msg

    async def delete_message(
        self, db: AsyncSession, message_id: str, user_id: str, is_sender: bool
    ) -> bool:
        """单方面删除消息"""
        result = await db.execute(
            select(Message).where(Message.id == message_id)
        )
        msg = result.scalar_one_or_none()
        if msg is None:
            return False
        if is_sender:
            msg.is_deleted_by_sender = True
        else:
            msg.is_deleted_by_receiver = True
        await db.flush()
        return True

    async def get_conversations(
        self, db: AsyncSession, user_id: str
    ) -> list[dict]:
        """获取会话列表（最近一条消息 + 未读数）"""
        # 使用原生 SQL 获取每个会话的最新消息
        query = text("""
            SELECT DISTINCT ON (
                CASE WHEN sender_id = :uid THEN receiver_id ELSE sender_id END
            )
                CASE WHEN sender_id = :uid THEN receiver_id ELSE sender_id END AS other_id,
                content,
                created_at,
                (SELECT COUNT(*) FROM messages m2
                 WHERE m2.receiver_id = :uid
                   AND m2.sender_id = CASE WHEN sender_id = :uid THEN receiver_id ELSE sender_id END
                   AND m2.status = 'sent'
                ) AS unread_count
            FROM messages
            WHERE (sender_id = :uid OR receiver_id = :uid)
              AND NOT (is_deleted_by_sender = true AND is_deleted_by_receiver = true)
            ORDER BY
                CASE WHEN sender_id = :uid THEN receiver_id ELSE sender_id END,
                created_at DESC
        """)
        result = await db.execute(query, {"uid": user_id})
        conversations = []
        for row in result:
            conversations.append({
                "other_user_id": row[0],
                "last_message": row[1],
                "last_message_time": row[2],
                "unread_count": row[3],
            })
        return conversations


message_repo = MessageRepository()
