"""
消息模块 API 路由 (P3 即时聊天系统 — HTTP API 版)
- 消息发送与接收
- 对话历史拉取（分页）
- 消息轮询（since_id 增量获取）
- 消息已读标记（单条/批量）
- 消息撤回（2分钟限制）
- 消息删除（软删除）
- 会话列表（最近联系人+未读数）
- 会话清空
"""
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.deps import get_current_user_supabase
from app.core.supabase_client import supabase
from app.schemas.message import (
    MessageSendRequest,
    BatchReadRequest,
    MessageResponse as MsgResponse,
    ConversationItem,
    ConversationListResponse,
    ConversationMessagesResponse,
    PollResponse,
    SendResponse,
    MessageActionResponse,
)

router = APIRouter(prefix="/api/messages", tags=["即时通讯"])

RECALL_WINDOW_MINUTES = 2
CONVERSATION_PAGE_SIZE = 30
CONVERSATION_LIST_LIMIT = 50

# ================================================================
#  POST /send — 发送消息
# ================================================================

@router.post("/send", response_model=SendResponse, status_code=201)
async def send_message(
    req: MessageSendRequest,
    current_user: dict = Depends(get_current_user_supabase),
):
    """发送文本消息"""
    sender_id = current_user["id"]
    receiver_id = req.receiver_id

    if sender_id == receiver_id:
        raise HTTPException(status_code=400, detail="不能给自己发消息")

    # 校验接收方存在且激活
    users = await supabase.select("users", filters={"id": receiver_id})
    if not users:
        raise HTTPException(status_code=404, detail="接收方用户不存在")
    receiver = users[0] if isinstance(users, list) else users
    if not receiver.get("is_active", True):
        raise HTTPException(status_code=403, detail="接收方账户已被禁用")

    # 创建消息
    msg_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    msg_data = {
        "id": msg_id,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "content": req.content,
        "message_type": req.message_type,
        "status": "sent",
        "created_at": now,
        "updated_at": now,
    }

    await supabase.insert("messages", msg_data)

    return SendResponse(
        message=MsgResponse.from_db(msg_data, current_user["id"]),
        conversation_id=receiver_id,
    )


# ================================================================
#  GET /conversation/{user_id} — 获取与某用户的对话
# ================================================================

@router.get("/conversation/{user_id}", response_model=ConversationMessagesResponse)
async def get_conversation(
    user_id: str,
    before_id: str | None = Query(None, description="翻页游标：此消息之前的记录"),
    limit: int = Query(30, ge=1, le=100),
    current_user: dict = Depends(get_current_user_supabase),
):
    """获取与指定用户的双向对话（分页）"""
    me = current_user["id"]

    # 两个简单查询：我发给TA + TA发给我（避免 Supabase or 不支持嵌套 and）
    query1_active = True
    query2_active = True

    # 翻页：获取 before_id 之前的消息
    extra1 = {}
    extra2 = {}
    if before_id:
        ref_msg = await supabase.select("messages", filters={"id": before_id}, single=True)
        if ref_msg:
            created_at = ref_msg.get("created_at", "")
            lt_filter = f"lt.{created_at}"
            extra1["created_at"] = lt_filter
            extra2["created_at"] = lt_filter

    # 查询1: 我发的
    msgs1 = await supabase.select(
        "messages",
        columns="*",
        filters={"sender_id": me, "receiver_id": user_id},
        extra_params=extra1,
        limit=limit + 1,
        order="created_at.desc",
    )
    if not msgs1:
        msgs1 = []

    # 查询2: TA发的
    msgs2 = await supabase.select(
        "messages",
        columns="*",
        filters={"sender_id": user_id, "receiver_id": me},
        extra_params=extra2,
        limit=limit + 1,
        order="created_at.desc",
    )
    if not msgs2:
        msgs2 = []

    # 合并排序
    all_msgs = msgs1 + msgs2
    all_msgs.sort(key=lambda m: m.get("created_at", ""), reverse=True)
    has_more = len(all_msgs) > limit
    result = all_msgs[:limit]

    # 过滤已删除消息（当前用户视角）+ 回填撤回内容
    visible = []
    for m in result:
        # 发送方删除 → 发送方视角不可见
        if m.get("is_deleted_by_sender") and m["sender_id"] == me:
            continue
        # 接收方删除 → 接收方视角不可见
        if m.get("is_deleted_by_receiver") and m["receiver_id"] == me:
            continue
        visible.append(MsgResponse.from_db(m, me))

    return ConversationMessagesResponse(messages=visible, has_more=has_more)


# ================================================================
#  GET /poll — 轮询获取新消息（替代 WebSocket）
# ================================================================

