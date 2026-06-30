"""
用户资料 API 路由
- 查看/编辑个人资料
- 头像上传
- 公开资料查看
"""
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image
import io

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.repositories.profile import profile_repo
from app.schemas.profile import ProfileUpdate, ProfileResponse, ProfilePublic

router = APIRouter(prefix="/api/profile", tags=["用户资料"])


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户资料"""
    profile = await profile_repo.get_by_user_id(db, current_user.id)
    if profile is None:
        # 自动创建空资料
        import uuid as _uuid
        profile = await profile_repo.create(
            db,
            id=str(_uuid.uuid4()),
            user_id=current_user.id,
        )
    return profile


@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    req: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """编辑个人资料"""
    profile = await profile_repo.get_by_user_id(db, current_user.id)
    if profile is None:
        import uuid as _uuid
        profile = await profile_repo.create(
            db,
            id=str(_uuid.uuid4()),
            user_id=current_user.id,
        )

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    await db.flush()
    return profile


@router.post("/avatar", response_model=ProfileResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传头像（自动压缩至 500KB 以内）"""
    # 格式校验
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 JPG/PNG/WebP 格式",
        )

    # 读取文件
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小不能超过 {settings.MAX_UPLOAD_SIZE_MB} MB",
        )

    # 压缩图片
    img = Image.open(io.BytesIO(contents))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # 智能缩放：最大边 800px
    max_dim = 800
    w, h = img.size
    if w > max_dim or h > max_dim:
        ratio = max_dim / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    # 压缩输出
    output = io.BytesIO()
    quality = 85
    img.save(output, format="JPEG", quality=quality, optimize=True)
    while output.tell() > settings.AVATAR_MAX_SIZE_KB * 1024 and quality > 10:
        output.seek(0)
        output.truncate(0)
        quality -= 10
        img.save(output, format="JPEG", quality=quality, optimize=True)

    # 保存文件
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(output.getvalue())

    # 更新资料
    profile = await profile_repo.get_by_user_id(db, current_user.id)
    if profile is None:
        import uuid as _uuid
        profile = await profile_repo.create(
            db,
            id=str(_uuid.uuid4()),
            user_id=current_user.id,
        )

    avatar_url = f"/static/avatars/{filename}"
    profile.avatar_url = avatar_url
    await db.flush()

    return profile


@router.get("/{user_id}/public", response_model=ProfilePublic)
async def get_public_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查看其他用户的公开资料"""
    profile = await profile_repo.get_by_user_id(db, user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    if not profile.is_profile_public and profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="该用户资料不公开",
        )
    return profile
