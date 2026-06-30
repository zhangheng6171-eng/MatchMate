# Tier 1 开源项目源码逆向分析报告

> 分析范围：Connectly / flutter_chat / WhatsApp_clone / LiveKit SDK
> 分析日期：2026-06-29
> 编码：UTF-8

---

## 一、Connectly（dating-platform-api）—— 后端核心

### 1.1 目录结构

```
dating-platform-api/
├── app/
│   ├── domain/                      # 纯业务逻辑层（零 I/O）
│   │   ├── entities/                # 数据类：UserEntity, SwipeEntity, BoundingBox, InboxSwipe, Photo
│   │   ├── interfaces/              # 端口接口：IUserRepository, ISwipeRepository, IDeckCache, ICandidateRepository
│   │   ├── exceptions/              # 领域异常：NoCandidatesFound, UserNotFoundById
│   │   └── services/                # 纯函数：haversine, bounding_box
│   │
│   ├── application/                 # 用例编排层
│   │   ├── use_cases/               # 业务场景：user, swipe, deck, photo, inbox, ai
│   │   └── services/                # 应用服务：DeckBuilder, GeoFilter, SwipeFilter, Inbox, AI
│   │
│   ├── infrastructure/              # 适配器层
│   │   ├── models/                  # SQLAlchemy ORM 模型
│   │   ├── repositories/            # PostgreSQL + Redis 实现
│   │   │   ├── caches/             # Redis 缓存（DeckCache, InboxCache）
│   │   │   └── *.py               # 各实体仓储实现
│   │   └── rate_limit/             # Redis 限流器
│   │
│   ├── api/v1/                      # FastAPI 路由 + DTO
│   └── core/                        # 配置 + DI 容器
│
├── bot/                             # Telegram Bot（aiogram v3）
├── alembic/                         # 数据库迁移
└── docker-compose.yml
```

### 1.2 核心流程分析

#### A. Deck 候选推荐引擎（deck.py use_case）

```
GetNextCandidateUseCase.next(user)
│
├── Redis LPOP("deck:{telegram_id}")
│   └── HIT → 返回候选
│
└── MISS → 重建 Deck
    ├── bounding_box(user.lat, user.lon, max_radius)
    ├── CandidateRepository.find_by_preferences_and_bbox(user, bbox)
    ├── SwipeFilterService.filter(user_id, candidates)  # 排除已滑动
    ├── GeoCandidateFilterService.filter(user, candidates)  # 距离过滤
    ├── DeckBuilderService.build(user, candidates)  # 写入 Redis
    └── Redis LPOP 再次尝试
```

**关键设计亮点**：
- 热路径 O(1) Redis LPOP
- 重建兜底机制（MISS → rebuild → LPOP again）
- 多级半径扩展（[5, 10, 15, 20] km）
- 随机打乱候选顺序（避免排序偏差）

#### B. Swipe 匹配流程（swipe.py use_case + service）

```
SwipeUserUseCase.execute(swipe)
│
├── _normalize_swipe(swipe)
│   └── 统一 user1_id < user2_id（避免重复记录）
│
├── SwipeRepository.get_by_ids(user1, user2)
│   ├── NULL → SwipeRepository.create(normalized)
│   └── EXISTS → SwipeRepository.update(existing, normalized)
│
└── IF swipe.decision == true:
    └── InboxOnSwipeService.create_inbox_item(swipe)
        └── 写入 Redis LIST（对方可查看谁喜欢了自己）
```

**关键设计亮点**：
- `_normalize_swipe` 确保 ID 排序一致性，避免同一对用户产生两条记录
- Inbox 侧效应异步触发（不阻塞 swipe 请求）

#### C. 地理过滤（geo_filter.py + bounding_box.py + haversine.py）

流程：
```
BoundingBox(lat, lon, radius) → {min_lat, max_lat, min_lon, max_lon}
    ↓ 用于 SQL WHERE 初步过滤
GeoCandidateFilterService.filter(user, candidates)
    ↓ 精确 Haversine 距离计算
    ↓ 多级 radius_steps 匹配
```

