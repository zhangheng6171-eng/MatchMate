"""用户资料 Pydantic 模型（P2 扩展）"""
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator


# ---- 基础字段 ----
class ProfileBase(BaseModel):
    nickname: str | None = Field(None, max_length=50, description="昵称")
    bio: str | None = Field(None, max_length=500, description="个人简介")
    gender: str | None = Field(None, description="male / female / other")
    birthday: date | None = None
    city: str | None = Field(None, max_length=100)
    interests: list[str] | None = Field(None, description="兴趣爱好标签")
    hobbies: list[str] | None = Field(None, description="业余爱好")
    looking_for: str | None = Field(None, description="casual / serious / marriage / friendship")
    preferred_age_min: int | None = Field(None, ge=18, le=100)
    preferred_age_max: int | None = Field(None, ge=18, le=100)
    preferred_distance_km: int | None = Field(None, ge=1)


# ---- 资料编辑请求 ----
class ProfileUpdateRequest(ProfileBase):
    """编辑个人资料"""
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    is_profile_public: bool | None = True
    show_distance: bool | None = True

    @field_validator("preferred_age_max")
    @classmethod
    def check_age_range(cls, v: int | None, info) -> int | None:
        if v is not None and info.data.get("preferred_age_min") is not None:
            if v < info.data["preferred_age_min"]:
                raise ValueError("最大年龄不能小于最小年龄")
        return v


# ---- 偏好设置请求 ----
class PreferencesRequest(BaseModel):
    """更新择偶偏好"""
    looking_for: str | None = Field(None, description="casual / serious / marriage / friendship")
    preferred_age_min: int | None = Field(None, ge=18, le=100)
    preferred_age_max: int | None = Field(None, ge=18, le=100)
    preferred_distance_km: int | None = Field(None, ge=1)


# ---- 资料响应 ----
class ProfileResponse(ProfileBase):
    id: str
    user_id: str
    avatar_url: str | None = None
    photos: list[str] | None = Field(None, description="照片URL列表")
    age: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_profile_public: bool = True
    show_distance: bool = True
    profile_complete: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProfilePublicResponse(BaseModel):
    """公开资料（他人可见）"""
    id: str
    user_id: str
    nickname: str | None = None
    avatar_url: str | None = None
    photos: list[str] | None = Field(None, description="照片URL列表")
    age: int | None = None
    city: str | None = None
    bio: str | None = None
    interests: list[str] | None = None
    hobbies: list[str] | None = None
    looking_for: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    show_distance: bool = True


# ---- 照片响应 ----
class PhotoResponse(BaseModel):
    photo_id: str
    url: str


# ---- 通用响应 ----
class MessageResponse(BaseModel):
    message: str


# ---- 保留旧版兼容 ----
class ProfileUpdate(ProfileUpdateRequest):
    """个人资料编辑请求（旧版兼容）"""
    pass


class ProfilePublic(ProfileBase):
    """公开资料（旧版兼容）"""
    avatar_url: str | None = None
    age: int | None = None
    city: str | None = None
    photos: list[str] | None = None

    model_config = {"from_attributes": True}
