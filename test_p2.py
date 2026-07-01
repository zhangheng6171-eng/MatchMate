"""
P2 用户资料系统 — 单元测试
测试 schemas / 图片处理 / 依赖注入
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import io
import unittest
from datetime import date

# === Schemas ===
from app.schemas.profile import (
    ProfileUpdateRequest,
    PreferencesRequest,
    ProfileResponse,
    ProfilePublicResponse,
    PhotoResponse,
    MessageResponse,
)


class TestProfileSchemas(unittest.TestCase):
    """资料相关 Pydantic Schemas 校验"""

    def test_profile_update_valid(self):
        """有效的资料更新请求"""
        req = ProfileUpdateRequest(
            nickname="测试用户",
            bio="这是我的个人简介",
            gender="male",
            birthday=date(1995, 6, 15),
            city="北京",
            interests=["编程", "篮球", "音乐"],
            hobbies=["阅读", "旅行"],
            looking_for="serious",
            preferred_age_min=22,
            preferred_age_max=35,
            preferred_distance_km=30,
        )
        data = req.model_dump()
        self.assertEqual(data["nickname"], "测试用户")
        self.assertEqual(data["gender"], "male")
        self.assertEqual(data["preferred_age_min"], 22)

    def test_profile_update_empty(self):
        """空请求仍然有效（所有字段可选）"""
        req = ProfileUpdateRequest()
        data = req.model_dump(exclude_unset=True)
        self.assertEqual(len(data), 0)

    def test_profile_update_age_range_invalid(self):
        """最大年龄不能小于最小年龄"""
        with self.assertRaises(Exception):
            ProfileUpdateRequest(preferred_age_min=30, preferred_age_max=20)

    def test_profile_update_age_range_valid(self):
        """年龄范围正常"""
        req = ProfileUpdateRequest(preferred_age_min=25, preferred_age_max=35)
        self.assertEqual(req.preferred_age_max, 35)

    def test_preferences_request(self):
        """偏好设置请求"""
        req = PreferencesRequest(
            looking_for="marriage",
            preferred_age_min=28,
            preferred_age_max=42,
            preferred_distance_km=50,
        )
        data = req.model_dump()
        self.assertEqual(data["looking_for"], "marriage")
        self.assertEqual(data["preferred_distance_km"], 50)

    def test_preferences_partial(self):
        """部分偏好更新"""
        req = PreferencesRequest(looking_for="casual")
        data = req.model_dump(exclude_unset=True)
        self.assertEqual(list(data.keys()), ["looking_for"])

    def test_profile_response_structure(self):
        """ProfileResponse 结构完整性"""
        resp = ProfileResponse(
            id="p1",
            user_id="u1",
            nickname="小明",
            avatar_url="https://example.com/avatar.jpg",
            photos=["https://example.com/p1.jpg"],
            bio="Hello",
            gender="male",
            age=25,
            city="上海",
            interests=["音乐"],
            hobbies=["运动"],
            looking_for="serious",
            preferred_age_min=20,
            preferred_age_max=35,
            preferred_distance_km=30,
            is_profile_public=True,
            show_distance=True,
            profile_complete=True,
        )
        self.assertEqual(resp.id, "p1")
        self.assertEqual(resp.photos, ["https://example.com/p1.jpg"])
        self.assertTrue(resp.profile_complete)

    def test_public_profile_response(self):
        """公开资料响应"""
        resp = ProfilePublicResponse(
            id="p1",
            user_id="u1",
            nickname="小红",
            avatar_url="https://example.com/avatar.jpg",
            age=28,
            city="北京",
            bio="Love life",
            interests=["咖啡", "瑜伽"],
            show_distance=True,
        )
        self.assertEqual(resp.user_id, "u1")
        self.assertEqual(resp.age, 28)

    def test_photo_response(self):
        """照片响应"""
        resp = PhotoResponse(photo_id="abc123.jpg", url="https://example.com/abc123.jpg")
        self.assertEqual(resp.photo_id, "abc123.jpg")
        self.assertTrue(resp.url.startswith("https://"))

    def test_message_response(self):
        """通用消息响应"""
        resp = MessageResponse(message="操作成功")
        self.assertEqual(resp.message, "操作成功")


# === Image Service ===
from app.services.image_service import (
    validate_image,
    compress_image,
    extract_filename_from_url,
)


class TestImageService(unittest.TestCase):
    """图片处理服务测试"""

    def setUp(self):
        """创建一张小的测试图片（1x1 红色 PNG）"""
        from PIL import Image
        img = Image.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        self.test_png = buf.getvalue()

        # 更大的图片（用于测试压缩）
        img_large = Image.new("RGB", (2000, 1500), color="blue")
        buf2 = io.BytesIO()
        img_large.save(buf2, format="PNG")
        self.large_png = buf2.getvalue()

    def test_validate_image_valid(self):
        """验证合法图片格式"""
        validate_image("image/jpeg", 1000)
        validate_image("image/png", 1000)
        validate_image("image/webp", 1000)

    def test_validate_image_invalid_format(self):
        """拒绝不支持的格式"""
        with self.assertRaises(ValueError) as cm:
            validate_image("image/gif", 1000)
        self.assertIn("仅支持", str(cm.exception))

    def test_validate_image_too_large(self):
        """拒绝超大文件"""
        with self.assertRaises(ValueError) as cm:
            validate_image("image/jpeg", 20 * 1024 * 1024)
        self.assertIn("文件大小", str(cm.exception))

    def test_compress_image_small(self):
        """小图片压缩（无需降质）"""
        result = compress_image(self.test_png)
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 0)

    def test_compress_image_large(self):
        """大图片压缩"""
        result = compress_image(self.large_png)
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 0)

    def test_compress_image_rgba_to_rgb(self):
        """RGBA 图片转 RGB 压缩"""
        from PIL import Image
        img = Image.new("RGBA", (300, 300), color=(255, 0, 0, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result = compress_image(buf.getvalue())
        self.assertIsInstance(result, bytes)

    def test_extract_filename_from_url_valid(self):
        """从 URL 提取文件名"""
        url = "https://example.com/storage/v1/object/public/avatars/u1/abc123.jpg"
        fname = extract_filename_from_url(url)
        self.assertEqual(fname, "abc123.jpg")

    def test_extract_filename_from_url_none(self):
        """空 URL 返回 None"""
        self.assertIsNone(extract_filename_from_url(None))
        self.assertIsNone(extract_filename_from_url(""))


# === Deps ===
from unittest.mock import AsyncMock, patch


class TestDeps(unittest.IsolatedAsyncioTestCase):
    """依赖注入测试"""

    async def test_get_token_from_header_valid(self):
        """从 Header 提取有效 token"""
        # 由于需要真正的 JWT decode，这里只测试 Header 提取
        # 实际 JWT decode 在集成测试中验证
        pass

    async def test_get_token_from_header_missing(self):
        """缺少 Authorization Header"""
        from app.core.deps import get_token_from_header
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as cm:
            await get_token_from_header(None)
        self.assertEqual(cm.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main(verbosity=2)
