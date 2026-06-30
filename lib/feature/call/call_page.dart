
"""
通话页面 Widget
来源：参考 flutter_chat presentation 层 UI + WhatsApp_clone call 页设计
适配：基于 CallNotifier（Riverpod）状态驱动
"""
import 'package:flutter/material.dart';
import 'call_notifier.dart';

/// 通话页面
///
/// 支持语音/视频通话，包含：
/// - 远程视频渲染（视频通话）
/// - 本地小窗预览
/// - 麦克风开关
/// - 摄像头开关（视频通话）
/// - 前后摄像头切换
/// - 扬声器切换
/// - 挂断按钮
class CallPage extends StatefulWidget {
  final CallNotifier callNotifier;

  const CallPage({
    super.key,
    required this.callNotifier,
  });

  @override
  State<CallPage> createState() => _CallPageState();
}

class _CallPageState extends State<CallPage> {
  @override
  void dispose() {
    // 不在此处 dispose callNotifier（由 Provider 管理）
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<CallState>(
      valueListenable: widget.callNotifier,
      builder: (context, state, _) {
        return Scaffold(
          backgroundColor: Colors.black,
          body: Stack(
            children: [
              // --- 远程视频（全屏背景）---
              if (state.isVideoCall && state.remoteRenderer != null)
                Positioned.fill(
                  child: RTCVideoView(state.remoteRenderer!),
                )
              else
                const Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.person, size: 80, color: Colors.white54),
                      SizedBox(height: 16),
                      Text(
                        '语音通话中...',
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 18,
                        ),
                      ),
                    ],
                  ),
                ),

              // --- 顶部：对方信息和通话时长 ---
              Positioned(
                top: 60,
                left: 0,
                right: 0,
                child: Column(
                  children: [
                    Text(
                      state.remoteUserName ?? '未知用户',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    _buildStatusText(state),
                  ],
                ),
              ),

              // --- 本地视频小窗（右下角）---
              if (state.isVideoCall &&
                  state.isCameraOn &&
                  state.localRenderer != null)
                Positioned(
                  right: 16,
                  top: 100,
                  child: GestureDetector(
                    onTap: () => widget.callNotifier.switchCamera(),
                    child: Container(
                      width: 120,
                      height: 170,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: Colors.white.withValues(alpha: 0.3),
                          width: 1,
                        ),
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(11),
                        child: RTCVideoView(
                          state.localRenderer!,
                          mirror: state.isFrontCamera,
                        ),
                      ),
                    ),
                  ),
                ),

              // --- 底部：控制按钮区 ---
              Positioned(
                bottom: 40,
                left: 0,
                right: 0,
                child: _buildControlBar(state),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildStatusText(CallState state) {
    String text;
    switch (state.status) {
      case CallStatus.ringing:
        text = state.role == CallRole.caller ? '等待对方接听...' : '来电...';
        break;
      case CallStatus.handshaking:
        text = '连接中...';
        break;
      case CallStatus.inCall:
        text = '通话中';
        break;
      case CallStatus.hangUp:
        text = '通话已结束';
        break;
      case CallStatus.rejected:
        text = '对方忙线中';
        break;
      default:
        text = '';
    }
    return Text(
      text,
      style: const TextStyle(color: Colors.white60, fontSize: 14),
    );
  }

  Widget _buildControlBar(CallState state) {
    final isCallActive = state.status == CallStatus.inCall ||
        state.status == CallStatus.ringing;
    final isVideo = state.isVideoCall;

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        // 挂断按钮
        _ControlButton(
          icon: Icons.call_end,
          color: Colors.red,
          size: 64,
          onTap: () {
            widget.callNotifier.hangUp();
            Navigator.of(context).pop();
          },
        ),

        // 麦克风（通话中可见）
        if (isCallActive)
          _ControlButton(
            icon: state.isMicOn ? Icons.mic : Icons.mic_off,
            color: state.isMicOn ? Colors.white38 : Colors.white,
            size: 48,
            onTap: () => widget.callNotifier.toggleMic(),
          ),

        // 摄像头（视频通话中可见）
        if (isCallActive && isVideo)
          _ControlButton(
            icon: state.isCameraOn
                ? Icons.videocam
                : Icons.videocam_off,
            color: state.isCameraOn ? Colors.white38 : Colors.white,
            size: 48,
            onTap: () => widget.callNotifier.toggleCamera(),
          ),

        // 切换摄像头
        if (isCallActive && isVideo)
          _ControlButton(
            icon: Icons.flip_camera_android,
            color: Colors.white38,
            size: 48,
            onTap: () => widget.callNotifier.switchCamera(),
          ),
      ],
    );
  }
}

class _ControlButton extends StatelessWidget {
  final IconData icon;
  final Color color;
  final double size;
  final VoidCallback onTap;

  const _ControlButton({
    required this.icon,
    required this.color,
    required this.size,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: color.withValues(alpha: color == Colors.red ? 1.0 : 0.3),
        ),
        child: Icon(
          icon,
          color: color == Colors.white38 ? Colors.white : Colors.white,
          size: size * 0.4,
        ),
      ),
    );
  }
}
