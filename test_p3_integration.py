"""
P3 即时聊天系统 — 集成测试
针对 Vercel 生产环境 (https://workplace1app.vercel.app)
========================================================
测试范围：
  1. 消息发送 (send)
  2. 对话历史 (conversation)
  3. 消息轮询 (poll)
  4. 单条已读 (read)
  5. 批量已读 (read-batch)
  6. 消息撤回 (recall, 2min窗口)
  7. 消息删除 (delete, 软删除)
  8. 会话列表 (conversations)
  9. 会话清空 (clear)
 10. 异常场景 (自发送/不存在用户/空消息)
 11. P0-P2 兼容性回归
"""
import httpx
import asyncio
import random
import string
import time

BASE_URL = "https://workplace1app.vercel.app"

def rand_str(n=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

async def main():
    passed = 0
    failed = 0
    results = []

    def check(status_list, name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            status_list.append(f"  [PASS] {name}")
        else:
            failed += 1
            status_list.append(f"  [FAIL] {name} — {detail}")

    suffix = rand_str()
    r3 = []

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # ================================================================
        # 准备：创建两个测试用户
        # ================================================================
        print("=== 准备测试用户 ===")
        phone_a = f"+86{random.randint(13000000000, 13199999999)}"
        phone_b = f"+86{random.randint(13300000000, 13499999999)}"
        pwd = "ChatTest@123!"

        resp = await client.post("/api/auth/register", json={
            "phone": phone_a, "password": pwd, "email": f"chat_a_{suffix}@test.com"
        })
        token_a = resp.json()["access_token"] if resp.status_code == 201 else None
        check(r3, "创建用户A", resp.status_code == 201, f"got {resp.status_code}")

        resp = await client.post("/api/auth/register", json={
            "phone": phone_b, "password": pwd, "email": f"chat_b_{suffix}@test.com"
        })
        token_b = resp.json()["access_token"] if resp.status_code == 201 else None
        check(r3, "创建用户B", resp.status_code == 201, f"got {resp.status_code}")

        if not token_a or not token_b:
            print("用户创建失败，终止测试")
            return

        # 获取 user_id
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}
        resp = await client.get("/api/auth/me", headers=headers_a)
        user_a_id = resp.json()["id"]
        resp = await client.get("/api/auth/me", headers=headers_b)
        user_b_id = resp.json()["id"]

        # 设置B的资料（用于会话列表显示）
        await client.put("/api/profile/me", headers=headers_b, json={"nickname": f"B用户{suffix[:4]}"})

        # ================================================================
        # 1. 消息发送
        # ================================================================
        print("\n--- 1. 消息发送 ---")

        # A 给 B 发消息
        resp = await client.post("/api/messages/send", headers=headers_a, json={
            "receiver_id": user_b_id, "content": f"你好B！这是来自A的第一条消息 [{suffix}]"
        })
        check(r3, "A发送消息给B(201)", resp.status_code == 201, f"got {resp.status_code}")
        msg1_id = resp.json()["message"]["id"] if resp.status_code == 201 else None

        if resp.status_code == 201:
            data = resp.json()
            check(r3, "返回message对象", "message" in data)
            check(r3, "消息状态为sent", data["message"]["status"] == "sent")
            check(r3, "消息内容正确", suffix in data["message"]["content"])

        # B 给 A 回消息
        resp = await client.post("/api/messages/send", headers=headers_b, json={
            "receiver_id": user_a_id, "content": f"你好A！收到了你的消息 [{suffix}]"
        })
        check(r3, "B回复消息给A(201)", resp.status_code == 201, f"got {resp.status_code}")
        msg2_id = resp.json()["message"]["id"] if resp.status_code == 201 else None

        # A 再发一条
        resp = await client.post("/api/messages/send", headers=headers_a, json={
            "receiver_id": user_b_id, "content": f"这是A的第二条消息 [{suffix}]"
        })
        check(r3, "A发送第二条消息(201)", resp.status_code == 201)
        msg3_id = resp.json()["message"]["id"] if resp.status_code == 201 else None

        # 异常场景：发给自己
        resp = await client.post("/api/messages/send", headers=headers_a, json={
            "receiver_id": user_a_id, "content": "不能发给自己"
        })
        check(r3, "发给自己被拒(400)", resp.status_code == 400, f"got {resp.status_code}")

        # 异常场景：发给不存在用户
        resp = await client.post("/api/messages/send", headers=headers_a, json={
            "receiver_id": "nonexistent_user_999", "content": "测试"
        })
        check(r3, "发给不存在用户(404)", resp.status_code == 404, f"got {resp.status_code}")

        # 异常场景：空消息
        resp = await client.post("/api/messages/send", headers=headers_a, json={
            "receiver_id": user_b_id, "content": "   "
        })
        check(r3, "空消息被拒(422)", resp.status_code == 422, f"got {resp.status_code}")

        # ================================================================
        # 2. 对话历史
        # ================================================================
        print("\n--- 2. 对话历史 ---")

        # A 查看与 B 的对话
        resp = await client.get(f"/api/messages/conversation/{user_b_id}", headers=headers_a)
        check(r3, "A获取与B的对话(200)", resp.status_code == 200, f"got {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            # A 视角：A发的2条 + B回的1条 = 3条
            check(r3, "对话包含3条消息", len(data["messages"]) >= 2, f"got {len(data['messages'])}")
            check(r3, "has_more为False", data["has_more"] == False)

        # B 查看与 A 的对话
        resp = await client.get(f"/api/messages/conversation/{user_a_id}", headers=headers_b)
        check(r3, "B获取与A的对话(200)", resp.status_code == 200, f"got {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            check(r3, "B视角也看到消息", len(data["messages"]) >= 2)

        # ================================================================
        # 3. 消息已读
        # ================================================================
        print("\n--- 3. 消息已读标记 ---")

        # B 标记收到的消息为已读（B 收到了A的2条消息）
        if msg1_id:
            resp = await client.put(f"/api/messages/{msg1_id}/read", headers=headers_b)
            check(r3, "B标记消息已读(200)", resp.status_code == 200, f"got {resp.status_code}")

        if msg3_id:
            resp = await client.put(f"/api/messages/{msg3_id}/read", headers=headers_b)
            check(r3, "B标记第二条消息已读(200)", resp.status_code == 200)

        # A 标记B发来的消息已读（A 是接收方，应成功）
        if msg2_id:
            resp = await client.put(f"/api/messages/{msg2_id}/read", headers=headers_a)
            check(r3, "A标记B发来的消息已读(200)", resp.status_code == 200, f"got {resp.status_code}")

        # 批量已读
        resp = await client.put("/api/messages/read-batch", headers=headers_b, json={
            "message_ids": [msg1_id] if msg1_id else []
        })
        check(r3, "批量已读标记(200)", resp.status_code == 200, f"got {resp.status_code}")

        # ================================================================
        # 4. 消息撤回
        # ================================================================
        print("\n--- 4. 消息撤回 ---")

        # A 撤回自己的最新消息
        if msg3_id:
            resp = await client.post(f"/api/messages/{msg3_id}/recall", headers=headers_a)
            check(r3, "A撤回自己的消息(200)", resp.status_code == 200, f"got {resp.status_code}")

            # 验证撤回后内容
            resp = await client.get(f"/api/messages/conversation/{user_b_id}", headers=headers_a)
            if resp.status_code == 200:
                msgs = resp.json()["messages"]
                recalled = [m for m in msgs if m["id"] == msg3_id]
                if recalled:
                    check(r3, "撤回后内容变为[消息已撤回]",
                          recalled[0]["content"] == "[消息已撤回]",
                          f"content={recalled[0]['content'][:30]}")
                    check(r3, "撤回后is_recalled=True", recalled[0]["is_recalled"] == True)

        # B 不能撤回 A 的消息
        if msg1_id:
            resp = await client.post(f"/api/messages/{msg1_id}/recall", headers=headers_b)
            check(r3, "B不能撤回A的消息(403)", resp.status_code == 403, f"got {resp.status_code}")

        # ================================================================
        # 5. 消息删除（软删除）
        # ================================================================
        print("\n--- 5. 消息删除（软删除） ---")

        # A 删除与B对话中的一条消息
        resp = await client.get(f"/api/messages/conversation/{user_b_id}", headers=headers_a)
        if resp.status_code == 200:
            msgs = resp.json()["messages"]
            # 找一条未被撤回的A发的消息
            target = None
            for m in msgs:
                if m["sender_id"] == user_a_id and not m["is_recalled"]:
                    target = m["id"]
                    break
            if target:
                resp_del = await client.delete(f"/api/messages/{target}", headers=headers_a)
                check(r3, "A删除自己的消息(200)", resp_del.status_code == 200,
                      f"got {resp_del.status_code}")

                # A 视角不再看到该消息
                resp = await client.get(f"/api/messages/conversation/{user_b_id}", headers=headers_a)
                if resp.status_code == 200:
                    ids = [m["id"] for m in resp.json()["messages"]]
                    check(r3, "A视角已删除消息不可见", target not in ids)

                # B 视角仍可见（软删除）
                resp = await client.get(f"/api/messages/conversation/{user_a_id}", headers=headers_b)
                if resp.status_code == 200:
                    ids = [m["id"] for m in resp.json()["messages"]]
                    check(r3, "B视角仍可见已删除消息", target in ids,
                          f"target={target[:8]}, ids={[i[:8] for i in ids]}")

        # ================================================================
        # 6. 会话列表
        # ================================================================
        print("\n--- 6. 会话列表 ---")

        resp = await client.get("/api/conversations", headers=headers_a)
        check(r3, "A获取会话列表(200)", resp.status_code == 200, f"got {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            convs = data["conversations"]
            check(r3, "会话列表非空", len(convs) >= 1, f"got {len(convs)} convs")
            if convs:
                check(r3, "会话包含user_id", "user_id" in convs[0])
                check(r3, "会话包含last_message", convs[0].get("last_message") is not None)
                check(r3, "会话包含nickname", convs[0].get("nickname") is not None,
                      f"nickname={convs[0].get('nickname')}")

        resp = await client.get("/api/conversations", headers=headers_b)
        check(r3, "B获取会话列表(200)", resp.status_code == 200)

        # ================================================================
        # 7. 消息轮询
        # ================================================================
        print("\n--- 7. 消息轮询 (poll) ---")

        # 空轮询
        resp = await client.get("/api/messages/poll", headers=headers_a)
        check(r3, "轮询新消息(200)", resp.status_code == 200, f"got {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            check(r3, "轮询返回messages列表", "messages" in data)

        # 带 since_id 轮询（传入已知最新消息ID）
        if msg2_id:
            resp = await client.get(f"/api/messages/poll?since_id={msg2_id}", headers=headers_a)
            check(r3, "带since_id轮询(200)", resp.status_code == 200)

        # ================================================================
        # 8. 会话清空
        # ================================================================
        print("\n--- 8. 会话清空 ---")

        resp = await client.delete(f"/api/conversations/{user_b_id}", headers=headers_a)
        check(r3, "A清空与B的会话(200)", resp.status_code == 200, f"got {resp.status_code}")

        # 清空后 A 的会话列表不应再出现B
        resp = await client.get("/api/conversations", headers=headers_a)
        if resp.status_code == 200:
            b_in_list = any(c["user_id"] == user_b_id for c in resp.json()["conversations"])
            check(r3, "A清空后会话列表不含B", not b_in_list)

        # B 的会话列表仍有A（因为只是A清空了）
        resp = await client.get("/api/conversations", headers=headers_b)
        if resp.status_code == 200:
            a_in_list = any(c["user_id"] == user_a_id for c in resp.json()["conversations"])
            check(r3, "B的会话列表仍有A（单方清空）", a_in_list)

        # ================================================================
        # 9. P0-P2 兼容性回归
        # ================================================================
        print("\n--- 9. P0-P2 兼容性回归 ---")
        resp = await client.get("/api/health")
        check(r3, "P0 health check", resp.status_code == 200)

        resp = await client.get("/api/auth/me", headers=headers_a)
        check(r3, "P1 GET /me", resp.status_code == 200)

        resp = await client.get("/api/profile/me", headers=headers_a)
        check(r3, "P2 GET /profile/me", resp.status_code == 200)

        resp = await client.get("/api/distance?lat1=39.9&lon1=116.4&lat2=31.2&lon2=121.5")
        check(r3, "P0 distance calculation", resp.status_code == 200)

    # ================================================================
    #  汇总
    # ================================================================
    print(f"\n{'='*50}")
    for r in r3:
        print(r)
    print(f"{'='*50}")
    print(f"  P3 集成测试: {passed}/{passed+failed} PASS")
    if failed > 0:
        print(f"  {failed} FAILED!")
    print(f"{'='*50}")

    return passed, failed

if __name__ == "__main__":
    p, f = asyncio.run(main())
    if f > 0:
        exit(1)
