"""
应用核心配置
所有环境变量集中管理，通过 Pydantic Settings 校验
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ---- 应用 ----
    APP_NAME: str = "MatchMate"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "dev-secret-change-in-production"

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
    JWT_SECRET_KEY: str = "dev-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---- Supabase ----
    SUPABASE_URL: str = "https://ntaqnyegiiwtzdyqjiwy.supabase.co"
    SUPABASE_ANON_KEY: str = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50YXFueWVnaWl3dHpkeXFqaXd5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5MTY4NzUsImV4cCI6MjA4OTQ5Mjg3NX0."
        "4FEAb1Yd4xOwXz3LcfZ9iPG0ZZPbFd8dfry903c5lPc"
    )
    SUPABASE_SERVICE_KEY: str = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50YXFueWVnaWl3dHpkeXFqaXd5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzkxNjg3NSwiZXhwIjoyMDg5NDkyODc1fQ."
        "z8LPpoJoa9_DEJvBmNvSF0Q1I4FA3FNnFRU0PgKcF2A"
    )

    # ---- 文件上传 ----
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    AVATAR_MAX_SIZE_KB: int = 500

    # ---- CORS ----
    CORS_ORIGINS: list[str] = ["*"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
