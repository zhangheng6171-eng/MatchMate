"""
用户匹配 API 路由 (Supabase REST API 版本)
- 滑动（like/pass/super_like）
- 获取匹配列表
- 获取已滑过的用户ID

2026-07-01: SQLAlchemy → Supabase REST API 迁移，适配 Vercel Serverless
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_current_user_supabase
from app.core.supabase_client import supabase
from app.schemas.match import MatchResponse, MutualMatchResponse

router = APIRouter(prefix="/api/match", tags=["匹配系统"])


@router.post("/swipe")
async def swipe_user(
    target_user_id: str = Query(..., description="目标用户ID"),
    swipe_type: str = Query("like", pattern="^(like|pass|super_like)$", description="滑动类型"),
    current_user: dict = Depends(get_current_user_supabase),
):
    """用户滑动（like / pass / super_like）"""
    me = current_user["id"]

    if target_user_id == me:
        raise HTTPException(status_code=400, detail="不能对自己滑动")

    # 校验目标用户存在且激活
    users = await supabase.select("users", filters={"id": target_user_id})
    if not users:
        raise HTTPException(status_code=404, detail="目标用户不存在")
    target = users[0]
    if not target.get("is_active", True):
        raise HTTPException(status_code=403, detail="目标用户账户已被禁用")

    # 标准化 ID 顺序（用户1 < 用户2）
    u1, u2 = sorted([me, target_user_id])
    is_user1 = me == u1
    decision = swipe_type in ("like", "super_like")

    # 查找已有记录
    existing = await supabase.select("matches", filters={"user1_id": u1, "user2_id": u2})

    now = datetime.now(timezone.utc).isoformat()

    if not existing:
        # 创建新的匹配记录
        match_id = str(uuid.uuid4())
        match_data = {
            "id": match_id,
            "user1_id": u1,
            "user2_id": u2,
            "swipe_type": swipe_type,
            "is_mutual": False,
            "created_at": now,
            "updated_at": now,
        }
        if is_user1:
            match_data["user1_decision"] = decision
        else:
            match_data["user2_decision"] = decision

        await supabase.insert("matches", match_data)
        is_mutual = False
        match_id_final = match_id
    else:
        match = existing[0]
        match_id_final = match["id"]

        # 更新决策
        update_data = {
            "swipe_type": swipe_type,
            "updated_at": now,
        }
        if is_user1:
            update_data["user1_decision"] = decision
            other_decision = match.get("user2_decision")
        else:
            update_data["user2_decision"] = decision
            other_decision = match.get("user1_decision")

        # 检测双向匹配
        is_mutual = decision and bool(other_decision)
        if is_mutual:
            update_data["is_mutual"] = True
            update_data["matched_at"] = now

        await supabase.update("matches", update_data, {"id": match_id_final})

    result = {"match_id": match_id_final, "is_mutual": is_mutual}
    if is_mutual:
        result["message"] = "恭喜！你们互相喜欢，可以开始聊天了！"
        result["matched_user_id"] = target_user_id

    return result


@router.get("/mutual")
async def get_mutual_matches(
    current_user: dict = Depends(get_current_user_supabase),
):
    """获取互相关注的匹配列表"""
    me = current_user["id"]

    # 查询所有 is_mutual=true 且当前用户参与的记录
    or_filter = f"(user1_id.eq.{me},user2_id.eq.{me})"
    matches = await supabase.select(
        "matches",
        columns="*",
        extra_params={"or": or_filter, "is_mutual": "eq.true"},
        order="matched_at.desc",
    )

    if not matches:
        return []

    result = []
    for m in matches:
        other_id = m["user2_id"] if m["user1_id"] == me else m["user1_id"]

        # 获取对方昵称
        profiles_data = await supabase.select("profiles", filters={"user_id": other_id})
        nickname = profiles_data[0].get("nickname") if profiles_data else None

        result.append(MutualMatchResponse(
            match_id=m["id"],
            matched_user_id=other_id,
            matched_user_nickname=nickname,
            matched_at=m.get("matched_at"),
        ))

    return result


@router.get("/swiped")
async def get_swiped_ids(
    current_user: dict = Depends(get_current_user_supabase),
):
    """获取已滑过的用户 ID 列表"""
    me = current_user["id"]

    or_filter = f"(user1_id.eq.{me},user2_id.eq.{me})"
    matches = await supabase.select(
        "matches",
        columns="user1_id,user2_id",
        extra_params={"or": or_filter},
    )

    if not matches:
        return []

    swiped = set()
    for m in matches:
        if m["user1_id"] == me:
            swiped.add(m["user2_id"])
        else:
            swiped.add(m["user1_id"])

    return list(swiped)
