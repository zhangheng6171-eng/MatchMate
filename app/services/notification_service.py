"""
短信/邮件发送服务 — 适配器模式

development: Console 输出（开发调试）
production:  真实短信/邮件 Provider（腾讯云SMS / 阿里云短信 / SendGrid）

使用方式:
    from app.services.notification_service import notification_service
    await notification_service.send_code(target="+8613800138000", code="123456", channel="sms", purpose="register")
"""
import os
import logging
import httpx
from abc import ABC, abstractmethod

logger = logging.getLogger("notification_service")


# ============================================================
# 抽象适配器接口
# ============================================================
class NotificationAdapter(ABC):
    """通知适配器抽象基类"""

    @abstractmethod
    async def send_sms(self, phone: str, code: str, purpose: str) -> bool:
        """发送短信验证码"""
        ...

    @abstractmethod
    async def send_email(self, email: str, code: str, purpose: str) -> bool:
        """发送邮件验证码"""
        ...


# ============================================================
# 开发环境适配器: Console 输出
# ============================================================
class ConsoleAdapter(NotificationAdapter):
    """开发环境：控制台输出验证码"""

    async def send_sms(self, phone: str, code: str, purpose: str) -> bool:
        print(f"\n{'='*50}")
        print(f"[开发期] 📱 短信验证码")
        print(f"  目标: {phone}")
        print(f"  用途: {purpose}")
        print(f"  验证码: {code}")
        print(f"  有效期: 5 分钟")
        print(f"{'='*50}\n")
        return True

    async def send_email(self, email: str, code: str, purpose: str) -> bool:
        print(f"\n{'='*50}")
        print(f"[开发期] 📧 邮件验证码")
        print(f"  目标: {email}")
        print(f"  用途: {purpose}")
        print(f"  验证码: {code}")
        print(f"  有效期: 5 分钟")
        print(f"{'='*50}\n")
        return True


# ============================================================
# 生产环境适配器: 真实 Provider
# ============================================================
class TencentCloudSMSAdapter(NotificationAdapter):
    """
    腾讯云短信服务适配器

    前置条件:
        1. 腾讯云控制台开通 SMS 服务
        2. 创建应用，获取 SDK App ID
        3. 创建签名 + 模板，获取 Template ID
        4. 获取 SecretId 和 SecretKey

    环境变量:
        TENCENT_SMS_SECRET_ID:    腾讯云 API SecretId
        TENCENT_SMS_SECRET_KEY:   腾讯云 API SecretKey
        TENCENT_SMS_SDK_APP_ID:   短信应用 ID
        TENCENT_SMS_TEMPLATE_ID:  短信模板 ID
        TENCENT_SMS_SIGN_NAME:    短信签名
    """

    API_ENDPOINT = "https://sms.tencentcloudapi.com"

    def __init__(self):
        self.secret_id = os.getenv("TENCENT_SMS_SECRET_ID", "")
        self.secret_key = os.getenv("TENCENT_SMS_SECRET_KEY", "")
        self.sdk_app_id = os.getenv("TENCENT_SMS_SDK_APP_ID", "")
        self.template_id = os.getenv("TENCENT_SMS_TEMPLATE_ID", "")
        self.sign_name = os.getenv("TENCENT_SMS_SIGN_NAME", "")

    @property
    def is_configured(self) -> bool:
        return all([self.secret_id, self.secret_key, self.sdk_app_id, self.template_id])

    async def send_sms(self, phone: str, code: str, purpose: str) -> bool:
        if not self.is_configured:
            logger.warning("腾讯云SMS未配置，降级为Console输出")
            return await ConsoleAdapter().send_sms(phone, code, purpose)

        # 腾讯云 SMS API v3 签名
        import hashlib
        import hmac
        from datetime import datetime, timezone

        # 标准化手机号格式
        phone_number = phone.lstrip("+")

        payload = {
            "PhoneNumberSet": [phone_number],
            "SmsSdkAppId": self.sdk_app_id,
            "TemplateId": self.template_id,
            "SignName": self.sign_name,
            "TemplateParamSet": [code],
        }

        try:
            # TODO: 实现完整的腾讯云 API v3 签名流程
            # 当前为简化实现，生产使用时需补充:
            # 1. TC3-HMAC-SHA256 签名算法
            # 2. Authorization Header 构造
            # 3. 日期/服务名计算
            logger.info(
                f"[TencentSMS] 准备发送: phone={phone_number} code={code} "
                f"app_id={self.sdk_app_id} template={self.template_id}"
            )

            # 实际发送逻辑（需接入腾讯云SDK或手动实现签名）
            # async with httpx.AsyncClient(timeout=10) as client:
            #     resp = await client.post(self.API_ENDPOINT, headers=headers, json=payload)
            #     if resp.status_code == 200:
            #         result = resp.json()
            #         return result.get("Response", {}).get("SendStatusSet", [{}])[0].get("Code") == "Ok"

            # 未配置真实凭证时，记录日志并返回成功（模拟）
            logger.warning(
                f"[TencentSMS-未配置] 短信未实际发送: phone={phone_number} code={code}"
            )
            return False  # 未配置真实凭证时返回 False

        except Exception as e:
            logger.error(f"[TencentSMS] 发送失败: {e}")
            raise


