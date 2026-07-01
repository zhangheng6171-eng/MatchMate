"""
会话列表 API 路由 (P3)
- 获取会话列表（最近联系人+未读数+最后消息）
- 清空会话（软删除全部消息）
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user_supabase
from app.core.supabase_client import supabase
from app.schemas.message import (
    ConversationItem,
    ConversationListResponse,
    MessageActionResponse,
)

router = APIRouter(prefix="/api/conversations", tags=["会话管理"])

CONVERSATION_LIST_LIMIT = 50


# ================================================================
#  GET / — 获取会话列表
# ================================================================

@router.get("", response_model=ConversationListResponse)
async def get_conversations(
    current_user: dict = Depends(get_current_user_supabase),
):
    """获取当前用户的所有会话（最近联系人列表）"""
    me = current_user["id"]

    # 获取涉及当前用户的所有消息（我发的 + 我收的）
    # Supabase or 参数格式: (col1.eq.val1,col2.eq.val2)
    or_filter = f"(sender_id.eq.{me},receiver_id.eq.{me})"
    messages = await supabase.select(
        "messages",
        columns="id,sender_id,receiver_id,content,message_type,is_recalled,is_deleted_by_sender,is_deleted_by_receiver,status,created_at",
        extra_params={"or": or_filter},
        limit=500,
        order="created_at.desc",
    )

    if not messages:
        messages = []

    # 按会话分组
    conversations: dict[str, ConversationItem] = {}
    visible_counts: dict[str, int] = {}  # 每个会话可见消息数

    for m in messages:
        # 确定对方ID
        other_id = m["sender_id"] if m["sender_id"] != me else m["receiver_id"]

        # 判断当前用户视角是否已删除
        msg_deleted = (
            (m.get("is_deleted_by_sender") and m["sender_id"] == me)
            or (m.get("is_deleted_by_receiver") and m["receiver_id"] == me)
        )

        if other_id not in conversations:
            # 获取对方用户信息
            users = await supabase.select("users", filters={"id": other_id})
            if not users:
                continue
            user = users[0] if isinstance(users, list) else users

            # 获取对方资料
            profiles = await supabase.select("profiles", filters={"user_id": other_id})
            profile = profiles[0] if (isinstance(profiles, list) and profiles) else None

            conv = ConversationItem(
                user_id=other_id,
                nickname=profile.get("nickname") if profile else None,
                avatar_url=profile.get("avatar_url") if profile else None,
                last_message=None,
                unread_count=0,
            )
            conversations[other_id] = conv
            visible_counts[other_id] = 0

        conv = conversations[other_id]

        # 跳过已删除消息（不计入last_message）
        if msg_deleted:
            continue

        visible_counts[other_id] += 1

        # 设置最后一条消息（第一条是最新的因为倒序）
        if conv.last_message is None:
            content = m.get("content", "")
            if m.get("is_recalled"):
                content = "[消息已撤回]"
            conv.last_message = content
            conv.last_message_time = m.get("created_at")

        # 统计未读数（已删除消息不计未读）
        if m["receiver_id"] == me and m["status"] != "read" and not m.get("is_recalled"):
            conv.unread_count += 1

    # 过滤掉所有消息已删除的会话
    active_conv = [c for c in conversations.values() if visible_counts.get(c.user_id, 0) > 0]

    # 按最后消息时间排序
    conv_list = sorted(
        active_conv,
        key=lambda c: c.last_message_time or "",
        reverse=True,
    )[:CONVERSATION_LIST_LIMIT]

    return ConversationListResponse(conversations=conv_list)


# ================================================================
#  DELETE /{user_id} — 清空与某用户的会话
# ================================================================

@router.delete("/{user_id}", response_model=MessageActionResponse)
async def clear_conversation(
    user_id: str,
    current_user: dict = Depends(get_current_user_supabase),
):
    """清空与指定用户的会话（软删除操作方视角的所有消息）"""
    me = current_user["id"]

    # 查找涉及双方的所有消息（两次简单查询，避免嵌套 and）
    msgs1 = await supabase.select(
        "messages",
        columns="id,sender_id,receiver_id",
        filters={"sender_id": me, "receiver_id": user_id},
        limit=1000,
    )
    if not msgs1:
        msgs1 = []
    msgs2 = await supabase.select(
        "messages",
        columns="id,sender_id,receiver_id",
        filters={"sender_id": user_id, "receiver_id": me},
        limit=1000,
    )
    if not msgs2:
        msgs2 = []
    messages = msgs1 + msgs2

    now = datetime.now(timezone.utc).isoformat()
    cleared = 0
    for m in messages:
        update_data = {"updated_at": now}
        if m["sender_id"] == me:
            if m.get("is_deleted_by_sender"):
                continue
            update_data["is_deleted_by_sender"] = True
        else:
            if m.get("is_deleted_by_receiver"):
                continue
            update_data["is_deleted_by_receiver"] = True

        try:
            await supabase.update("messages", update_data, {"id": m["id"]})
            cleared += 1
        except Exception:
            pass

    return MessageActionResponse(message=f"已清空 {cleared} 条消息")
