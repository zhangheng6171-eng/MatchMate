"""
Flutter WebRTC 语音/视频通话 Notifier（Riverpod）
来源：flutter_chat (aliyazdi75) lib/blocs/call/ + lib/blocs/web_rtc/
许可证：MIT（重写为 Riverpod）
适配变更：
  - Bloc Events/States → Riverpod Notifier + State classes
  - SignalR → FastAPI WebSocket 信令
  - freezed Builder → equatable / 手动 copyWith
  - 合并 CallBloc + WebRTCBloc 为单一 Notifier
"""
import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';

/// 通话状态枚举
enum CallStatus {
  idle,          // 空闲
  ready,         // 准备就绪（已连接信令）
  ringing,       // 振铃中（收到来电/等待对方接听）
  handshaking,   // WebRTC 握手（Offer/Answer/ICE）
  inCall,        // 通话中
  hangUp,        // 已挂断
  rejected,      // 对方拒绝
}

/// 通话端类型
enum CallRole { caller, callee }

/// 通话 Notifier 状态
class CallState {
  final CallStatus status;
  final CallRole role;
  final String? remoteUserId;
  final String? remoteUserName;
  final bool isVideoCall;

  // 视频渲染器
  final RTCVideoRenderer? localRenderer;
  final RTCVideoRenderer? remoteRenderer;

  // 媒体流
  final MediaStream? localStream;
  final MediaStream? remoteStream;

  // 设备控制
  final bool isCameraOn;
  final bool isMicOn;
  final bool isFrontCamera;
  final bool hasTorch;
  final bool isTorchOn;

  const CallState({
    this.status = CallStatus.idle,
    this.role = CallRole.caller,
    this.remoteUserId,
    this.remoteUserName,
    this.isVideoCall = true,
    this.localRenderer,
    this.remoteRenderer,
    this.localStream,
    this.remoteStream,
    this.isCameraOn = true,
    this.isMicOn = true,
    this.isFrontCamera = true,
    this.hasTorch = false,
    this.isTorchOn = false,
  });

  CallState copyWith({
    CallStatus? status,
    CallRole? role,
    String? remoteUserId,
    String? remoteUserName,
    bool? isVideoCall,
    RTCVideoRenderer? localRenderer,
    RTCVideoRenderer? remoteRenderer,
    MediaStream? localStream,
    MediaStream? remoteStream,
    bool? isCameraOn,
    bool? isMicOn,
    bool? isFrontCamera,
    bool? hasTorch,
    bool? isTorchOn,
  }) {
    return CallState(
      status: status ?? this.status,
      role: role ?? this.role,
      remoteUserId: remoteUserId ?? this.remoteUserId,
      remoteUserName: remoteUserName ?? this.remoteUserName,
      isVideoCall: isVideoCall ?? this.isVideoCall,
      localRenderer: localRenderer ?? this.localRenderer,
      remoteRenderer: remoteRenderer ?? this.remoteRenderer,
      localStream: localStream ?? this.localStream,
      remoteStream: remoteStream ?? this.remoteStream,
      isCameraOn: isCameraOn ?? this.isCameraOn,
      isMicOn: isMicOn ?? this.isMicOn,
      isFrontCamera: isFrontCamera ?? this.isFrontCamera,
      hasTorch: hasTorch ?? this.hasTorch,
      isTorchOn: isTorchOn ?? this.isTorchOn,
    );
  }
}

/// WebRTC 通话 Notifier（Riverpod）
///
/// 用法：
/// ```dart
/// final callNotifier = ref.watch(callNotifierProvider.notifier);
/// callNotifier.initiateCall(userId: 'user_456', isVideo: true);
/// callNotifier.acceptCall();
/// callNotifier.hangUp();
/// ```
class CallNotifier extends ValueNotifier<CallState> {
  RTCPeerConnection? _peerConnection;
  final String _currentUserId;
  final void Function(String userId, Map<String, dynamic> signal) _onSendSignal;