### 1.3 依赖关系

```
use_cases/
  ├── deck.py    → DeckBuilderService, GeoCandidateFilterService, SwipeFilterService
  │                 IDeckCache, ICandidateRepository, bounding_box (domain)
  ├── swipe.py   → ISwipeRepository, InboxOnSwipeService
  ├── user.py    → IUserRepository, IPhotoRepository, DeckBuilderService
  └── ai.py      → IAIClientRepository, AIProfileAnalyzer, AIMatchOpener

services/
  ├── deck.py         → IDeckCache, settings (配置)
  ├── geo_filter.py   → haversine (domain), settings
  ├── swipe_filter.py → ISwipeRepository
  └── inbox.py        → IInboxCache
```

### 1.4 适配风险点

| 风险 | 原因 | 适配方案 |
|------|------|---------|
| **telegram_id 作为主键** | 原项目基于 Telegram Bot | 替换为 UUID user_id |
| **Redis 缓存依赖** | Deck/Inbox 重度依赖 Redis | 保留，添加 Fallback 到 DB |
| **Clean Architecture 过度分层** | 小型项目可能过重 | 初期简化，按需扩展 |
| **AI 模型依赖** | OpenRouter API 调用 | 可选，独立模块 |
| **缺少音视频能力** | 纯文本/图片交友 | 需额外集成 WebRTC |

---

## 二、flutter_chat —— WebRTC 音视频通话

### 2.1 架构总览

```
lib/
├── blocs/
│   ├── call/              # 通话生命周期管理
│   │   ├── bloc.dart      # CallBloc（36 行）
│   │   ├── event.dart     # 6 种事件
│   │   └── state.dart     # 5 种状态
│   ├── web_rtc/           # WebRTC 媒体管理
│   │   ├── bloc.dart      # WebRTCBloc（86 行）
│   │   ├── event.dart     # 11 种事件
│   │   └── state.dart     # 完整状态模型
│   ├── chat/              # 文字聊天
│   └── socket/            # SignalR 信令
│
├── services/
│   ├── signalR/           # SignalR HubConnection
│   └── web_rtc/           # WebRTC PeerConnection
│
└── data/
    ├── models/             # WebRTCOffer, WebRTCAnswer, ICE
    └── repositories/       # CallRepository, SocketRepository, WebRTCRepository
```

### 2.2 通话状态机（CallBloc）

```
INITIAL → [ReadyForCallRequested] → READY_FOR_CALL
                                         │
                    ┌────────────────────┤
                    ▼                    ▼
               RINGING               HANG_UP
         (收到 WebRTCOffer)    (收到 CallEnded 事件)
                    │                    ▲
                    ▼                    │
        [CallAcceptRequested]    [EndCallRequested]
                    │                    │
                    ▼                    │
                IN_CALL ────────────────┘
```

### 2.3 WebRTC 握手流程（WebRTCBloc）

```
【发起方】                        【信令服务器】                     【接收方】
RequestCall(userId)                                          
  ├→ activateVideoRender()                                    
  ├→ requestCall()                      
  │   └── 创建 PeerConnection                                
  │   └── createOffer() ────────── WebRTCOffer ──────────→ WebRTCOfferReceived()
  │   └── 创建本地音频流                                     ├→ activateVideoRender()
  │                          ←── WebRTCAnswer ─────────────── answerCall()
  │                          ←── IceCandidate ─────────────── (多次)  
  │                                                          └→ IN_CALL
  │
  └→ RemoteVideoRenderActivated → callBloc.add(CallAcceptRequested)
```

### 2.4 完整的设备控制

| 事件 | 功能 | 实现 |
|------|------|------|
| `ToggleTorchRequested` | 手电筒开关 | `webRTCRepository.toggleTorch()` |
| `SwitchCameraRequested` | 前后摄像头切换 | `webRTCRepository.switchCamera()` + 手电筒重置 |
| `ToggleLocalVideoRenderActivationRequested` | 视频画面开关 | `webRTCRepository.toggleCameraActivation()` |
| `ToggleMicActivationRequested` | 麦克风静音 | `webRTCRepository.toggleMicActivation()` |
| `HangUpCallRequested` | 挂断 | 发送 HangUp 信令 → 通知 CallBloc → 释放资源 |

