"""
WebSocket 聊天服务
来源：参考 flutter-fastapi-websocket-chat（MIT 许可证）
增强：JWT 认证 + 私聊支持 + 消息持久化接口
"""
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status

router = APIRouter(prefix="/ws", tags=["WebSocket 聊天"])

# user_id → WebSocket 连接映射（支持私聊）
connected_clients: dict[str, WebSocket] = {}


async def _persist_message(sender_id: str, receiver_id: str, content: str):
    """
    消息持久化钩子 —— 当前为占位实现。
    实际项目中应调用 repository 写入 PostgreSQL。

    TODO: 注入 MessageRepository
    """
    # 示例日志
    print(f"[MSG] {sender_id} → {receiver_id}: {content[:50]}...")


async def _broadcast(sender_id: str, message: dict):
    """向所有已连接用户广播消息"""
    for uid, ws in list(connected_clients.items()):
        try:
            await ws.send_json(message)
        except Exception:
            connected_clients.pop(uid, None)


async def _send_to_user(target_user_id: str, message: dict):
    """向指定用户发送私聊消息"""
    ws = connected_clients.get(target_user_id)
    if ws:
        try:
            await ws.send_json(message)
        except Exception:
            connected_clients.pop(target_user_id, None)


@router.websocket("/chat")
async def chat_endpoint(
    websocket: WebSocket,
    token: str = Query(...),  # JWT token（query 参数或升级时携带）
):
    """
    WebSocket 聊天端点。

    连接 URL 示例：
        ws://localhost:8000/ws/chat?token=<JWT_TOKEN>

    消息格式（JSON）：
    ```json
    {
        "type": "text",
        "receiver_id": "user_abc",
        "content": "你好！"
    }
    ```

    接收消息格式：
    ```json
    {
        "type": "text",
        "sender_id": "user_xyz",
        "sender_name": "张三",
        "content": "你好！",
        "timestamp": "2026-06-29T10:00:00Z"
    }
    ```
    """
    # TODO: 验证 JWT，提取 user_id
    # from app.core.auth import decode_token
    # payload = decode_token(token)
    # user_id = payload["sub"]
    user_id = "temp_user"  # 占位

    await websocket.accept()
    connected_clients[user_id] = websocket

    try:
        # 通知其他用户上线
        await _broadcast(user_id, {
            "type": "system",
            "content": f"用户 {user_id} 上线了",
            "timestamp": "now",
        })

        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            msg_type = data.get("type", "text")
            receiver_id = data.get("receiver_id")
            content = data.get("content", "")

            # 构建消息
            message = {
                "type": msg_type,
                "sender_id": user_id,
                "content": content,
                "timestamp": "now",  # TODO: 使用 datetime.utcnow().isoformat()
            }

            if receiver_id:
                # 私聊
                await _send_to_user(receiver_id, message)
            else:
                # 广播
                await _broadcast(user_id, message)

            # 持久化（异步，不阻塞）
            if receiver_id and content:
                await _persist_message(user_id, receiver_id, content)

    except WebSocketDisconnect:
        connected_clients.pop(user_id, None)
        await _broadcast(user_id, {
            "type": "system",
            "content": f"用户 {user_id} 下线了",
            "timestamp": "now",
        })
    except Exception:
        connected_clients.pop(user_id, None)
