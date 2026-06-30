"""
用户匹配 API 路由
- 滑动（like/pass/super_like）
- 获取匹配列表
- 获取推荐候选人
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.match import Match
from app.repositories.match import match_repo
from app.schemas.match import SwipeRequest, MatchResponse, MutualMatchResponse

router = APIRouter(prefix="/api/match", tags=["匹配系统"])


@router.post("/swipe", response_model=dict)
async def swipe_user(
    req: SwipeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """用户滑动（like / pass / super_like）"""
    import uuid
    from datetime import datetime, timezone

    if req.target_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能对自己滑动",
        )

    # 标准化 ID 顺序
    u1, u2 = sorted([current_user.id, req.target_user_id])
    is_user1 = current_user.id == u1
    decision = req.swipe_type in ("like", "super_like")

    # 查找或创建匹配记录
    match = await match_repo.find_or_create(db, u1, u2)

    # 更新决策
    if is_user1:
        match.user1_decision = decision
    else:
        match.user2_decision = decision

    match.swipe_type = req.swipe_type

    # 检测双向匹配
    if match.user1_decision is True and match.user2_decision is True:
        match.is_mutual = True
        match.matched_at = datetime.now(timezone.utc)

    await db.flush()

    result = {"match_id": match.id, "is_mutual": match.is_mutual}

    if match.is_mutual:
        result["message"] = "恭喜！你们互相喜欢，可以开始聊天了！"
        result["matched_user_id"] = req.target_user_id

    return result


@router.get("/mutual", response_model=list[MatchResponse])
async def get_mutual_matches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取互相关注的匹配列表"""
    matches = await match_repo.find_mutual_matches(db, current_user.id)
    return matches


@router.get("/swiped", response_model=list[str])
async def get_swiped_ids(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取已滑过的用户 ID 列表"""
    return await match_repo.get_swiped_user_ids(db, current_user.id)
