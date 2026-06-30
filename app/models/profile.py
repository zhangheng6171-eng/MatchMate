"""
Profile 用户资料模型
存储用户个人展示信息：昵称、头像、个人简介、兴趣标签、择偶条件等
"""
from datetime import datetime, timezone

from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, func, ARRAY, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from app.core.database import Base
import enum


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class LookingFor(str, enum.Enum):
    casual = "casual"          # 随缘交友
    serious = "serious"        # 认真恋爱
    marriage = "marriage"      # 以结婚为目的
    friendship = "friendship"  # 先交朋友


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # ---- 基础信息 ----
    nickname: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="昵称"
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="头像 URL"
    )
    bio: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="个人简介"
    )
    gender: Mapped[Gender | None] = mapped_column(
        SAEnum(Gender, name="gender_enum", create_type=False),
        nullable=True,
    )
    birthday: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="生日"
    )
    age: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="年龄（计算字段）"
    )

    # ---- 地理位置 ----
    latitude: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="纬度"
    )
    longitude: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="经度"
    )
    city: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="城市"
    )

    # ---- 兴趣与标签 ----
    interests: Mapped[list | None] = mapped_column(
        ARRAY(String), nullable=True, comment="兴趣爱好标签"
    )
    hobbies: Mapped[list | None] = mapped_column(
        ARRAY(String), nullable=True, comment="业余爱好"
    )

    # ---- 择偶条件 ----
    looking_for: Mapped[LookingFor | None] = mapped_column(
        SAEnum(LookingFor, name="looking_for_enum", create_type=False),
        nullable=True,
        comment="交友目的"
    )
    preferred_age_min: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=18
    )
    preferred_age_max: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=60
    )
    preferred_distance_km: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=30
    )

    # ---- 性格测评 ----
    personality_quiz: Mapped[dict | None] = mapped_column(
        String, nullable=True, comment="性格测评结果 (JSON string)"
    )

    # ---- 隐私设置 ----
    is_profile_public: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="资料是否公开"
    )
    show_distance: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否展示距离"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # 关联
    user: Mapped["User"] = relationship(back_populates="profile")

    def __repr__(self) -> str:
        return f"<Profile(nickname={self.nickname})>"
