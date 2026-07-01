"""
用户资料 API 路由 (P2 完整版 — Supabase REST API)
- 查看/编辑个人资料
- 头像上传（Supabase Storage）
- 照片管理
- 择偶偏好设置
- 公开资料查看（权限校验）
- 操作日志留存
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from app.core.deps import get_current_user_supabase
from app.core.supabase_client import supabase
from app.schemas.profile import (
    ProfileUpdateRequest,
    ProfileResponse,
    ProfilePublicResponse,
    PreferencesRequest,
    PhotoResponse,
    MessageResponse,
)
from app.services.image_service import (
    validate_image,
    compress_image,
    upload_to_storage,
    delete_from_storage,
    extract_filename_from_url,
)

router = APIRouter(prefix="/api/profile", tags=["用户资料"])

BUCKET_AVATARS = "avatars"
BUCKET_PHOTOS = "photos"
MAX_PHOTOS = 6


def _profile_to_response(profile: dict) -> dict:
    """将数据库 profile 记录转为响应格式"""
    photos = profile.get("photos")
    if isinstance(photos, str):
        import json
        try:
            photos = json.loads(photos)
        except (json.JSONDecodeError, TypeError):
            photos = []
    return {
        "id": profile["id"],
        "user_id": profile["user_id"],
        "nickname": profile.get("nickname"),
        "avatar_url": profile.get("avatar_url"),
        "photos": photos or [],
        "bio": profile.get("bio"),
        "gender": profile.get("gender"),
        "birthday": profile.get("birthday"),
        "age": profile.get("age"),
        "latitude": profile.get("latitude"),
        "longitude": profile.get("longitude"),
        "city": profile.get("city"),
        "interests": profile.get("interests"),
        "hobbies": profile.get("hobbies"),
        "looking_for": profile.get("looking_for"),
        "preferred_age_min": profile.get("preferred_age_min"),
        "preferred_age_max": profile.get("preferred_age_max"),
        "preferred_distance_km": profile.get("preferred_distance_km"),
        "is_profile_public": profile.get("is_profile_public", True),
        "show_distance": profile.get("show_distance", True),
        "profile_complete": profile.get("profile_complete", False),
        "created_at": profile.get("created_at"),
        "updated_at": profile.get("updated_at"),
    }


async def _get_or_create_profile(user_id: str) -> dict:
    """获取用户资料，不存在则自动创建"""
    profiles = await supabase.select("profiles", filters={"user_id": user_id})
    if profiles:
        return profiles[0] if isinstance(profiles, list) else profiles

    # 自动创建空资料
    profile_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await supabase.insert("profiles", {
        "id": profile_id,
        "user_id": user_id,
        "created_at": now,
        "updated_at": now,
    })
    return {
        "id": profile_id,
        "user_id": user_id,
        "is_profile_public": True,
        "show_distance": True,
        "profile_complete": False,
    }


async def _log_operation(user_id: str, action: str, details: str = ""):
    """记录操作日志"""
    try:
        await supabase.insert("profile_operation_logs", {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "action": action,
            "details": details,
        })
    except Exception:
        pass  # 日志失败不影响主流程


# ================================================================
#  GET /me — 获取本人资料
# ================================================================

@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(current_user: dict = Depends(get_current_user_supabase)):
    """获取当前用户完整资料，不存在则自动创建"""
    profile = await _get_or_create_profile(current_user["id"])
    return _profile_to_response(profile)


# ================================================================
#  PUT /me — 编辑个人资料
# ================================================================

@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    req: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user_supabase),
):
    """编辑个人资料（仅本人可操作）"""
    profile = await _get_or_create_profile(current_user["id"])

    update_data = req.model_dump(exclude_unset=True, mode="json")
    if not update_data:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")

    # 计算年龄
    if "birthday" in update_data and update_data["birthday"]:
        from datetime import date
        bd_str = update_data["birthday"]
        bd = date.fromisoformat(bd_str)
        today = date.today()
        age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
        update_data["age"] = age

    # 判断资料完整度
    nickname = update_data.get("nickname", profile.get("nickname"))
    avatar = profile.get("avatar_url")
    gender = update_data.get("gender", profile.get("gender"))
    profile_complete = bool(nickname and avatar and gender)
    update_data["profile_complete"] = profile_complete
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    await supabase.update("profiles", update_data, {"user_id": current_user["id"]})
    await _log_operation(current_user["id"], "update_profile",
                         f"更新了 {', '.join(update_data.keys())}")

    # 重新获取最新数据
    return await get_my_profile(current_user)


# ================================================================
#  GET /{user_id} — 查看他人公开资料
# ================================================================

@router.get("/{user_id}", response_model=ProfilePublicResponse)
async def get_public_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user_supabase),
):
    """查看其他用户的公开资料"""
    profiles = await supabase.select("profiles", filters={"user_id": user_id})
    if not profiles:
        raise HTTPException(status_code=404, detail="用户不存在")

    profile = profiles[0] if isinstance(profiles, list) else profiles

    # 本人可以看完整资料
    if profile["user_id"] == current_user["id"]:
        return _profile_to_response(profile)

    # 他人仅看公开字段
    if not profile.get("is_profile_public", True):
        raise HTTPException(status_code=403, detail="该用户资料不公开")

    photos = profile.get("photos")
    if isinstance(photos, str):
        import json
        try:
            photos = json.loads(photos)
        except (json.JSONDecodeError, TypeError):
            photos = []

    return {
        "id": profile["id"],
        "user_id": profile["user_id"],
        "nickname": profile.get("nickname"),
        "avatar_url": profile.get("avatar_url"),
        "photos": photos or [],
        "age": profile.get("age"),
        "city": profile.get("city"),
        "bio": profile.get("bio"),
        "interests": profile.get("interests"),
        "hobbies": profile.get("hobbies"),
        "looking_for": profile.get("looking_for"),
        "latitude": profile.get("latitude"),
        "longitude": profile.get("longitude"),
        "show_distance": profile.get("show_distance", True),
    }


# ================================================================
#  POST /me/avatar — 上传头像
# ================================================================

@router.post("/me/avatar", response_model=ProfileResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_supabase),
):
    """上传头像（自动压缩至 500KB 以内，存储到 Supabase Storage）"""
    contents = await file.read()
    validate_image(file.content_type or "image/jpeg", len(contents))

    # 压缩图片
    compressed = compress_image(contents)

    # 生成文件名
    filename = f"{current_user['id']}/{uuid.uuid4().hex}.jpg"

    # 上传到 Supabase Storage
    avatar_url = await upload_to_storage(BUCKET_AVATARS, compressed, filename)

    # 更新数据库中的头像 URL
    await _get_or_create_profile(current_user["id"])
    await supabase.update(
        "profiles",
        {"avatar_url": avatar_url, "updated_at": datetime.now(timezone.utc).isoformat()},
        {"user_id": current_user["id"]},
    )
    await _log_operation(current_user["id"], "upload_avatar")

    return await get_my_profile(current_user)


# ================================================================
#  DELETE /me/avatar — 删除头像
# ================================================================

@router.delete("/me/avatar", response_model=MessageResponse)
async def delete_avatar(current_user: dict = Depends(get_current_user_supabase)):
    """删除头像"""
    profiles = await supabase.select("profiles", filters={"user_id": current_user["id"]})
    if profiles:
        profile = profiles[0] if isinstance(profiles, list) else profiles
        old_url = profile.get("avatar_url")
        if old_url:
            fname = extract_filename_from_url(old_url)
            if fname:
                await delete_from_storage(BUCKET_AVATARS, fname)
        await supabase.update(
            "profiles",
            {"avatar_url": None, "updated_at": datetime.now(timezone.utc).isoformat()},
            {"user_id": current_user["id"]},
        )
        await _log_operation(current_user["id"], "delete_avatar")

    return MessageResponse(message="头像已删除")


# ================================================================
#  POST /me/photos — 上传照片
# ================================================================

@router.post("/me/photos", response_model=PhotoResponse)
async def upload_photo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_supabase),
):
    """上传照片（最多 6 张，存储到 Supabase Storage）"""
    contents = await file.read()
    validate_image(file.content_type or "image/jpeg", len(contents))

    # 查当前照片数量
    profile = await _get_or_create_profile(current_user["id"])
    photos = profile.get("photos")
    if isinstance(photos, str):
        import json
        try:
            photos = json.loads(photos)
        except (json.JSONDecodeError, TypeError):
            photos = []
    photos = photos or []
    if len(photos) >= MAX_PHOTOS:
        raise HTTPException(status_code=400, detail=f"最多上传 {MAX_PHOTOS} 张照片")

    # 压缩图片
    compressed = compress_image(contents)

    # 上传到 Supabase Storage
    filename = f"{current_user['id']}/{uuid.uuid4().hex}.jpg"
    photo_url = await upload_to_storage(BUCKET_PHOTOS, compressed, filename)

    # 更新数据库
    photos.append(photo_url)
    import json
    await supabase.update(
        "profiles",
        {"photos": json.dumps(photos), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"user_id": current_user["id"]},
    )
    await _log_operation(current_user["id"], "upload_photo")

    return PhotoResponse(photo_id=filename.split("/")[-1], url=photo_url)


# ================================================================
#  DELETE /me/photos/{photo_id} — 删除照片
# ================================================================

@router.delete("/me/photos/{photo_id}", response_model=MessageResponse)
async def delete_photo(
    photo_id: str,
    current_user: dict = Depends(get_current_user_supabase),
):
    """删除指定照片"""
    profile = await _get_or_create_profile(current_user["id"])
    photos = profile.get("photos")
    if isinstance(photos, str):
        import json
        try:
            photos = json.loads(photos)
        except (json.JSONDecodeError, TypeError):
            photos = []
    photos = photos or []

    # 查找并删除匹配的 URL
    target_url = None
    new_photos = []
    for url in photos:
        if photo_id in url:
            target_url = url
        else:
            new_photos.append(url)

    if target_url:
        fname = extract_filename_from_url(target_url)
        if fname:
            await delete_from_storage(BUCKET_PHOTOS, fname)

    import json
    await supabase.update(
        "profiles",
        {"photos": json.dumps(new_photos), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"user_id": current_user["id"]},
    )
    await _log_operation(current_user["id"], "delete_photo")

    return MessageResponse(message="照片已删除")


# ================================================================
#  PUT /me/preferences — 更新择偶偏好
# ================================================================

@router.put("/me/preferences", response_model=ProfileResponse)
async def update_preferences(
    req: PreferencesRequest,
    current_user: dict = Depends(get_current_user_supabase),
):
    """更新择偶偏好设置"""
    profile = await _get_or_create_profile(current_user["id"])

    update_data = req.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    await supabase.update("profiles", update_data, {"user_id": current_user["id"]})
    await _log_operation(current_user["id"], "update_preferences")

    return await get_my_profile(current_user)
