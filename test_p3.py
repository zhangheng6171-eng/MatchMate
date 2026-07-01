"""
P3 即时聊天系统 — 单元测试
测试 schemas / 消息响应构造 / 业务逻辑
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from datetime import datetime, timezone


class TestMessageSchemas(unittest.TestCase):
    """消息 Pydantic Schemas 校验"""

    def test_message_send_valid(self):
        """有效消息发送请求"""
        from app.schemas.message import MessageSendRequest
        req = MessageSendRequest(
            receiver_id="user-abc-123",
            content="Hello, this is a test message!"
        )
        self.assertEqual(req.receiver_id, "user-abc-123")
        self.assertEqual(req.content, "Hello, this is a test message!")
        self.assertEqual(req.message_type, "text")

    def test_message_send_empty_content(self):
        """空消息被拒绝"""
        from app.schemas.message import MessageSendRequest
        with self.assertRaises(Exception):
            MessageSendRequest(receiver_id="user-abc", content="")

    def test_message_send_whitespace_only(self):
        """纯空白消息被拒绝"""
        from app.schemas.message import MessageSendRequest
        with self.assertRaises(Exception):
            MessageSendRequest(receiver_id="user-abc", content="   ")

    def test_message_send_strips_whitespace(self):
        """尾部空白自动 trim"""
        from app.schemas.message import MessageSendRequest
        req = MessageSendRequest(receiver_id="user-abc", content="  hello  ")
        self.assertEqual(req.content, "hello")

    def test_message_send_type_default(self):
        """默认消息类型为 text"""
        from app.schemas.message import MessageSendRequest
        req = MessageSendRequest(receiver_id="user-abc", content="hi")
        self.assertEqual(req.message_type, "text")

    def test_batch_read_valid(self):
        """有效批量已读请求"""
        from app.schemas.message import BatchReadRequest
        req = BatchReadRequest(message_ids=["m1", "m2", "m3"])
        self.assertEqual(len(req.message_ids), 3)

    def test_batch_read_empty(self):
        """空列表被拒绝"""
        from app.schemas.message import BatchReadRequest
        with self.assertRaises(Exception):
            BatchReadRequest(message_ids=[])

    def test_batch_read_too_many(self):
        """超上限被拒绝"""
        from app.schemas.message import BatchReadRequest
        with self.assertRaises(Exception):
            BatchReadRequest(message_ids=[f"m{i}" for i in range(101)])

    def test_message_response_from_db(self):
        """从数据库记录构造 MessageResponse"""
        from app.schemas.message import MessageResponse
        now = datetime.now(timezone.utc).isoformat()
        msg = {
            "id": "msg-1",
            "sender_id": "user-a",
            "receiver_id": "user-b",
            "content": "Hello!",
            "message_type": "text",
            "status": "sent",
            "is_recalled": False,
            "is_deleted_by_sender": False,
            "is_deleted_by_receiver": False,
            "read_at": None,
            "recalled_at": None,
            "created_at": now,
        }
        resp = MessageResponse.from_db(msg, "user-a")
        self.assertEqual(resp.id, "msg-1")
        self.assertEqual(resp.content, "Hello!")
        self.assertEqual(resp.sender_id, "user-a")

    def test_message_response_recalled(self):
        """撤回消息的响应展示"""
        from app.schemas.message import MessageResponse
        now = datetime.now(timezone.utc).isoformat()
        msg = {
            "id": "msg-2",
            "sender_id": "user-a",
            "receiver_id": "user-b",
            "content": "original content",
            "message_type": "text",
            "status": "sent",
            "is_recalled": True,
            "is_deleted_by_sender": False,
            "is_deleted_by_receiver": False,
            "read_at": None,
            "recalled_at": now,
            "created_at": now,
        }
        resp = MessageResponse.from_db(msg, "user-a")
        self.assertEqual(resp.content, "[消息已撤回]")
        self.assertTrue(resp.is_recalled)

    def test_message_response_deleted_sender_view(self):
        """发送方删除后自己的视角"""
        from app.schemas.message import MessageResponse
        now = datetime.now(timezone.utc).isoformat()
        msg = {
            "id": "msg-3",
            "sender_id": "user-a",
            "receiver_id": "user-b",
            "content": "deleted by sender",
            "message_type": "text",
            "status": "sent",
            "is_recalled": False,
            "is_deleted_by_sender": True,
            "is_deleted_by_receiver": False,
            "read_at": None,
            "recalled_at": None,
            "created_at": now,
        }
        resp_a = MessageResponse.from_db(msg, "user-a")
        self.assertTrue(resp_a.is_deleted, "发送方视角应标记已删除")

        resp_b = MessageResponse.from_db(msg, "user-b")
        self.assertFalse(resp_b.is_deleted, "接收方视角不应标记已删除")

    def test_message_response_deleted_receiver_view(self):
        """接收方删除后自己的视角"""
        from app.schemas.message import MessageResponse
        now = datetime.now(timezone.utc).isoformat()
        msg = {
            "id": "msg-4",
            "sender_id": "user-a",
            "receiver_id": "user-b",
            "content": "deleted by receiver",
            "message_type": "text",
            "status": "sent",
            "is_recalled": False,
            "is_deleted_by_sender": False,
            "is_deleted_by_receiver": True,
            "read_at": None,
            "recalled_at": None,
            "created_at": now,
        }
        resp_a = MessageResponse.from_db(msg, "user-a")
        self.assertFalse(resp_a.is_deleted, "发送方视角不应标记已删除")

        resp_b = MessageResponse.from_db(msg, "user-b")
        self.assertTrue(resp_b.is_deleted, "接收方视角应标记已删除")

    def test_conversation_item(self):
        """会话项结构"""
        from app.schemas.message import ConversationItem
        now = datetime.now(timezone.utc).isoformat()
        item = ConversationItem(
            user_id="user-b",
            nickname="小明",
            avatar_url="https://example.com/avatar.jpg",
            last_message="你好！",
            last_message_time=now,
            unread_count=3,
        )
        self.assertEqual(item.user_id, "user-b")
        self.assertEqual(item.nickname, "小明")
        self.assertEqual(item.unread_count, 3)

    def test_conversation_list_response(self):
        """会话列表响应"""
        from app.schemas.message import ConversationListResponse, ConversationItem
        resp = ConversationListResponse(
            conversations=[
                ConversationItem(
                    user_id="u1",
                    last_message="Hello",
                    unread_count=1,
                )
            ]
        )
        self.assertEqual(len(resp.conversations), 1)

    def test_conversation_messages_response(self):
        """对话消息响应"""
        from app.schemas.message import ConversationMessagesResponse, MessageResponse
        resp = ConversationMessagesResponse(
            messages=[],
            has_more=False,
        )
        self.assertEqual(len(resp.messages), 0)
        self.assertFalse(resp.has_more)

    def test_poll_response(self):
        """轮询响应"""
        from app.schemas.message import PollResponse
        resp = PollResponse(messages=[], has_more=False)
        self.assertEqual(len(resp.messages), 0)

    def test_send_response(self):
        """发送响应"""
        from app.schemas.message import SendResponse, MessageResponse
        resp = SendResponse(
            message=MessageResponse(
                id="m1", sender_id="a", receiver_id="b", content="hi"
            ),
            conversation_id="b",
        )
        self.assertEqual(resp.conversation_id, "b")

    def test_message_action_response(self):
        """操作响应"""
        from app.schemas.message import MessageActionResponse
        resp = MessageActionResponse(message="已撤回", message_id="m1")
        self.assertEqual(resp.message, "已撤回")
        self.assertEqual(resp.message_id, "m1")


class TestMessageBusinessLogic(unittest.TestCase):
    """消息业务规则测试"""

    def test_recall_window_constant(self):
        """撤回窗口常量"""
        from app.api.messages import RECALL_WINDOW_MINUTES
        self.assertEqual(RECALL_WINDOW_MINUTES, 2)

    def test_conversation_page_size(self):
        """分页大小常量"""
        from app.api.messages import CONVERSATION_PAGE_SIZE
        self.assertEqual(CONVERSATION_PAGE_SIZE, 30)

    def test_content_rejection_rules(self):
        """内容校验规则"""
        # 空字符串
        from app.schemas.message import MessageSendRequest
        with self.assertRaises(Exception):
            MessageSendRequest(receiver_id="u1", content="")
        with self.assertRaises(Exception):
            MessageSendRequest(receiver_id="u1", content="   ")
        # 有效
        req = MessageSendRequest(receiver_id="u1", content="valid")
        self.assertEqual(req.content, "valid")


if __name__ == "__main__":
    unittest.main(verbosity=2)
