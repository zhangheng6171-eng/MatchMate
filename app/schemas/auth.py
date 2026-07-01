"""认证相关 Pydantic 模型（P1 扩展）"""
from pydantic import BaseModel, Field, field_validator, model_validator
from app.core.security import validate_password_strength


# ---- 发送验证码 ----
class SendCodeRequest(BaseModel):
    target: str = Field(..., description="手机号 或 邮箱")
    channel: str = Field(..., description="sms / email")
    purpose: str = Field(..., description="register / login / reset_password")


# ---- 验证码注册 ----
class CodeRegisterRequest(BaseModel):
    phone: str | None = None
    email: str | None = None
    code: str = Field(..., min_length=4, max_length=6, description="短信/邮件验证码")
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
    def check_phone_format(cls, v: str | None) -> str | None:
        if v and not v.startswith("+"):
            raise ValueError("手机号需包含国际区号，如 +8613800138000")
        return v

    @model_validator(mode="after")
    def check_at_least_one_contact(self):
        if not self.phone and not self.email:
            raise ValueError("请提供手机号或邮箱")
        return self


# ---- 密码注册（兼容旧版） ----
class PasswordRegisterRequest(BaseModel):
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

    @model_validator(mode="after")
    def check_at_least_one_contact(self):
        if not self.phone and not self.email:
            raise ValueError("请提供手机号或邮箱")
        return self


# ---- 登录 ----
class LoginRequest(BaseModel):
    login: str = Field(..., description="手机号 或 邮箱")
    password: str


class CodeLoginRequest(BaseModel):
    login: str = Field(..., description="手机号")
    code: str = Field(..., min_length=4, max_length=6)


# ---- Token 响应 ----
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ---- 密码重置 ----
class ResetPasswordRequest(BaseModel):
    target: str = Field(..., description="手机号 或 邮箱")


class ResetPasswordConfirm(BaseModel):
    target: str
    code: str = Field(..., min_length=4, max_length=6)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        ok, msg = validate_password_strength(v)
        if not ok:
            raise ValueError(msg)
        return v


# ---- 邮箱激活 ----
class ActivateEmailRequest(BaseModel):
    email: str
    code: str = Field(..., min_length=4, max_length=6)


# ---- 通用响应 ----
class MessageResponse(BaseModel):
    message: str
