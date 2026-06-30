"""
JWT 身份认证 & 密码安全模块
- access_token: 短期令牌 (默认 30 分钟)
- refresh_token: 长期令牌 (默认 7 天)
- 密码使用 bcrypt 哈希
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# ---- 密码哈希 (直接使用 bcrypt) ----


def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希"""
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与哈希值是否匹配"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    校验密码强度。
    要求：至少 8 位，包含大写、小写、数字、特殊字符中的至少 3 类。
    """
    if len(password) < 8:
        return False, "密码长度不能少于 8 位"
    
    checks = 0
    import re
    if re.search(r"[A-Z]", password):
        checks += 1
    if re.search(r"[a-z]", password):
        checks += 1
    if re.search(r"[0-9]", password):
        checks += 1
    if re.search(r"[^A-Za-z0-9]", password):
        checks += 1

    if checks < 3:
        return False, "密码需包含大写字母、小写字母、数字、特殊字符中的至少 3 类"
    
    return True, "密码强度合格"


# ---- JWT ----

def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """签发 access_token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """签发 refresh_token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """解码并验证 JWT token"""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise ValueError(f"Token 验证失败: {e}")


def create_tokens(user_id: str) -> dict[str, str]:
    """一次性签发 access + refresh 双令牌"""
    payload = {"sub": user_id}
    return {
        "access_token": create_access_token(payload),
        "refresh_token": create_refresh_token(payload),
        "token_type": "bearer",
    }