### 2.5 依赖项（pubspec.yaml 推测）

```yaml
dependencies:
  flutter_webrtc: ^0.9.x       # WebRTC Flutter 绑定
  flutter_bloc: ^8.x            # Bloc 状态管理
  signalr_netcore: ^1.x         # SignalR 客户端（信令）
  equatable: ^2.x               # 值对象比较
  freezed: ^2.x                 # 数据类（Builder 模式生成）
```

### 2.6 适配风险点

| 风险 | 原因 | 适配方案 |
|------|------|---------|
| **Bloc → Riverpod** | 原项目使用 `flutter_bloc`，我们使用 `riverpod` | 将 Bloc Events/States 映射为 Riverpod Notifier + State |
| **SignalR → WebSocket** | 信令使用 .NET SignalR | 替换为 FastAPI WebSocket（我们已有） |
| **WebRTCHangUp/Offer 数据模型** | 使用 freezed Builder 模式 | 改为 PODO 或 equatable |
| **flutter_webrtc 版本** | 需匹配 Flutter 3.x | 使用最新稳定版 `^0.10.x` |

---

## 三、WhatsApp_clone —— Riverpod 全场景聊天 UI

### 3.1 架构总览

```
lib/
├── main.dart                     # MaterialApp + GoRouter
├── router.dart                   # GoRouter 路由配置
├── mobile_chat_screen.dart       # 主页（TabBar: CHATS/STATUS/CALLS）
├── config/                       # 配置常量
├── models/                       # 消息/用户/群组模型
├── common/                       # 共享工具/颜色/Widget
└── feature/
    ├── auth/                     # 认证模块
    │   └── controller/           # Riverpod AuthController
    ├── chat/                     # 聊天模块
    │   ├── controller/           # Riverpod ChatController
    │   ├── repositories/         # 数据仓储
    │   ├── screens/              # 聊天页面
    │   └── widgets/              # 消息气泡/联系人列表
    ├── call/                     # 通话模块
    ├── group/                    # 群组模块
    ├── status/                   # 动态模块
    └── select_contacts/          # 联系人选择
```

### 3.2 Riverpod 模式示例

```dart
// Auth Controller (Provider)
final authControllerProvider = ChangeNotifierProvider((ref) {
  return AuthController(
    authRepository: ref.watch(authRepositoryProvider),
  );
});

// App 生命周期管理
@override
void didChangeAppLifecycleState(AppLifecycleState state) {
  switch (state) {
    case AppLifecycleState.resumed:
      ref.read(authControllerProvider).setUserState(true);
      break;
    case AppLifecycleState.paused:
      ref.read(authControllerProvider).setUserState(false);
      break;
  }
}
```

### 3.3 功能模块覆盖

| 功能 | WhatsApp_clone | 我们项目需求 | 适配价值 |
|------|:---:|:---:|:---:|
| 一对一文字聊天 | ✅ | ✅ | 🔴 高 |
| 群聊 | ✅ | ❌（非必需） | 🟡 中 |
| 语音通话 | ✅ | ✅ | 🔴 高 |
| 视频通话 | ✅ | ✅ | 🔴 高 |
| 图片/GIF/表情/文件 | ✅ | ✅ | 🟡 中 |
| 用户状态（在线/离线） | ✅ | ✅ | 🟡 中 |
| 故事（Status） | ✅ | ❌ | 🟢 低 |
| 已读/正在输入 | ✅ | ✅ | 🟡 中 |
| Firebase 后端 | ✅ | ❌（我们 FastAPI）| — |

### 3.4 适配风险点

