"""
验证码服务
- 短信验证码生成与校验（开发期 Console 模拟）
- 邮件验证码/激活链接生成与校验
- 验证码过期管理
"""
import random
import uuid
from datetime import datetime, timedelta, timezone

from app.core.supabase_client import supabase


# 验证码有效期（分钟）
CODE_EXPIRE_MINUTES = 5
# 同一目标 60 秒内不可重复发送
RESEND_COOLDOWN_SECONDS = 60


def generate_code(length: int = 6) -> str:
    """生成随机数字验证码"""
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def generate_activation_token() -> str:
    """生成邮箱激活 token"""
    return uuid.uuid4().hex


async def send_verification_code(target: str, channel: str, purpose: str) -> str:
    """
    发送验证码并存储到数据库。
    开发期：验证码通过 Console 打印，不上线前替换为真实短信/邮件服务。

    Args:
        target: 手机号 (如 +8613800138000) 或 邮箱
        channel: sms / email
        purpose: register / login / reset_password / activate_email

    Returns:
        生成的验证码（生产环境不返回）
    """
    # 检查冷却时间
    recent = await supabase.select(
        "verification_codes",
        filters={"target": target},
        order="created_at.desc",
        limit=1,
    )
    if recent:
        latest = recent[0] if isinstance(recent, list) else recent
        created = datetime.fromisoformat(latest["created_at"].replace("Z", "+00:00"))
        elapsed = (datetime.now(timezone.utc) - created).total_seconds()
        if elapsed < RESEND_COOLDOWN_SECONDS:
            remaining = int(RESEND_COOLDOWN_SECONDS - elapsed)
            raise Exception(f"验证码发送过于频繁，请 {remaining} 秒后重试")

    # 生成验证码
    code = generate_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=CODE_EXPIRE_MINUTES)

    # 存储到数据库
    await supabase.insert("verification_codes", {
        "id": str(uuid.uuid4()),
        "target": target,
        "code": code,
        "purpose": purpose,
        "channel": channel,
        "used": False,
        "expires_at": expires_at.isoformat(),
    })

    # 通过通知服务发送（根据 ENVIRONMENT 自动选择 Console / 腾讯云SMS / 阿里云SMS）
    from app.services.notification_service import notification_service
    await notification_service.send_verification_code(
        target=target, code=code, channel=channel, purpose=purpose
    )

    return code


async def verify_code(target: str, code: str, purpose: str) -> bool:
    """
    校验验证码。成功后将标记为已使用。

    Args:
        target: 手机号 / 邮箱
        code: 用户输入的验证码
        purpose: register / login / reset_password / activate_email

    Returns:
        是否校验成功
    """
    records = await supabase.select(
        "verification_codes",
        filters={"target": target, "purpose": purpose},
        order="created_at.desc",
        limit=3,
    )

    if not records:
        return False

    for record in records:
        # 已使用的跳过
        if record.get("used"):
            continue
        # 过期检查
        expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
        if expires < datetime.now(timezone.utc):
            continue
        # 验证码匹配
        if record["code"] == code:
            # 标记已使用
            await supabase.update(
                "verification_codes",
                {"used": True},
                {"id": record["id"]},
            )
            return True

    return False


async def cleanup_expired_codes():
    """清理过期验证码（定期调用）"""
    now = datetime.now(timezone.utc).isoformat()
    await supabase.delete("verification_codes", {"expires_at": f"lt.{now}"})