@router.get("/poll", response_model=PollResponse)
async def poll_messages(
    since_id: str | None = Query(None, description="上次获取的最大消息ID"),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user_supabase),
):
    """
    轮询获取发给当前用户的新消息。
    客户端应高频调用（如每2-3秒），传入上次已获取的最新消息ID。
    """
    me = current_user["id"]

    # 查询发给我的消息
    extra_params = {}
    if since_id:
        # 按ID排序：只取比 since_id 更新的
        # Supabase 中我们用 created_at 代替
        ref_msg = await supabase.select("messages", filters={"id": since_id}, single=True)
        if ref_msg:
            extra_params["created_at"] = f"gt.{ref_msg.get('created_at', '')}"

    messages = await supabase.select(
        "messages",
        columns="*",
        filters={"receiver_id": me},
        extra_params=extra_params,
        limit=limit + 1,
        order="created_at.asc",
    )

    if not messages:
        messages = []

    has_more = len(messages) > limit
    result = messages[:limit]

    visible = [MsgResponse.from_db(m, me) for m in result]

    return PollResponse(messages=visible, has_more=has_more)


# ================================================================
#  PUT /{message_id}/read — 标记单条消息已读
# ================================================================

@router.put("/{message_id}/read", response_model=MessageActionResponse)
async def mark_read(
    message_id: str,
    current_user: dict = Depends(get_current_user_supabase),
):
    """标记单条消息为已读（仅接收方可操作）"""
    me = current_user["id"]

    msg = await supabase.select("messages", filters={"id": message_id}, single=True)
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")

    if msg["receiver_id"] != me:
        raise HTTPException(status_code=403, detail="仅接收方可以标记已读")

    if msg["status"] == "read":
        return MessageActionResponse(message="消息已为已读状态", message_id=message_id)

    now = datetime.now(timezone.utc).isoformat()
    await supabase.update(
        "messages",
        {"status": "read", "read_at": now, "updated_at": now},
        {"id": message_id},
    )

    return MessageActionResponse(message="已标记为已读", message_id=message_id)


# ================================================================
#  PUT /read-batch — 批量标记已读
# ================================================================

@router.put("/read-batch", response_model=MessageActionResponse)
async def mark_read_batch(
    req: BatchReadRequest,
    current_user: dict = Depends(get_current_user_supabase),
):
    """批量标记消息为已读"""
    me = current_user["id"]
    now = datetime.now(timezone.utc).isoformat()

    updated = 0
    for mid in req.message_ids:
        msg = await supabase.select("messages", filters={"id": mid}, single=True)
        if not msg:
            continue
        if msg["receiver_id"] != me:
            continue
        if msg["status"] == "read":
            continue
        try:
            await supabase.update(
                "messages",
                {"status": "read", "read_at": now, "updated_at": now},
                {"id": mid},
            )
            updated += 1
        except Exception:
            pass

    return MessageActionResponse(message=f"已标记 {updated} 条消息为已读")


# ================================================================
#  POST /{message_id}/recall — 撤回消息
# ================================================================

@router.post("/{message_id}/recall", response_model=MessageActionResponse)
async def recall_message(
    message_id: str,
    current_user: dict = Depends(get_current_user_supabase),
):
    """撤回消息（2分钟内，仅发送方可操作）"""
    me = current_user["id"]

    msg = await supabase.select("messages", filters={"id": message_id}, single=True)
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")

    if msg["sender_id"] != me:
        raise HTTPException(status_code=403, detail="仅发送方可以撤回消息")

    if msg.get("is_recalled"):
        return MessageActionResponse(message="消息已撤回", message_id=message_id)

    # 2分钟限制
    created = msg.get("created_at", "")
    if created:
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                created = None
        if created and isinstance(created, datetime):
            elapsed = datetime.now(timezone.utc) - created.replace(tzinfo=timezone.utc)
            if elapsed > timedelta(minutes=RECALL_WINDOW_MINUTES):
                raise HTTPException(status_code=400, detail=f"已超过{RECALL_WINDOW_MINUTES}分钟撤回时限")

    now = datetime.now(timezone.utc).isoformat()
    await supabase.update(
        "messages",
        {
            "content": "[消息已撤回]",
            "is_recalled": True,
            "recalled_at": now,
            "updated_at": now,
        },
        {"id": message_id},
    )

    return MessageActionResponse(message="消息已撤回", message_id=message_id)


# ================================================================
#  DELETE /{message_id} — 删除消息（软删除）
# ================================================================

@router.delete("/{message_id}", response_model=MessageActionResponse)
async def delete_message(
    message_id: str,
    current_user: dict = Depends(get_current_user_supabase),
):
    """删除消息（软删除，仅影响操作方视角）"""
    me = current_user["id"]

    msg = await supabase.select("messages", filters={"id": message_id}, single=True)
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")

    now = datetime.now(timezone.utc).isoformat()
    update_data = {"updated_at": now}

    if msg["sender_id"] == me:
        if msg.get("is_deleted_by_sender"):
            return MessageActionResponse(message="消息已删除", message_id=message_id)
        update_data["is_deleted_by_sender"] = True
    elif msg["receiver_id"] == me:
        if msg.get("is_deleted_by_receiver"):
            return MessageActionResponse(message="消息已删除", message_id=message_id)
        update_data["is_deleted_by_receiver"] = True
    else:
        raise HTTPException(status_code=403, detail="无权操作此消息")

    await supabase.update("messages", update_data, {"id": message_id})

    return MessageActionResponse(message="消息已删除", message_id=message_id)
