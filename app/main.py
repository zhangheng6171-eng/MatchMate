"""
MatchMate - FastAPI 后端主入口
相亲交友平台 API（基于 Supabase PostgreSQL + SQLAlchemy 2.0）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import settings
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

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION, "database": "supabase"}


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


@app.get("/api/deck/sample")
async def get_sample_deck():
    """返回示例推荐列表（Demo 用，后续接入数据库）"""
    return {
        "candidates": [
            {
                "id": "u1", "name": "Alice", "age": 26,
                "compatibility": 85, "distance_km": 3.2,
                "bio": "热爱旅行和摄影，周末喜欢探索城市角落",
                "interests": ["旅行", "摄影", "咖啡", "瑜伽"],
                "avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400"
            },
            {
                "id": "u2", "name": "Bob", "age": 28,
                "compatibility": 72, "distance_km": 5.1,
                "bio": "程序员一枚，平时喜欢打篮球和看电影",
                "interests": ["编程", "篮球", "电影", "音乐"],
                "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400"
            },
            {
                "id": "u3", "name": "Cathy", "age": 25,
                "compatibility": 91, "distance_km": 1.8,
                "bio": "爱猫人士，周末喜欢去书店和公园",
                "interests": ["阅读", "猫", "徒步", "烘焙"],
                "avatar": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400"
            },
        ]
    }


# ---- 静态文件（前端） ----
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")