  CallNotifier({
    required String currentUserId,
    required void Function(String userId, Map<String, dynamic> signal) onSendSignal,
  })  : _currentUserId = currentUserId,
        _onSendSignal = onSendSignal,
        super(const CallState());

  // ======= 公开 API =======

  /// 发起语音通话
  Future<void> startVoiceCall({
    required String userId,
    String? userName,
  }) async {
    await _startCall(userId: userId, userName: userName, isVideo: false);
  }

  /// 发起视频通话
  Future<void> startVideoCall({
    required String userId,
    String? userName,
  }) async {
    await _startCall(userId: userId, userName: userName, isVideo: true);
  }

  /// 接听来电
  Future<void> acceptCall() async {
    assert(value.status == CallStatus.ringing);
    value = value.copyWith(status: CallStatus.handshaking);

    await _initPeerConnection();
    await _initLocalStream(isVideo: value.isVideoCall);

    // 创建 Answer
    await _peerConnection!.setRemoteDescription(
      RTCSessionDescription(
        _pendingOffer?['sdp'],
        _pendingOffer?['type'] ?? 'offer',
      ),
    );
    final answer = await _peerConnection!.createAnswer();
    await _peerConnection!.setLocalDescription(answer);

    // 发送 Answer
    _onSendSignal(value.remoteUserId!, {
      'type': 'answer',
      'sdp': answer.sdp,
    });

    value = value.copyWith(status: CallStatus.inCall);
  }

  /// 挂断电话
  Future<void> hangUp() async {
    _onSendSignal(value.remoteUserId!, {
      'type': 'hangup',
      'userId': _currentUserId,
    });

    await _cleanup();
    value = value.copyWith(status: CallStatus.hangUp);
  }

  /// 切换摄像头
  Future<void> switchCamera() async {
    if (value.localStream == null) return;
    for (final track in value.localStream!.getVideoTracks()) {
      await track.switchCamera();
    }
    final isFront = !value.isFrontCamera;
    value = value.copyWith(
      isFrontCamera: isFront,
      hasTorch: !isFront ? await _checkTorch() : false,
      isTorchOn: false,
    );
  }

  /// 切换麦克风静音
  void toggleMic() {
    if (value.localStream == null) return;
    final muted = !value.isMicOn;
    for (final track in value.localStream!.getAudioTracks()) {
      track.enabled = !muted;
    }
    value = value.copyWith(isMicOn: !muted);
  }

  /// 切换摄像头开关
  void toggleCamera() {
    if (value.localStream == null) return;
    final enabled = !value.isCameraOn;
    for (final track in value.localStream!.getVideoTracks()) {
      track.enabled = enabled;
    }
    value = value.copyWith(isCameraOn: enabled);
  }

  /// 切换手电筒
  Future<void> toggleTorch() async {
    if (!value.hasTorch || value.localStream == null) return;
    final on = !value.isTorchOn;
    for (final track in value.localStream!.getVideoTracks()) {
      await track.enableSpeakerphone(on);
    }
    value = value.copyWith(isTorchOn: on);
  }

  /// 处理信令消息（由 WebSocket 服务调用）
  void handleSignal(Map<String, dynamic> signal) {
    final type = signal['type'] as String?;

    switch (type) {
      case 'offer':
        _handleOffer(signal);
        break;
      case 'answer':
        _handleAnswer(signal);
        break;
      case 'ice_candidate':
        _handleIceCandidate(signal);
        break;
      case 'hangup':
        _handleHangUp(signal);
        break;
      case 'reject':
        _handleReject(signal);
        break;
    }
  }

  /// 释放资源
  void disposeResources() {
    _cleanup();
    super.dispose();
  }

  // ======= 内部实现 =======

  Map<String, dynamic>? _pendingOffer;

