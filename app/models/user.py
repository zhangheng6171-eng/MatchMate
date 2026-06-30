"""
User 基础用户模型
存储认证信息：手机号、邮箱、密码哈希、账户状态
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), unique=True, nullable=True, index=True,
        comment="手机号（国际格式 +86xxx）"
    )
    email: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True,
        comment="邮箱地址"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(128), comment="bcrypt 哈希后的密码"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="账户是否启用"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否已验证（手机/邮箱）"
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="管理员标记"
    )

    # 认证相关
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refresh_token_version: Mapped[int] = mapped_column(
        default=1, comment="refresh_token 版本号，用于强制失效"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # 关联
    profile: Mapped["Profile"] = relationship(
        back_populates="user", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
