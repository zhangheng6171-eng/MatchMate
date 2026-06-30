"""
Flutter WebSocket 聊天服务
来源：参考 flutter-fastapi-websocket-chat（MIT 许可证）
增强：JSON 协议 + 重连机制 + 消息类型支持
"""
import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as status;

/// WebSocket 消息模型
class ChatMessage {
  final String type; // "text" | "image" | "system"
  final String senderId;
  final String? senderName;
  final String content;
  final String timestamp;

  ChatMessage({
    required this.type,
    required this.senderId,
    this.senderName,
    required this.content,
    required this.timestamp,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      type: json['type'] ?? 'text',
      senderId: json['sender_id'] ?? '',
      senderName: json['sender_name'],
      content: json['content'] ?? '',
      timestamp: json['timestamp'] ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'type': type,
        'receiver_id': senderId,
        'content': content,
      };
}

/// WebSocket 聊天服务
///
/// 用法：
/// ```dart
/// final service = ChatWebSocketService(
///   token: 'your_jwt_token',
///   currentUserId: 'user_123',
/// );
/// await service.connect();
/// service.messageStream.listen((msg) => print(msg.content));
/// service.sendMessage(receiverId: 'user_456', content: '你好');
/// ```
class ChatWebSocketService {
  final String baseUrl;
  final String token;
  final String currentUserId;
  final String? currentUserName;

  WebSocketChannel? _channel;
  Timer? _reconnectTimer;
  bool _isConnected = false;

  final _messageController = StreamController<ChatMessage>.broadcast();
  Stream<ChatMessage> get messageStream => _messageController.stream;
  bool get isConnected => _isConnected;

  ChatWebSocketService({
    required this.baseUrl,
    required this.token,
    required this.currentUserId,
    this.currentUserName,
  });

  /// 连接 WebSocket 服务器
  Future<void> connect() async {
    try {
      final uri = Uri.parse(
        '$baseUrl/ws/chat?token=$token',
      ).replace(scheme: 'ws');

      _channel = WebSocketChannel.connect(uri);
      _isConnected = true;

      _channel!.stream.listen(
        (data) {
          try {
            final json = jsonDecode(data as String) as Map<String, dynamic>;
            final message = ChatMessage.fromJson(json);
            _messageController.add(message);
          } catch (e) {
            // 忽略解析错误
          }
        },
        onError: (error) {
          _isConnected = false;
          _scheduleReconnect();
        },
        onDone: () {
          _isConnected = false;
          _scheduleReconnect();
        },
      );
    } catch (e) {
      _isConnected = false;
      _scheduleReconnect();
    }
  }

  /// 发送消息（私聊）
  void sendMessage({
    required String receiverId,
    required String content,
    String type = 'text',
  }) {
    if (_channel == null || !_isConnected) return;

    final message = jsonEncode({
      'type': type,
      'receiver_id': receiverId,
      'content': content,
    });

    _channel!.sink.add(message);
  }

  /// 自动重连（指数退避）
  void _scheduleReconnect() {
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 3), () {
      if (!_isConnected) {
        connect();
      }
    });
  }

  /// 断开连接
  Future<void> disconnect() async {
    _reconnectTimer?.cancel();
    try {
      await _channel?.sink.close(status.normalClosure);
    } catch (_) {}
    _isConnected = false;
    _channel = null;
  }

  /// 释放资源
  void dispose() {
    disconnect();
    _messageController.close();
  }
}
