"""
应用核心配置
所有环境变量集中管理，通过 Pydantic Settings 校验
敏感凭证必须通过环境变量提供，不允许硬编码默认值
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ---- 应用 ----
    APP_NAME: str = "MatchMate"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ---- 数据库 ----
    # Supabase PostgreSQL (通过 Session Pooler 或 Direct)
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres.ntaqnyegiiwtzdyqjiwy:"
        "replace_with_db_password"
        "@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ---- JWT ----
    # P0.6: 必须从环境变量读取，禁止默认值
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---- Supabase ----
    SUPABASE_URL: str = "https://ntaqnyegiiwtzdyqjiwy.supabase.co"
    # ANON_KEY 是公开密钥，可安全硬编码
    SUPABASE_ANON_KEY: str = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50YXFueWVnaWl3dHpkeXFqaXd5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5MTY4NzUsImV4cCI6MjA4OTQ5Mjg3NX0."
        "4FEAb1Yd4xOwXz3LcfZ9iPG0ZZPbFd8dfry903c5lPc"
    )
    # P0.6: SERVICE_KEY 必须从环境变量读取，禁止默认值
    SUPABASE_SERVICE_KEY: str = ""

    # ---- 文件上传 ----
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    AVATAR_MAX_SIZE_KB: int = 500

    # ---- 分页 ----
    PAGE_SIZE_DEFAULT: int = 20
    MAX_PAGE_SIZE: int = 100

    # ---- 运行环境 ----
    ENVIRONMENT: str = "development"

    # ---- CORS ----
    CORS_ORIGINS: list[str] = ["*"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    _validate_critical_secrets(s)
    return s


def _validate_critical_secrets(s: Settings):
    """启动时校验关键凭证已通过环境变量配置"""
    missing = []

    if not s.JWT_SECRET_KEY:
        missing.append("JWT_SECRET_KEY")
    if not s.SUPABASE_SERVICE_KEY:
        missing.append("SUPABASE_SERVICE_KEY")

    if missing:
        key_list = ", ".join(missing)
        raise RuntimeError(
            f"[Security] 关键凭证未配置: {key_list}\n"
            f"请在环境变量或 .env 文件中设置。\n"
            f"切勿将凭证硬编码到源代码中。\n"
            f"参考文档: SECRET_ROTATION_GUIDE.md"
        )


settings = get_settings()