class AlibabaCloudSMSAdapter(NotificationAdapter):
    """
    阿里云短信服务适配器

    环境变量:
        ALIBABA_SMS_ACCESS_KEY_ID:     阿里云 AccessKeyId
        ALIBABA_SMS_ACCESS_KEY_SECRET: 阿里云 AccessKeySecret
        ALIBABA_SMS_SIGN_NAME:         短信签名
        ALIBABA_SMS_TEMPLATE_CODE:     短信模板Code
    """

    API_ENDPOINT = "https://dysmsapi.aliyuncs.com"

    def __init__(self):
        self.access_key_id = os.getenv("ALIBABA_SMS_ACCESS_KEY_ID", "")
        self.access_key_secret = os.getenv("ALIBABA_SMS_ACCESS_KEY_SECRET", "")
        self.sign_name = os.getenv("ALIBABA_SMS_SIGN_NAME", "")
        self.template_code = os.getenv("ALIBABA_SMS_TEMPLATE_CODE", "")

    @property
    def is_configured(self) -> bool:
        return all([self.access_key_id, self.access_key_secret, self.sign_name, self.template_code])

    async def send_sms(self, phone: str, code: str, purpose: str) -> bool:
        if not self.is_configured:
            logger.warning("阿里云SMS未配置，降级为Console输出")
            return await ConsoleAdapter().send_sms(phone, code, purpose)

        phone_number = phone.lstrip("+")
        logger.info(f"[AlibabaSMS] 准备发送: phone={phone_number} code={code}")

        # TODO: 实现阿里云 SMS API 签名和调用
        logger.warning(f"[AlibabaSMS-未配置] 短信未实际发送: phone={phone_number} code={code}")
        return False

    async def send_email(self, email: str, code: str, purpose: str) -> bool:
        # 阿里云短信不支持邮件，降级到 Console
        return await ConsoleAdapter().send_email(email, code, purpose)


# ============================================================
# 通知服务管理器
# ============================================================
class NotificationService:
    """通知服务管理器 — 根据环境自动选择适配器"""

    def __init__(self):
        self._adapter: NotificationAdapter | None = None

    @property
    def adapter(self) -> NotificationAdapter:
        if self._adapter is None:
            environment = os.getenv("ENVIRONMENT", "development")

            if environment == "production":
                # 优先腾讯云 SMS，备选阿里云 SMS
                tencent = TencentCloudSMSAdapter()
                if tencent.is_configured:
                    logger.info("[NotificationService] 使用腾讯云短信服务")
                    self._adapter = tencent
                else:
                    alibaba = AlibabaCloudSMSAdapter()
                    if alibaba.is_configured:
                        logger.info("[NotificationService] 使用阿里云短信服务")
                        self._adapter = alibaba
                    else:
                        logger.warning(
                            "[NotificationService] 生产环境未配置任何SMS Provider，"
                            "降级为Console输出"
                        )
                        self._adapter = ConsoleAdapter()
            else:
                self._adapter = ConsoleAdapter()

        return self._adapter

    async def send_verification_code(
        self, target: str, code: str, channel: str, purpose: str
    ) -> bool:
        """发送验证码"""
        if channel == "sms":
            return await self.adapter.send_sms(target, code, purpose)
        elif channel == "email":
            return await self.adapter.send_email(target, code, purpose)
        else:
            logger.error(f"未知的通知渠道: {channel}")
            return False


# 全局单例
notification_service = NotificationService()
