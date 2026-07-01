"""
用户认证 API 路由 (P1 完整版)
- 发送短信/邮件验证码 (Console 模拟)
- 验证码注册（手机号 / 邮箱）
- 密码注册（兼容旧版）
- 密码登录
- 验证码登录（手机号）
- Token 刷新（带版本校验）
- 注销（Token 版本号递增）
- 密码找回（验证码重置）
- 邮箱激活
- 获取当前用户信息
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, status

from app.core.security import (
    hash_password,
    verify_password,
    create_tokens,
    decode_token,
    validate_password_strength,
)
from app.core.supabase_client import supabase
from app.services.verification import (
    send_verification_code,
    verify_code as verify_vcode,
)
from app.schemas.auth import (
    SendCodeRequest,
    CodeRegisterRequest,
    PasswordRegisterRequest,
    LoginRequest,
    CodeLoginRequest,
    TokenResponse,
    RefreshRequest,
    ResetPasswordRequest,
    ResetPasswordConfirm,
    ActivateEmailRequest,
    MessageResponse,
)

router = APIRouter(prefix="/api/auth", tags=["用户认证"])

_SUPPORTED_CHANNELS = {"sms", "email"}
_SUPPORTED_PURPOSES = {"register", "login", "reset_password", "activate_email"}


# ================================================================
#  验证码
# ================================================================

@router.post("/send-code", response_model=MessageResponse)
async def send_code(req: SendCodeRequest):
    """发送短信/邮件验证码（开发期 Console 模拟）"""
    if req.channel not in _SUPPORTED_CHANNELS:
        raise HTTPException(status_code=422, detail="channel 仅支持 sms / email")
    if req.purpose not in _SUPPORTED_PURPOSES:
        raise HTTPException(status_code=422, detail="purpose 不合法")

    # 业务校验：注册/重置场景需确保目标可操作
    if req.purpose == "register":
        if req.channel == "email":
            exist = await supabase.select("users", filters={"email": req.target})
        else:
            exist = await supabase.select("users", filters={"phone": req.target})
        if exist:
            raise HTTPException(status_code=409, detail="该账号已被注册，请直接登录")

    if req.purpose in ("login", "reset_password", "activate_email"):
        if req.channel == "email":
            exist = await supabase.select("users", filters={"email": req.target})
        else:
            exist = await supabase.select("users", filters={"phone": req.target})
        if not exist:
            raise HTTPException(status_code=404, detail="该账号未注册")

    try:
        code = await send_verification_code(req.target, req.channel, req.purpose)
    except Exception as e:
        raise HTTPException(status_code=429, detail=str(e))

    return MessageResponse(message=f"验证码已发送到 {req.target}")


# ================================================================
#  注册
# ================================================================

@router.post("/register/code", response_model=TokenResponse, status_code=201)
async def register_with_code(req: CodeRegisterRequest):
    """验证码注册（手机号或邮箱）"""
    target = req.phone or req.email
    channel = "sms" if req.phone else "email"

    # 唯一性检查
    if req.email:
        exist = await supabase.select("users", filters={"email": req.email})
        if exist:
            raise HTTPException(status_code=409, detail="该邮箱已被注册")
    if req.phone:
        exist = await supabase.select("users", filters={"phone": req.phone})
        if exist:
            raise HTTPException(status_code=409, detail="该手机号已被注册")

    # 验证码校验
    ok = await verify_vcode(target, req.code, "register")
    if not ok:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    # 创建用户
    user_id = str(uuid.uuid4())
    await supabase.insert("users", {
        "id": user_id,
        "email": req.email,
        "phone": req.phone,
        "hashed_password": hash_password(req.password),
        "is_verified": True,
    })

    tokens = create_tokens(user_id)
    return TokenResponse(**tokens)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register_with_password(req: PasswordRegisterRequest):
    """密码注册（兼容模式，无需验证码）"""
    if req.email:
        exist = await supabase.select("users", filters={"email": req.email})
        if exist:
            raise HTTPException(status_code=409, detail="该邮箱已被注册")
    if req.phone:
        exist = await supabase.select("users", filters={"phone": req.phone})
        if exist:
            raise HTTPException(status_code=409, detail="该手机号已被注册")

    user_id = str(uuid.uuid4())
    await supabase.insert("users", {
        "id": user_id,
        "email": req.email,
        "phone": req.phone,
        "hashed_password": hash_password(req.password),
        "is_verified": False,
    })

    tokens = create_tokens(user_id)
    return TokenResponse(**tokens)


# ================================================================
#  登录
# ================================================================

@router.post("/login", response_model=TokenResponse)
async def login_with_password(req: LoginRequest):
    """密码登录（手机号/邮箱 + 密码）"""
    is_email = "@" in req.login
    users = await supabase.select(
        "users",
        filters={"email" if is_email else "phone": req.login},
    )
    if not users:
        raise HTTPException(status_code=401, detail="账号或密码错误")

    user = users[0] if isinstance(users, list) else users
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="账户已被禁用")

    if not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="账号或密码错误")

    await supabase.update(
        "users",
        {"last_login_at": datetime.now(timezone.utc).isoformat()},
        {"id": user["id"]},
    )

    ver = user.get("refresh_token_version", 1)
    tokens = create_tokens(user["id"], ver)
    return TokenResponse(**tokens)


@router.post("/login/code", response_model=TokenResponse)
async def login_with_code(req: CodeLoginRequest):
    """验证码登录（手机号 + 验证码）"""
    users = await supabase.select("users", filters={"phone": req.login})
    if not users:
        raise HTTPException(status_code=401, detail="该手机号未注册")

    user = users[0] if isinstance(users, list) else users
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="账户已被禁用")

    ok = await verify_vcode(req.login, req.code, "login")
    if not ok:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    await supabase.update(
        "users",
        {"last_login_at": datetime.now(timezone.utc).isoformat()},
        {"id": user["id"]},
    )

    ver = user.get("refresh_token_version", 1)
    tokens = create_tokens(user["id"], ver)
    return TokenResponse(**tokens)


# ================================================================
#  Token 刷新 & 注销
# ================================================================

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest):
    """刷新 Token（校验 refresh_token 版本号）"""
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="请使用 refresh_token")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user_id = payload.get("sub")
    # 校验 token 版本号（防止旧 refresh_token 被复用）
    token_version = payload.get("ver", 0)
    users = await supabase.select("users", filters={"id": user_id})
    if not users:
        raise HTTPException(status_code=401, detail="用户不存在")

    user = users[0] if isinstance(users, list) else users
    current_version = user.get("refresh_token_version", 1)
    if token_version < current_version:
        raise HTTPException(status_code=401, detail="Token 已失效，请重新登录")

    tokens = create_tokens(user_id, current_version)
    return TokenResponse(**tokens)


@router.post("/logout", response_model=MessageResponse)
async def logout(req: RefreshRequest):
    """注销（递增 refresh_token 版本号，使所有旧 token 失效）"""
    try:
        payload = decode_token(req.refresh_token)
        user_id = payload.get("sub")
    except ValueError:
        # Token 无效时也认为已注销
        return MessageResponse(message="已注销")

    users = await supabase.select("users", filters={"id": user_id})
    if users:
        user = users[0] if isinstance(users, list) else users
        new_version = user.get("refresh_token_version", 1) + 1
        await supabase.update(
            "users",
            {"refresh_token_version": new_version},
            {"id": user_id},
        )

    return MessageResponse(message="已注销")


# ================================================================
#  密码找回
# ================================================================

@router.post("/reset-password/request", response_model=MessageResponse)
async def request_password_reset(req: ResetPasswordRequest):
    """请求密码重置——发送验证码"""
    is_email = "@" in req.target
    channel = "email" if is_email else "sms"
    purpose = "reset_password"

    users = await supabase.select(
        "users",
        filters={"email" if is_email else "phone": req.target},
    )
    if not users:
        # 安全考虑：不暴露目标是否注册
        return MessageResponse(message="如果该账号已注册，验证码已发送")

    try:
        await send_verification_code(req.target, channel, purpose)
    except Exception as e:
        raise HTTPException(status_code=429, detail=str(e))

    return MessageResponse(message="如果该账号已注册，验证码已发送")


@router.post("/reset-password/confirm", response_model=MessageResponse)
async def confirm_password_reset(req: ResetPasswordConfirm):
    """确认密码重置——校验验证码并更新密码"""
    is_email = "@" in req.target
    channel = "email" if is_email else "sms"

    # 查找用户
    users = await supabase.select(
        "users",
        filters={"email" if is_email else "phone": req.target},
    )
    if not users:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 校验验证码
    ok = await verify_vcode(req.target, req.code, "reset_password")
    if not ok:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    # 更新密码
    user = users[0] if isinstance(users, list) else users
    new_hashed = hash_password(req.new_password)
    await supabase.update(
        "users",
        {
            "hashed_password": new_hashed,
            "refresh_token_version": user.get("refresh_token_version", 1) + 1,
        },
        {"id": user["id"]},
    )

    return MessageResponse(message="密码已重置，请使用新密码重新登录")


# ================================================================
#  邮箱激活
# ================================================================

@router.post("/activate-email", response_model=MessageResponse)
async def activate_email(req: ActivateEmailRequest):
    """使用验证码激活邮箱"""
    users = await supabase.select("users", filters={"email": req.email})
    if not users:
        raise HTTPException(status_code=404, detail="该邮箱未注册")

    user = users[0] if isinstance(users, list) else users
    if user.get("is_verified"):
        return MessageResponse(message="邮箱已激活，无需重复操作")

    ok = await verify_vcode(req.email, req.code, "activate_email")
    if not ok:
        raise HTTPException(status_code=400, detail="激活码错误或已过期")

    await supabase.update(
        "users",
        {"is_verified": True},
        {"id": user["id"]},
    )

    return MessageResponse(message="邮箱激活成功")


# ================================================================
#  当前用户
# ================================================================

@router.get("/me")
async def get_me(authorization: str | None = Header(None)):
    """获取当前登录用户信息"""
    if not authorization:
        raise HTTPException(status_code=401, detail="请提供 Authorization Header")

    token = authorization.replace("Bearer ", "")
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="请使用 access_token")
        user_id = payload.get("sub")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    users = await supabase.select("users", filters={"id": user_id})
    if not users:
        raise HTTPException(status_code=401, detail="用户不存在")

    user = users[0] if isinstance(users, list) else users
    return {
        "id": user["id"],
        "email": user.get("email"),
        "phone": user.get("phone"),
        "is_verified": user.get("is_verified"),
        "is_active": user.get("is_active"),
        "created_at": user.get("created_at"),
        "last_login_at": user.get("last_login_at"),
    }
