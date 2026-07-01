"""
图片处理服务
- 图片压缩（目标 < 500KB）
- 图片缩放（最大边 800px）
- RGBA → RGB 转换
- Supabase Storage 上传/删除
"""
import io
import uuid
from PIL import Image

from app.core.config import settings
from app.core.supabase_client import supabase


ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_DIM = 800
AVATAR_MAX_BYTES = settings.AVATAR_MAX_SIZE_KB * 1024


def validate_image(content_type: str, size: int):
    """校验图片格式和大小"""
    if content_type not in ALLOWED_TYPES:
        raise ValueError("仅支持 JPG/PNG/WebP 格式")
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size > max_bytes:
        raise ValueError(f"文件大小不能超过 {settings.MAX_UPLOAD_SIZE_MB} MB")


def compress_image(image_bytes: bytes) -> bytes:
    """
    压缩图片到目标大小以内。
    - 缩放最大边至 800px
    - RGBA/P 转 RGB
    - JPEG 渐进降质压缩
    返回 JPEG 格式 bytes
    """
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # 智能缩放
    w, h = img.size
    if w > MAX_DIM or h > MAX_DIM:
        ratio = MAX_DIM / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    # 压缩输出
    output = io.BytesIO()
    quality = 85
    img.save(output, format="JPEG", quality=quality, optimize=True)
    while output.tell() > AVATAR_MAX_BYTES and quality > 10:
        output.seek(0)
        output.truncate(0)
        quality -= 10
        img.save(output, format="JPEG", quality=quality, optimize=True)

    return output.getvalue()


async def upload_to_storage(bucket: str, file_bytes: bytes, filename: str) -> str:
    """
    上传文件到 Supabase Storage，返回公开 URL。
    通过 Supabase REST API 上传。
    """
    import httpx

    supabase_url = settings.SUPABASE_URL
    service_key = settings.SUPABASE_SERVICE_KEY

    url = f"{supabase_url}/storage/v1/object/{bucket}/{filename}"
    headers = {
        "Authorization": f"Bearer {service_key}",
        "apikey": service_key,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            headers=headers,
            content=file_bytes,
            params={"upsert": "true"},
        )
        if resp.status_code not in (200, 201):
            raise Exception(f"存储上传失败: {resp.status_code} {resp.text[:300]}")

    return f"{supabase_url}/storage/v1/object/public/{bucket}/{filename}"


async def delete_from_storage(bucket: str, filename: str):
    """从 Supabase Storage 删除文件"""
    import httpx

    supabase_url = settings.SUPABASE_URL
    service_key = settings.SUPABASE_SERVICE_KEY

    url = f"{supabase_url}/storage/v1/object/{bucket}/{filename}"
    headers = {
        "Authorization": f"Bearer {service_key}",
        "apikey": service_key,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.delete(url, headers=headers)
        # 404 说明已删除，也算成功
        if resp.status_code not in (200, 204, 404):
            raise Exception(f"存储删除失败: {resp.status_code} {resp.text[:300]}")


def extract_filename_from_url(url: str) -> str | None:
    """从 Supabase Storage URL 中提取文件名"""
    if not url:
        return None
    # URL 格式: https://.../storage/v1/object/public/{bucket}/{filename}
    parts = url.rsplit("/", 1)
    return parts[-1] if len(parts) > 1 else None
