"""认证相关 Pydantic 模型"""
from pydantic import BaseModel, Field, field_validator
from app.core.security import validate_password_strength


# ---- 注册 ----
class RegisterRequest(BaseModel):
    phone: str | None = None
    email: str | None = None
    password: str = Field(..., min_length=8)
    nickname: str | None = Field(None, max_length=50)

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        ok, msg = validate_password_strength(v)
        if not ok:
            raise ValueError(msg)
        return v

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str | None) -> str | None:
        if v and not v.startswith("+"):
            raise ValueError("手机号需包含国际区号，如 +8613800138000")
        return v


# ---- 登录 ----
class LoginRequest(BaseModel):
    login: str = Field(..., description="手机号 或 邮箱")
    password: str


# ---- Token 响应 ----
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ---- 密码重置 ----
class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        ok, msg = validate_password_strength(v)
        if not ok:
            raise ValueError(msg)
        return v
