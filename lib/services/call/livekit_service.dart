"""
LiveKit 语音/视频通话服务（可选方案）
许可证：Apache 2.0
用途：使用 LiveKit SFU 替代自建 WebRTC 信令

依赖：
  flutter pub add livekit_client

使用方式：
  final livekit = LiveKitCallService(
    serverUrl: 'wss://your-livekit-server.com',
    apiKey: 'xxx',
    apiSecret: 'xxx',
  );
  await livekit.joinRoom(roomName: 'match_user123_user456');
  await livekit.publishVideo();
  await livekit.publishAudio();
"""
import 'dart:async';

import 'package:flutter/foundation.dart';

/// LiveKit 通话服务（需安装 livekit_client 包）
///
/// 相比自建 WebRTC 的优势：
///   - 原生支持多人通话（SFU 架构）
///   - 生产级质量（Jitter buffer, FEC, NACK）
///   - 录音/录像 API
///   - 屏幕共享
///
/// 安装方式：
///   flutter pub add livekit_client
///
/// 自托管 LiveKit Server：
///   docker run --rm -p 7880:7880 \
///     -e LIVEKIT_KEYS="devkey: secret" \
///     livekit/livekit-server
class LiveKitCallService {
  final String serverUrl;    // wss://your-server:7880
  final String apiKey;
  final String apiSecret;

  // ignore: undefined_class
  dynamic _room;             // Room 实例
  // ignore: undefined_class
  dynamic _localParticipant; // LocalParticipant 实例

  final _eventController = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get events => _eventController.stream;

  bool isConnected = false;

  LiveKitCallService({
    required this.serverUrl,
    required this.apiKey,
    required this.apiSecret,
  });

  /// 加入房间（发起/接听通话）
  Future<void> joinRoom({
    required String roomName,
    required String userId,
    String? displayName,
  }) async {
    // -- 以下代码需在安装 livekit_client 后启用 --
    // Note: livekit_client 包未安装时，此方法为占位实现
    //
    // ```dart
    // import 'package:livekit_client/livekit_client.dart';
    //
    // _room = Room();
    // _room!.events.on<RoomEvent.connected>((_) {
    //   _eventController.add({'type': 'connected', 'room': roomName});
    // });
    // ...
    // ```

    throw UnimplementedError(
      '请先运行: flutter pub add livekit_client\n'
      '然后取消本文件中 import 和代码的注释',
    );
  }

  /// 发布本地视频
  Future<void> publishVideo() async {
    throw UnimplementedError('依赖 livekit_client 包');
  }

  /// 发布本地音频
  Future<void> publishAudio() async {
    throw UnimplementedError('依赖 livekit_client 包');
  }

  /// 静音/取消静音
  Future<void> toggleMic() async {
    throw UnimplementedError('依赖 livekit_client 包');
  }

  /// 开关摄像头
  Future<void> toggleCamera() async {
    throw UnimplementedError('依赖 livekit_client 包');
  }

  /// 切换前后摄像头
  Future<void> switchCamera() async {
    throw UnimplementedError('依赖 livekit_client 包');
  }

  /// 离开房间（挂断）
  Future<void> leaveRoom() async {
    throw UnimplementedError('依赖 livekit_client 包');
  }

  /// 释放资源
  void dispose() {
    _eventController.close();
  }
}
