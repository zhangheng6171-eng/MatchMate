"""P1 用户身份系统 — 端到端集成测试"""
import httpx, asyncio, uuid, os, sys

BASE = "https://workplace1app.vercel.app"
passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} {detail}")

async def test():
    global passed, failed
    async with httpx.AsyncClient(timeout=30) as c:
        phone = f"+86138{uuid.uuid4().hex[:8]}"
        email = f"test_{uuid.uuid4().hex[:8]}@matchmate.test"
        password = "Test@1234"
        print(f"Test phone: {phone}")
        print(f"Test email: {email}")
        print()

        # ============================================================
        # 阶段 1: 验证码发送
        # ============================================================
        print("--- 1. 验证码发送 ---")

        # 1a: 短信注册码
        r = await c.post(f"{BASE}/api/auth/send-code", json={
            "target": phone, "channel": "sms", "purpose": "register"
        })
        check("send sms register code", r.status_code == 200, f"{r.status_code} {r.text[:100]}")
        sms_code = None
        if r.status_code == 200:
            # 从 Console 获取验证码（集成测试需检查 Supabase）
            codes = await get_code_from_db(phone, "register")
            if codes:
                sms_code = codes[0]["code"]
                print(f"      SMS code from DB: {sms_code}")

        # 1b: 邮件注册码
        r = await c.post(f"{BASE}/api/auth/send-code", json={
            "target": email, "channel": "email", "purpose": "register"
        })
        check("send email register code", r.status_code == 200, f"{r.status_code} {r.text[:100]}")

        # 1c: 频道错误
        r = await c.post(f"{BASE}/api/auth/send-code", json={
            "target": phone, "channel": "wechat", "purpose": "register"
        })
        check("reject invalid channel", r.status_code == 422, f"{r.status_code}")

        # 1d: 重复注册拒绝
        # (先创建一个用户，再尝试发注册码)

        # ============================================================
        # 阶段 2: 密码注册
        # ============================================================
        print("\n--- 2. 密码注册 ---")

        # 2a: 手机号注册
        r = await c.post(f"{BASE}/api/auth/register", json={
            "phone": phone, "password": password, "nickname": "TestUser"
        })
        check("phone register (201)", r.status_code == 201, f"{r.status_code} {r.text[:100]}")
        if r.status_code == 201:
            tokens = r.json()
            check("phone register returns tokens", "access_token" in tokens)
            access = tokens["access_token"]

            # 用 access_token 查询 /me
            r2 = await c.get(f"{BASE}/api/auth/me", headers={
                "Authorization": f"Bearer {access}"
            })
            check("GET /me with token", r2.status_code == 200, f"{r2.status_code}")
            if r2.status_code == 200:
                me = r2.json()
                check("me.phone matches", me.get("phone") == phone)
                check("me.is_verified is False", me.get("is_verified") == False)

        # 2b: 重复注册拒绝
        r = await c.post(f"{BASE}/api/auth/register", json={
            "phone": phone, "password": password
        })
        check("duplicate phone register (409)", r.status_code == 409, f"{r.status_code}")

        # 2c: 弱密码拒绝
        r = await c.post(f"{BASE}/api/auth/register", json={
            "email": "weak@test.com", "password": "123"
        })
        check("reject weak password (422)", r.status_code == 422, f"{r.status_code}")

        # 2d: 邮箱注册
        r = await c.post(f"{BASE}/api/auth/register", json={
            "email": email, "password": password
        })
        check("email register (201)", r.status_code == 201, f"{r.status_code}")

        # ============================================================
        # 阶段 3: 密码登录
        # ============================================================
        print("\n--- 3. 密码登录 ---")

        # 3a: 手机号密码登录
        r = await c.post(f"{BASE}/api/auth/login", json={
            "login": phone, "password": password
        })
        check("phone login (200)", r.status_code == 200, f"{r.status_code} {r.text[:100]}")
        if r.status_code == 200:
            tokens = r.json()
            refresh = tokens["refresh_token"]
            access = tokens["access_token"]

        # 3b: 错误密码
        r = await c.post(f"{BASE}/api/auth/login", json={
            "login": phone, "password": "WrongPass1"
        })
        check("wrong password (401)", r.status_code == 401, f"{r.status_code}")

        # 3c: 邮箱登录
        r = await c.post(f"{BASE}/api/auth/login", json={
            "login": email, "password": password
        })
        check("email login (200)", r.status_code == 200, f"{r.status_code}")

        # ============================================================
        # 阶段 4: Token 刷新与注销
        # ============================================================
        print("\n--- 4. Token 刷新与注销 ---")

        # 4a: 刷新
        r = await c.post(f"{BASE}/api/auth/refresh", json={
            "refresh_token": refresh
        })
        check("token refresh (200)", r.status_code == 200, f"{r.status_code} {r.text[:100]}")

        # 4b: 注销
        r = await c.post(f"{BASE}/api/auth/logout", json={
            "refresh_token": refresh
        })
        check("logout (200)", r.status_code == 200, f"{r.status_code}")

        # 4c: 注销后 refresh 应失效（version 递增）
        r = await c.post(f"{BASE}/api/auth/refresh", json={
            "refresh_token": refresh
        })
        check("logout makes token invalid (401)", r.status_code == 401, f"{r.status_code}")

        # ============================================================
        # 阶段 5: 密码找回
        # ============================================================
        print("\n--- 5. 密码找回 ---")

        # 5a: 请求重置（已注册用户）
        r = await c.post(f"{BASE}/api/auth/reset-password/request", json={
            "target": email
        })
        check("request password reset (200)", r.status_code == 200, f"{r.status_code}")

        # 5b: 请求重置（未注册用户，安全不暴露）
        r = await c.post(f"{BASE}/api/auth/reset-password/request", json={
            "target": "nonexist@test.com"
        })
        check("reset unknown user (200, silent)", r.status_code == 200, f"{r.status_code}")

        # ============================================================
        # 阶段 6: 邮箱激活
        # ============================================================
        print("\n--- 6. 邮箱激活 ---")

        # 6a: 发送激活码
        r = await c.post(f"{BASE}/api/auth/send-code", json={
            "target": email, "channel": "email", "purpose": "activate_email"
        })
        check("send activation code (200)", r.status_code == 200, f"{r.status_code}")

        # 6b: 错误激活码
        r = await c.post(f"{BASE}/api/auth/activate-email", json={
            "email": email, "code": "000000"
        })
        check("reject wrong activation code (400)", r.status_code == 400, f"{r.status_code}")

        # 6c: 激活不存在邮箱
        r = await c.post(f"{BASE}/api/auth/activate-email", json={
            "email": "nobody@test.com", "code": "123456"
        })
        check("reject nonexistent email (404)", r.status_code == 404, f"{r.status_code}")

        # ============================================================
        # 阶段 7: 健康检查
        # ============================================================
        print("\n--- 7. 其他 API ---")
        r = await c.get(f"{BASE}/api/health")
        check("health check (200)", r.status_code == 200 and r.json().get("status") == "ok")

        r = await c.get(f"{BASE}/api/distance?lat1=39.9&lon1=116.4&lat2=31.2&lon2=121.5")
        check("distance calculation (200)", r.status_code == 200)

        # ============================================================
        # 结果汇总
        # ============================================================
        print(f"\n{'='*50}")
        print(f"  P1 集成测试: {passed}/{passed+failed} PASS")
        if failed:
            print(f"  FAILED: {failed}")
        print(f"{'='*50}")


async def get_code_from_db(target, purpose):
    """从 Supabase 读取最新验证码"""
    async with httpx.AsyncClient() as c:
        r = await c.get(
            "https://ntaqnyegiiwtzdyqjiwy.supabase.co/rest/v1/verification_codes",
            headers={
                "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50YXFueWVnaWl3dHpkeXFqaXd5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzkxNjg3NSwiZXhwIjoyMDg5NDkyODc1fQ.z8LPpoJoa9_DEJvBmNvSF0Q1I4FA3FNnFRU0PgKcF2A",
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50YXFueWVnaWl3dHpkeXFqaXd5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzkxNjg3NSwiZXhwIjoyMDg5NDkyODc1fQ.z8LPpoJoa9_DEJvBmNvSF0Q1I4FA3FNnFRU0PgKcF2A",
            },
            params={
                "target": f"eq.{target}",
                "purpose": f"eq.{purpose}",
                "order": "created_at.desc",
                "limit": "1",
            },
        )
        if r.status_code == 200:
            return r.json()
        return None


if __name__ == "__main__":
    asyncio.run(test())
