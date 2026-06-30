"""消息相关 Pydantic 模型"""
from datetime import datetime
from pydantic import BaseModel


class MessageSend(BaseModel):
    receiver_id: str
    content: str
    message_type: str = "text"


class MessageResponse(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    content: str
    message_type: str
    status: str
    is_recalled: bool
    created_at: datetime
    read_at: datetime | None = None

    model_config = {"from_attributes": True}


class MessageUpdateStatus(BaseModel):
    message_ids: list[str]
    status: str  # delivered / read


class ConversationBrief(BaseModel):
    other_user_id: str
    other_user_nickname: str | None = None
    other_user_avatar: str | None = None
    last_message: str | None = None
    last_message_time: datetime | None = None
    unread_count: int = 0
