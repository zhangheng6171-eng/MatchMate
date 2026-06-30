"""用户资料 Pydantic 模型"""
from datetime import date, datetime
from pydantic import BaseModel, Field


class ProfileBase(BaseModel):
    nickname: str | None = Field(None, max_length=50)
    bio: str | None = Field(None, max_length=500)
    gender: str | None = None
    birthday: date | None = None
    city: str | None = None
    interests: list[str] | None = None
    hobbies: list[str] | None = None
    looking_for: str | None = None
    preferred_age_min: int | None = Field(None, ge=18, le=100)
    preferred_age_max: int | None = Field(None, ge=18, le=100)
    preferred_distance_km: int | None = None


class ProfileUpdate(ProfileBase):
    """个人资料编辑请求"""
    pass


class ProfileResponse(ProfileBase):
    id: str
    user_id: str
    avatar_url: str | None = None
    age: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    personality_quiz: str | None = None
    is_profile_public: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfilePublic(ProfileBase):
    """公开资料（他人可见）"""
    avatar_url: str | None = None
    age: int | None = None
    city: str | None = None

    model_config = {"from_attributes": True}
