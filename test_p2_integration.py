"""
P2 用户资料系统 — 集成测试
针对 Vercel 生产环境 (https://workplace1app.vercel.app)
"""
import httpx
import asyncio
import random
import string

BASE_URL = "https://workplace1app.vercel.app"


def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


async def main():
    passed = 0
    failed = 0
    results = []

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            results.append(f"  [PASS] {name}")
        else:
            failed += 1
            results.append(f"  [FAIL] {name} — {detail}")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # ========================================================
        # 准备：创建两个测试用户
        # ========================================================
        print("=== 准备测试用户 ===")
        suffix = random_string()

        # 用户 A
        phone_a = f"+86{random.randint(10000000000, 99999999999)}"
        email_a = f"test_a_{suffix}@example.com"
        password_a = "Test@1234"

        resp = await client.post("/api/auth/register", json={
            "phone": phone_a, "email": email_a, "password": password_a
        })
        check("create user A", resp.status_code == 201, f"got {resp.status_code}")
        token_a = resp.json()["access_token"] if resp.status_code == 201 else None

        # 用户 B
        phone_b = f"+86{random.randint(100000000000, 999999999999)}"
        email_b = f"test_b_{suffix}@example.com"
        resp = await client.post("/api/auth/register", json={
            "phone": phone_b, "email": email_b, "password": password_a
        })
        check("create user B", resp.status_code == 201, f"got {resp.status_code}")
        token_b = resp.json()["access_token"] if resp.status_code == 201 else None

        if not token_a or not token_b:
            print("用户创建失败，终止测试")
            return

        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # ========================================================
        # 1. GET /me — 获取本人资料（自动创建）
        # ========================================================
        print("\n--- 1. GET /me 获取本人资料 ---")

        resp = await client.get("/api/profile/me", headers=headers_a)
        check("GET /me returns 200", resp.status_code == 200, f"got {resp.status_code}")
        profile_a = resp.json()
        check("profile has id", "id" in profile_a)
        check("profile has user_id", profile_a.get("user_id"))
        check("profile has photos []", profile_a.get("photos") == [])
        check("profile_complete is False", profile_a.get("profile_complete") == False)

        # 无 token 应返回 401
        resp = await client.get("/api/profile/me")
        check("GET /me without token returns 401", resp.status_code == 401, f"got {resp.status_code}")

        # ========================================================
        # 2. PUT /me — 更新个人资料
        # ========================================================
        print("\n--- 2. PUT /me 更新个人资料 ---")

        resp = await client.put("/api/profile/me", headers=headers_a, json={
            "nickname": f"测试用户{suffix[:4]}",
            "bio": "这是一个测试个人简介",
            "gender": "male",
            "city": "北京",
            "interests": ["编程", "篮球", "音乐"],
            "hobbies": ["阅读", "旅行"],
            "looking_for": "serious",
            "preferred_age_min": 22,
            "preferred_age_max": 35,
            "preferred_distance_km": 30,
            "latitude": 39.9042,
            "longitude": 116.4074,
        })
        check("PUT /me returns 200", resp.status_code == 200, f"got {resp.status_code} {resp.text[:100]}")
        if resp.status_code == 200:
            data = resp.json()
            check("nickname updated", data.get("nickname") == f"测试用户{suffix[:4]}")
            check("bio updated", data.get("bio") == "这是一个测试个人简介")
            check("gender updated", data.get("gender") == "male")
            check("interests updated", "编程" in data.get("interests", []))
            check("city updated", data.get("city") == "北京")
            check("coordinates updated", data.get("latitude") == 39.9042)

        # ========================================================
        # 3. PUT /me — 更新生日（自动计算年龄）
        # ========================================================
        print("\n--- 3. PUT /me 更新生日（年龄自动计算） ---")

        resp = await client.put("/api/profile/me", headers=headers_a, json={
            "birthday": "1995-06-15",
        })
        check("birthday update returns 200", resp.status_code == 200, f"got {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            check("age auto-calculated", data.get("age") is not None, f"age={data.get('age')}")

        # ========================================================
        # 4. PUT /me/preferences — 更新择偶偏好
        # ========================================================
        print("\n--- 4. PUT /me/preferences 更新择偶偏好 ---")

        resp = await client.put("/api/profile/me/preferences", headers=headers_a, json={
            "looking_for": "marriage",
            "preferred_age_min": 25,
            "preferred_age_max": 40,
            "preferred_distance_km": 50,
        })
        check("PUT /preferences returns 200", resp.status_code == 200, f"got {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            check("looking_for updated to marriage", data.get("looking_for") == "marriage")
            check("preferred_age_min updated", data.get("preferred_age_min") == 25)

        # ========================================================
        # 5. GET /{user_id} — 查看其他用户公开资料
        # ========================================================
        print("\n--- 5. GET /{user_id} 查看他人公开资料 ---")

        # 先给用户 B 设置资料
        await client.put("/api/profile/me", headers=headers_b, json={
            "nickname": f"B用户{suffix[:4]}",
            "bio": "B用户的简介",
            "gender": "female",
            "city": "上海",
            "interests": ["瑜伽", "咖啡"],
        })

        # 获取 B 的 user_id
        resp_b = await client.get("/api/auth/me", headers=headers_b)
        if resp_b.status_code == 200:
            user_b_id = resp_b.json()["id"]

            # A 查看 B 的公开资料
            resp = await client.get(f"/api/profile/{user_b_id}", headers=headers_a)
            check(f"GET /profile/{user_b_id} returns 200", resp.status_code == 200,
                  f"got {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                check("public profile has nickname", data.get("nickname") == f"B用户{suffix[:4]}")
                check("public profile has bio", "B用户的简介" in data.get("bio", ""))
                check("public profile has city", data.get("city") == "上海")
                check("public profile has interests", "瑜伽" in data.get("interests", []))

        # ========================================================
        # 6. 权限校验 — A 不能修改 B 的资料
        # ========================================================
        print("\n--- 6. 权限校验 ---")

        # PUT /me 只能改自己的（token_a 对应 user_a，无法跨账号）
        # 实际上 PUT /me 总是改 token 对应的用户，所以天然隔离
        # 验证：用 B 的 token 获取 B 的资料，确保没被 A 修改
        resp = await client.get("/api/profile/me", headers=headers_b)
        if resp.status_code == 200:
            data = resp.json()
            check("B nickname unchanged", data.get("nickname") == f"B用户{suffix[:4]}")
            check("B bio unchanged", "B用户的简介" in data.get("bio", ""))

        # ========================================================
        # 7. 资料不公开时的权限校验
        # ========================================================
        print("\n--- 7. 资料不公开权限校验 ---")

        # B 设置资料不公开
        await client.put("/api/profile/me", headers=headers_b, json={
            "is_profile_public": False,
        })

        # A 试图查看 B 的资料，应返回 403
        resp = await client.get(f"/api/profile/{user_b_id}", headers=headers_a)
        check("private profile returns 403", resp.status_code == 403,
              f"got {resp.status_code} {resp.text[:100]}")

        # 恢复 B 的资料公开
        await client.put("/api/profile/me", headers=headers_b, json={
            "is_profile_public": True,
        })

        # ========================================================
        # 8. 查看不存在用户应返回 404
        # ========================================================
        print("\n--- 8. 边界条件测试 ---")

        resp = await client.get("/api/profile/nonexistent_user_999", headers=headers_a)
        check("nonexistent user returns 404", resp.status_code == 404,
              f"got {resp.status_code}")

        # ========================================================
        # 9. 空更新应返回 400
        # ========================================================
        resp = await client.put("/api/profile/me", headers=headers_a, json={})
        check("empty update returns 400", resp.status_code == 400,
              f"got {resp.status_code}")

        # ========================================================
        # 10. P0 兼容性检查
        # ========================================================
        print("\n--- 10. P0 兼容性检查 ---")

        resp = await client.get("/api/health")
        check("health check", resp.status_code == 200, f"got {resp.status_code}")

        resp = await client.get("/api/distance?lat1=39.9&lon1=116.4&lat2=31.2&lon2=121.5")
        check("distance calculation", resp.status_code == 200, f"got {resp.status_code}")

    # ========================================================
    # 结果汇总
    # ========================================================
    print(f"\n{'='*50}")
    for r in results:
        print(r)
    print(f"{'='*50}")
    print(f"  P2 集成测试: {passed}/{passed+failed} PASS")
    if failed > 0:
        print(f"  {failed} FAILED!")
    print(f"{'='*50}")

    return passed, failed


if __name__ == "__main__":
    passed, failed = asyncio.run(main())
    if failed > 0:
        exit(1)
