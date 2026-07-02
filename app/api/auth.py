"""
用户认证 API 路由 (P1 完整版)
- 发送短信/邮件验证码 (Console 模拟)
- 验证码注册（手机号 / 邮箱）
- 密码登录（带防刷保护）
- 验证码登录（手机号）
- Token 刷新（带版本校验）
- 注销（Token 版本号递增）
- 密码找回（验证码重置）
- 邮箱激活
- 获取当前用户信息
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import settings
from app.core.limiter import limiter
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


@router.post("/send-code", response_model=MessageResponse)
@limiter.limit("3/minute")
async def send_code(request: Request, req: SendCodeRequest):
    if req.channel not in _SUPPORTED_CHANNELS:
        raise HTTPException(status_code=422, detail="channel 仅支持 sms / email")
    if req.purpose not in _SUPPORTED_PURPOSES:
        raise HTTPException(status_code=422, detail="purpose 不合法")

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


@router.post("/register/code", response_model=TokenResponse, status_code=201)
@limiter.limit("3/minute")
async def register_with_code(request: Request, req: CodeRegisterRequest):
    target = req.phone or req.email
    channel = "sms" if req.phone else "email"

    if req.email:
        exist = await supabase.select("users", filters={"email": req.email})
        if exist:
            raise HTTPException(status_code=409, detail="该邮箱已被注册")
    if req.phone:
        exist = await supabase.select("users", filters={"phone": req.phone})
        if exist:
            raise HTTPException(status_code=409, detail="该手机号已被注册")

    ok = await verify_vcode(target, req.code, "register")
    if not ok:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

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


LOGIN_MAX_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login_with_password(request: Request, req: LoginRequest):
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

    locked_until = user.get("locked_until")
    if locked_until:
        try:
            lock_time = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
            if lock_time > datetime.now(timezone.utc):
                remaining = int((lock_time - datetime.now(timezone.utc)).total_seconds() / 60) + 1
                raise HTTPException(
                    status_code=429,
                    detail=f"账户已临时锁定，请{remaining}分钟后重试"
                )
        except ValueError:
            pass

    if not verify_password(req.password, user["hashed_password"]):
        attempts = user.get("login_attempts", 0) + 1
        update_data: dict = {"login_attempts": attempts}
        if attempts >= LOGIN_MAX_ATTEMPTS:
            locked_time = datetime.now(timezone.utc) + timedelta(minutes=LOCK_DURATION_MINUTES)
            update_data["locked_until"] = locked_time.isoformat()
        await supabase.update("users", update_data, {"id": user["id"]})
        raise HTTPException(status_code=401, detail="账号或密码错误")

    await supabase.update(
        "users",
        {
            "last_login_at": datetime.now(timezone.utc).isoformat(),
            "login_attempts": 0,
            "locked_until": None,
        },
        {"id": user["id"]},
    )

    ver = user.get("refresh_token_version", 1)
    tokens = create_tokens(user["id"], ver)
    return TokenResponse(**tokens)


@router.post("/login/code", response_model=TokenResponse)
async def login_with_code(req: CodeLoginRequest):
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


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest):
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="请使用 refresh_token")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user_id = payload.get("sub")
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
    try:
        payload = decode_token(req.refresh_token)
        user_id = payload.get("sub")
    except ValueError:
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


@router.post("/reset-password/request", response_model=MessageResponse)
async def request_password_reset(req: ResetPasswordRequest):
    is_email = "@" in req.target
    channel = "email" if is_email else "sms"
    purpose = "reset_password"

    users = await supabase.select(
        "users",
        filters={"email" if is_email else "phone": req.target},
    )
    if not users:
        return MessageResponse(message="如果该账号已注册，验证码已发送")

    try:
        await send_verification_code(req.target, channel, purpose)
    except Exception as e:
        raise HTTPException(status_code=429, detail=str(e))

    return MessageResponse(message="如果该账号已注册，验证码已发送")


@router.post("/reset-password/confirm", response_model=MessageResponse)
async def confirm_password_reset(req: ResetPasswordConfirm):
    is_email = "@" in req.target
    channel = "email" if is_email else "sms"

    users = await supabase.select(
        "users",
        filters={"email" if is_email else "phone": req.target},
    )
    if not users:
        raise HTTPException(status_code=404, detail="账号不存在")

    ok = await verify_vcode(req.target, req.code, "reset_password")
    if not ok:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

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


@router.post("/activate-email", response_model=MessageResponse)
async def activate_email(req: ActivateEmailRequest):
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


@router.get("/me")
async def get_me(authorization: str | None = Header(None)):
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