| 风险 | 原因 | 适配方案 |
|------|------|---------|
| **Firebase → FastAPI** | 原项目深度依赖 Firebase Auth/Firestore/Storage | 替换为 Dio HTTP 客户端 + FastAPI REST |
| **Firebase 消息推送** | FCM 推送 | 保留 FCM 或替换为自建推送 |
| **Agora 视频通话** | 部分项目用 Agora（收费） | 替换为 WebRTC（自建或 LiveKit） |
| **未标注许可证** | WhatsApp_clone 无 LICENSE | 仅参考架构和 UI 模式，不直接复制代码 |

---

## 四、LiveKit client-sdk-flutter —— 生产级 WebRTC 基础设施

### 4.1 架构

```
LiveKit Server (SFU)  ←→  LiveKit Flutter SDK
     │                          │
     ├── Room 管理               ├── connect(url, token)
     ├── Participant 管理         ├── createLocalVideoTrack()
     ├── Track 发布/订阅          ├── createLocalAudioTrack()
     └── 信令 + 媒体转发           └── room.remoteParticipants[0]
                                     .videoTrackPublications
```

### 4.2 关键 API

```dart
// 1. 连接房间
final room = Room();
await room.connect(
  'wss://your-livekit-server.com',
  token,  // JWT 鉴权
);

// 2. 发布本地音视频
final localVideo = await LocalVideoTrack.create();
final localAudio = await LocalAudioTrack.create();
await room.localParticipant!.publishTrack(localVideo);
await room.localParticipant!.publishTrack(localAudio);

// 3. 监听远端参与者
room.events.on<ParticipantConnected>((event) {
  // 新参与者加入
});
room.events.on<TrackSubscribed>((event) {
  // 收到远端音视频轨
  if (event.track.kind == TrackType.video) {
    // 渲染视频
  }
});
```

### 4.3 WebRTC 实现方案对比

| 维度 | 自建 WebRTC | LiveKit |
|------|:---:|:---:|
| 开发工作量 | 🔴 高（需实现信令服务） | 🟢 低（SDK 封装好） |
| 多人通话 | 🟡 需实现 Mesh/SFU | ✅ 原生 SFU 支持 |
| 运营成本 | 免费 | 免费（自托管）/ 付费（Cloud） |
| 维护成本 | 自行维护 | 社区维护（402⭐） |
| 质量保障 | 自己保证 | 生产验证 |
| 许可证 | — | Apache 2.0 |

---

## 五、综合适配方案

### 5.1 后端适配（Connectly → 当前项目）

参考 [project_comparison_report.md](file:///e:/traeguojiban/workplace1app/project_comparison_report.md) 的组合策略。

### 5.2 前端适配（flutter_chat + WhatsApp_clone → Riverpod）

**Bloc → Riverpod 映射表**：

| Bloc 概念 | Riverpod 等价 |
|-----------|--------------|
| `Bloc<Event, State>` | `StateNotifier<State>` / `AsyncNotifier<State>` |
| `add(Event)` | 直接调用 Notifier 方法 |
| `mapEventToState()` | Notifier 方法内更新 state |
| `state.copyWith(...)` | 同 `state.copyWith(...)` |
| `close()` | `ref.onDispose()` |
| `BlocProvider` | `StateNotifierProvider` / `NotifierProvider` |

### 5.3 适配文件清单

- ✅ `backend/app/domain/services/compatibility.py` — 已存在（MIIRA 适配）
- ✅ `backend/app/domain/services/haversine.py` — 已存在（Connectly 适配）
- ✅ `backend/app/api/websocket.py` — 已存在（flutter-fastapi-chat 适配）
- 新增：`backend/app/application/use_cases/swipe.py` — Connectly swipe 适配
- 新增：`backend/app/application/use_cases/deck.py` — Connectly deck 适配
- 新增：`backend/app/domain/entities/swipe.py` — 领域实体
- 新增：`lib/feature/call/` — WebRTC 通话模块（flutter_chat Bloc → Riverpod）
- 新增：`lib/feature/chat/` — 文字聊天模块（WhatsApp_clone 参考）
- 新增：`lib/services/call/` — LiveKit 语音/视频通话服务（可选）
