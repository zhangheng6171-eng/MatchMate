"""匹配相关 Pydantic 模型"""
from datetime import datetime
from pydantic import BaseModel


class SwipeRequest(BaseModel):
    target_user_id: str
    swipe_type: str = "like"  # like / pass / super_like


class MatchResponse(BaseModel):
    id: str
    user1_id: str
    user2_id: str
    user1_decision: bool | None
    user2_decision: bool | None
    is_mutual: bool
    matched_at: datetime | None
    swipe_type: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MutualMatchResponse(BaseModel):
    match_id: str
    matched_user_id: str
    matched_user_nickname: str | None
    matched_at: datetime | None
    message: str = "恭喜！你们互相喜欢，可以开始聊天了！"
