"""
MatchMate - FastAPI 后端主入口
相亲交友平台 API（基于 Supabase PostgreSQL + SQLAlchemy 2.0）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import settings
from app.core.security import decode_token
from app.domain.services.haversine import haversine
from app.domain.services.compatibility import calculate_compatibility, get_shared_tags

logger = logging.getLogger(__name__)

# ---- API 路由 ----
from app.api.auth import router as auth_router
from app.api.profile import router as profile_router
from app.api.match import router as match_router
from app.api.messages import router as messages_router
from app.api.conversations import router as conversations_router


# ---- FastAPI 应用 ----
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "MatchMate 相亲App后端服务 —— "
        "用户注册/登录 · 资料管理 · 滑动匹配 · 即时聊天 · 音视频通话"
    ),
    version=settings.APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 数据库不可用时的异常处理 ----
@app.exception_handler(Exception)
async def catch_db_errors(request, exc):
    """捕获数据库连接等基础设施异常，返回友好错误"""
    error_msg = str(exc)
    if "connect" in error_msg.lower() or "not found" in error_msg.lower():
        return JSONResponse(
            status_code=503,
            content={
                "detail": "数据库服务暂不可用，请稍后重试",
                "error": error_msg[:200],
            },
        )
    raise exc


# ---- 注册路由 ----
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(messages_router)
app.include_router(conversations_router)
app.include_router(match_router)

# ---- 兼容性 & 距离计算（通用领域服务） ----

BUILD_TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "database": "supabase",
        "build_time": BUILD_TIMESTAMP,
    }


@app.get("/api/distance")
async def calc_distance(lat1: float, lon1: float, lat2: float, lon2: float):
    """计算两地之间的地表距离"""
    km = haversine(lat1, lon1, lat2, lon2)
    return {"distance_km": round(km, 2), "unit": "km"}


@app.post("/api/compatibility")
async def calc_compatibility(user1: dict, user2: dict):
    """计算两个用户的兼容性评分（0-100）"""
    score = calculate_compatibility(user1, user2)
    tags = get_shared_tags(user1, user2)
    return {
        "compatibility_score": score,
        "shared_interests": tags,
        "max_score": 100,
    }


@app.get("/api/deck/explore")
async def explore_deck(authorization: str | None = Header(None)):
    """推荐列表 — 基于真实 profiles 表查询，排除当前用户及已滑过的用户"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")

    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="登录凭证无效或已过期")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="请使用登录凭证")

    user_id = payload.get("sub")
    from app.core.supabase_client import supabase

    # 获取已滑过的用户ID
    or_filter = f"(user1_id.eq.{user_id},user2_id.eq.{user_id})"
    swiped_records = await supabase.select(
        "matches",
        columns="user1_id,user2_id",
        extra_params={"or": or_filter},
    )
    swiped_ids = set()
    for m in (swiped_records or []):
        swiped_ids.add(m["user2_id"] if m["user1_id"] == user_id else m["user1_id"])

    # 查询所有用户的 profile（排除自己和已滑过的）
    all_profiles = await supabase.select(
        "profiles",
        columns="user_id,nickname,age,bio,avatar_url,city,latitude,longitude,interests,gender",
        order="created_at.desc",
        limit=30,
    )

    candidates = []
    for p in (all_profiles or []):
        pid = p.get("user_id")
        if pid == user_id or pid in swiped_ids:
            continue
        if not p.get("nickname"):
            continue

        item = {
            "user_id": pid,
            "name": p.get("nickname", ""),
            "age": p.get("age"),
            "bio": p.get("bio", ""),
            "city": p.get("city", ""),
            "avatar": p.get("avatar_url", ""),
            "interests": p.get("interests") or [],
            "gender": p.get("gender", ""),
        }
        candidates.append(item)

    return {"candidates": candidates, "count": len(candidates)}


# ---- 静态文件（前端） ----
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")
