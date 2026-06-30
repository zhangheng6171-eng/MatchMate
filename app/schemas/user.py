"""用户基础信息 Pydantic 模型"""
from datetime import datetime
from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    id: str
    phone: str | None = None
    email: str | None = None
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserBrief(BaseModel):
    id: str
    nickname: str | None = None
    avatar_url: str | None = None
