"""消息模块 Pydantic 模型（P3 扩展）"""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ==== 请求模型 ====

class MessageSendRequest(BaseModel):
    """发送消息请求"""
    receiver_id: str = Field(..., description="接收方用户ID")
    content: str = Field(..., min_length=1, max_length=5000, description="消息内容（1-5000字符）")
    message_type: str = Field("text", description="text / image / system")

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("消息内容不能为空")
        if len(stripped) > 5000:
            raise ValueError("消息内容超过5000字符上限")
        return stripped


class MessageRecallRequest(BaseModel):
    """撤回消息请求"""
    pass


class BatchReadRequest(BaseModel):
    """批量已读请求"""
    message_ids: list[str] = Field(..., min_length=1, max_length=100)


class ConversationClearRequest(BaseModel):
    """清空会话请求"""
    pass


# ==== 响应模型 ====

class MessageResponse(BaseModel):
    """单条消息响应"""
    id: str
    sender_id: str
    receiver_id: str
    content: str
    message_type: str = "text"
    status: str = "sent"
    is_recalled: bool = False
    is_deleted: bool = False  # 当前用户视角是否已删
    read_at: datetime | None = None
    recalled_at: datetime | None = None
    created_at: datetime | None = None

    @classmethod
    def from_db(cls, msg: dict, current_user_id: str) -> "MessageResponse":
        """从数据库记录+当前用户视角构造"""
        is_del_sender = bool(msg.get("is_deleted_by_sender")) and msg.get("sender_id") == current_user_id
        is_del_receiver = bool(msg.get("is_deleted_by_receiver")) and msg.get("receiver_id") == current_user_id
        is_deleted = is_del_sender or is_del_receiver
        content = msg.get("content", "")
        if msg.get("is_recalled"):
            content = "[消息已撤回]"
        return cls(
            id=msg["id"],
            sender_id=msg["sender_id"],
            receiver_id=msg["receiver_id"],
            content=content,
            message_type=msg.get("message_type", "text"),
            status=msg.get("status", "sent"),
            is_recalled=msg.get("is_recalled", False),
            is_deleted=is_deleted,
            read_at=msg.get("read_at"),
            recalled_at=msg.get("recalled_at"),
            created_at=msg.get("created_at"),
        )


class ConversationItem(BaseModel):
    """会话列表项"""
    user_id: str
    nickname: str | None = None
    avatar_url: str | None = None
    last_message: str | None = None
    last_message_time: datetime | None = None
    unread_count: int = 0


class ConversationListResponse(BaseModel):
    """会话列表响应"""
    conversations: list[ConversationItem]


class ConversationMessagesResponse(BaseModel):
    """对话消息列表响应"""
    messages: list[MessageResponse]
    has_more: bool = False


class PollResponse(BaseModel):
    """轮询新消息响应"""
    messages: list[MessageResponse]
    has_more: bool = False


class SendResponse(BaseModel):
    """消息发送响应"""
    message: MessageResponse
    conversation_id: str


class MessageActionResponse(BaseModel):
    """通用操作响应"""
    message: str
    message_id: str | None = None


# ==== 旧版兼容 ====

class MessageSend(MessageSendRequest):
    """消息发送请求（旧版兼容）"""
    pass
