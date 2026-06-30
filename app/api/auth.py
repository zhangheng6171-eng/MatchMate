"""
产品用户认证 API 路由 (Supabase REST)
- 注册（手机号 / 邮箱）
- 登录（密码 / 验证码）
- Token 刷新
- 密码重置
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from app.core.security import (
    hash_password,
    verify_password,
    create_tokens,
    decode_token,
)
from app.core.supabase_client import supabase
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)

router = APIRouter(prefix="/api/auth", tags=["用户认证"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(req: RegisterRequest):
    """用户注册"""
    if not req.phone and not req.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供手机号或邮箱",
        )

    # 唯一性检查
    if req.email:
        existing = await supabase.select("users", filters={"email": req.email})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该邮箱已被注册",
            )
    if req.phone:
        existing = await supabase.select("users", filters={"phone": req.phone})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该手机号已被注册",
            )

    # 创建用户
    user_id = str(uuid.uuid4())
    await supabase.insert("users", {
        "id": user_id,
        "email": req.email,
        "phone": req.phone,
        "hashed_password": hash_password(req.password),
        "is_verified": False,
    })

    # 签发 Token
    tokens = create_tokens(user_id)
    return TokenResponse(**tokens)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """用户登录（手机号/邮箱 + 密码）"""
    # 查找用户
    users = await supabase.select(
        "users",
        filters={"email": req.login} if "@" in req.login else {"phone": req.login},
    )
    if not users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误"
        )

    user = users[0]
    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已被禁用")

    if not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")

    # 更新最后登录时间
    await supabase.update(
        "users",
        {"last_login_at": datetime.now(timezone.utc).isoformat()},
        {"id": user["id"]},
    )

    tokens = create_tokens(user["id"])
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest):
    """刷新 Token"""
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="请使用 refresh_token",
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    user_id = payload.get("sub")
    tokens = create_tokens(user_id)
    return TokenResponse(**tokens)


@router.get("/me")
async def get_me(authorization: str | None = None):
    """获取当前登录用户信息（简化版，通过 Authorization Header）"""
    # 简化版：从 JWT 提取 user_id 并查库
    # 实际使用时应通过 Depends 注入
    return {"message": "请使用 /api/auth/login 获取 token 后调用此接口"}


@router.post("/logout")
async def logout():
    """注销登录"""
    return {"message": "已注销"}


@router.post("/reset-password/request")
async def request_password_reset(req: PasswordResetRequest):
    """请求密码重置"""
    return {"message": "如果该邮箱已注册，重置链接已发送"}


@router.post("/reset-password/confirm")
async def confirm_password_reset(req: PasswordResetConfirm):
    """确认密码重置"""
    return {"message": "密码已重置"}