  Future<void> _startCall({
    required String userId,
    String? userName,
    required bool isVideo,
  }) async {
    value = value.copyWith(
      role: CallRole.caller,
      remoteUserId: userId,
      remoteUserName: userName,
      isVideoCall: isVideo,
      status: CallStatus.handshaking,
    );

    await _initPeerConnection();
    await _initLocalStream(isVideo: isVideo);

    // 创建 Offer
    final offer = await _peerConnection!.createOffer();
    await _peerConnection!.setLocalDescription(offer);

    // 发送 Offer
    _onSendSignal(userId, {
      'type': 'offer',
      'sdp': offer.sdp,
      'is_video': isVideo,
      'caller_name': userName ?? _currentUserId,
    });

    value = value.copyWith(status: CallStatus.ringing);
  }

  Future<void> _initPeerConnection() async {
    _peerConnection = await createPeerConnection({
      'iceServers': [
        {'urls': 'stun:stun.l.google.com:19302'},
        {'urls': 'stun:stun1.l.google.com:19302'},
      ],
    });

    _peerConnection!.onIceCandidate = (candidate) {
      _onSendSignal(value.remoteUserId!, {
        'type': 'ice_candidate',
        'candidate': candidate.toMap(),
      });
    };

    _peerConnection!.onAddStream = (stream) {
      value = value.copyWith(
        remoteStream: stream,
        remoteRenderer: value.remoteRenderer?..srcObject = stream,
      );
    };
  }

  Future<void> _initLocalStream({required bool isVideo}) async {
    final mediaConstraints = <String, dynamic>{
      'audio': true,
      'video': isVideo
          ? {
              'mandatory': {
                'minWidth': '640',
                'minHeight': '480',
                'minFrameRate': '30',
              },
              'facingMode': 'user',
              'optional': [],
            }
          : false,
    };

    final stream = await navigator.mediaDevices.getUserMedia(mediaConstraints);
    value = value.copyWith(
      localStream: stream,
      localRenderer: value.localRenderer?..srcObject = stream,
    );

    for (final track in stream.getTracks()) {
      _peerConnection?.addTrack(track, stream);
    }
  }

  void _handleOffer(Map<String, dynamic> signal) {
    _pendingOffer = signal;
    final isVideo = signal['is_video'] == true;
    final callerName = signal['caller_name'] as String? ?? 'Unknown';

    value = value.copyWith(
      status: CallStatus.ringing,
      role: CallRole.callee,
      remoteUserId: signal['from'] as String?,
      remoteUserName: callerName,
      isVideoCall: isVideo,
    );
  }

  Future<void> _handleAnswer(Map<String, dynamic> signal) async {
    if (value.status != CallStatus.ringing) return;
    await _peerConnection!.setRemoteDescription(
      RTCSessionDescription(signal['sdp'] as String, 'answer'),
    );
    value = value.copyWith(status: CallStatus.inCall);
  }

  void _handleIceCandidate(Map<String, dynamic> signal) {
    final candidate = signal['candidate'] as Map<String, dynamic>?;
    if (candidate != null) {
      _peerConnection?.addCandidate(
        RTCIceCandidate(
          candidate['candidate'] as String? ?? '',
          candidate['sdpMid'] as String? ?? '',
          candidate['sdpMLineIndex'] as int? ?? 0,
        ),
      );
    }
  }

  void _handleHangUp(Map<String, dynamic> signal) {
    if (signal['userId'] == value.remoteUserId) {
      _cleanup();
      value = value.copyWith(status: CallStatus.hangUp);
    }
  }

  void _handleReject(Map<String, dynamic> signal) {
    if (signal['userId'] == value.remoteUserId) {
      _cleanup();
      value = value.copyWith(status: CallStatus.rejected);
    }
  }

  Future<bool> _checkTorch() async {
    try {
      return await value.localStream
              ?.getVideoTracks()
              .first
              .hasTorch() ??
          false;
    } catch (_) {
      return false;
    }
  }

  Future<void> _cleanup() async {
    await value.localStream?.dispose();
    value.localRenderer?.srcObject = null;
    await value.localRenderer?.dispose();
    value.remoteRenderer?.srcObject = null;
    await value.remoteRenderer?.dispose();
    await _peerConnection?.close();
    _peerConnection = null;
    _pendingOffer = null;
  }
}
