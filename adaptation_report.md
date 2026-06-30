# Tier 1 项目源码适配改造说明

> 适配范围：Connectly / flutter_chat / WhatsApp_clone / LiveKit SDK
> 适配日期：2026-06-29
> 编码：UTF-8

---

## 一、改造范围总览

| 层次 | 来源项目 | 原始实现 | → | 当前项目适配 |
|------|---------|---------|---|-------------|
| 后端 | Connectly | SwipeBloc + UseCase | → | `backend/app/application/use_cases/swipe.py` |
| 后端 | Connectly | DeckBuilder + UseCase | → | `backend/app/application/use_cases/deck.py` |
| 后端 | Connectly | Domain Entities (Swipe) | → | `backend/app/domain/entities/swipe.py` |
| 前端 | flutter_chat | CallBloc + WebRTCBloc (Bloc) | → | `lib/feature/call/call_notifier.dart` (Riverpod) |
| 前端 | flutter_chat | Call Page UI | → | `lib/feature/call/call_page.dart` |
| 前端 | LiveKit | client-sdk-flutter API | → | `lib/services/call/livekit_service.dart` |

---

## 二、修改清单

### 2.1 后端文件（Python）

| # | 文件 | 原始来源 | 关键变更 | 状态 |
|---|------|---------|---------|:---:|
| 1 | `app/domain/services/compatibility.py` | MIIRA-matchmaking (JS → Python) | 翻译 + 类型注解 | ✅ |
| 2 | `app/domain/services/haversine.py` | Connecty | 结构相同，独立实现 | ✅ |
| 3 | `app/domain/entities/swipe.py` | Connecty `domain/entities/swipe.py` | telegram_id→UUID, 新增 swipe_type | ✅ |
| 4 | `app/application/use_cases/swipe.py` | Connecty `use_cases/swipe.py` | 观察者替代 InboxService, 新增双向匹配检测 | ✅ |
| 5 | `app/application/use_cases/deck.py` | Connecty `use_cases/deck.py` | 新增兼容性排序, 缓存可选, telegram_id→UUID | ✅ |
| 6 | `app/api/websocket.py` | flutter-fastapi-websocket-chat | JSON协议, 私聊支持, JWT认证接口 | ✅ |

### 2.2 前端文件（Dart）

| # | 文件 | 原始来源 | 关键变更 | 状态 |
|---|------|---------|---------|:---:|
| 7 | `lib/services/websocket_service.dart` | flutter-fastapi-websocket-chat | JSON协议, 重连机制, Stream API | ✅ |
| 8 | `lib/feature/call/call_notifier.dart` | flutter_chat `call/bloc.dart` + `web_rtc/bloc.dart` | Bloc→Riverpod, 合并双Bloc, SignalR→WebSocket | ✅ |
| 9 | `lib/feature/call/call_page.dart` | flutter_chat `presentation/` | 基于 CallNotifier 状态驱动的通话UI | ✅ |
| 10 | `lib/services/call/livekit_service.dart` | LiveKit `client-sdk-flutter` | 封装为独立服务, 提供统一接口 | ✅ |

---

## 三、适配风险点及解决方案

### 3.1 后端适配

| 风险 | 影响 | 解决方案 | 状态 |
|------|------|---------|:---:|
| `telegram_id` → `UUID` | 主键类型不一致 | 全部统一为 Python `uuid.UUID` | ✅ |
| Redis 硬依赖 | 无 Redis 环境无法运行 | Deck 缓存改为可选，无 Redis 走纯 DB 模式 | ✅ |
| InboxService 紧耦合 | 收件箱与 Swipe 强绑定 | 改为观察者模式（observer pattern） | ✅ |
| AI 服务未安装 | `ai.py` 用例无法运行 | 独立模块，不影响核心功能 | ⚠️ 延后 |
| 数据库迁移（Alembic） | 新实体无迁移脚本 | 需后续创建，当前为 dataclass 定义 | ⚠️ 延后 |

### 3.2 前端适配

| 风险 | 影响 | 解决方案 | 状态 |
|------|------|---------|:---:|
| `flutter_bloc` → `riverpod` | 状态管理不兼容 | 全部重写为 ValueNotifier + Riverpod 模式 | ✅ |
| SignalR → WebSocket | 信令协议不同 | 统一为 JSON WebSocket 信令 | ✅ |
| `flutter_webrtc` 未安装 | 编译错误 | 需 `flutter pub add flutter_webrtc` | ⚠️ 待安装 |
| `livekit_client` 未安装 | 编译错误 | 需 `flutter pub add livekit_client` | ⚠️ 待安装 |
| RTCVideoView 引用 | Widget 依赖 flutter_webrtc | 已 import，需安装包后编译 | ⚠️ 待安装 |

---

## 四、集成步骤

### 4.1 后端集成

```bash
# 1. 确认目录结构
backend/app/
├── domain/
│   ├── entities/
│   │   ├── swipe.py      # ✅ 新增
│   └── services/
│       ├── compatibility.py  # ✅ 已有
│       └── haversine.py      # ✅ 已有
├── application/
│   └── use_cases/
│       ├── swipe.py       # ✅ 新增
│       └── deck.py        # ✅ 新增
└── api/
    └── websocket.py       # ✅ 已有

# 2. 安装依赖
pip install fastapi uvicorn sqlalchemy alembic redis

# 3. 创建接口路由（在 main.py 中注册）
# from app.application.use_cases.swipe import SwipeUserUseCase
# from app.application.use_cases.deck import UserDeckUseCase

# 4. 数据库迁移（后续创建 Alembic 迁移文件）
# alembic revision --autogenerate -m "add swipe entities"
# alembic upgrade head
```

### 4.2 前端集成

```bash
# 1. 安装依赖
flutter pub add flutter_webrtc       # WebRTC 核心
flutter pub add riverpod             # 状态管理
flutter pub add go_router            # 路由
flutter pub add equatable            # 值对象比较

# 可选（替代自建 WebRTC）：
# flutter pub add livekit_client     # LiveKit SFU

# 2. 确认目录结构
lib/
├── feature/
│   └── call/
│       ├── call_notifier.dart  # ✅ 新增
│       └── call_page.dart      # ✅ 新增
├── services/
│   ├── websocket_service.dart  # ✅ 已有
│   └── call/
│       └── livekit_service.dart  # ✅ 新增

# 3. 注册路由（router.dart）
# GoRoute(
#   path: '/call/:userId',
#   builder: (context, state) => CallPage(
#     callNotifier: ...,  // 从 Provider 获取
#   ),
# ),

# 4. WebSocket 信令集成
# 将 CallNotifier 的 _onSendSignal 连接到 websocket_service.sendMessage()
```

---

## 五、测试验证方案

### 5.1 后端单元测试

```python
# tests/test_swipe.py
import pytest
from app.application.use_cases.swipe import SwipeUserUseCase

@pytest.mark.asyncio
async def test_swipe_normalization():
    """验证滑动标准化（user1_id < user2_id）"""
    # 待实现

@pytest.mark.asyncio
async def test_mutual_match_detection():
    """验证双向匹配检测"""
    # 待实现

# tests/test_compatibility.py
def test_compatibility_score_range():
    """验证兼容性评分在 0-100 范围"""
    from app.domain.services.compatibility import calculate_compatibility
    score = calculate_compatibility({"interests": ["a"]}, {"interests": ["a"]})
    assert 0 <= score <= 100

def test_no_overlap_returns_low_score():
    """验证无重叠时返回低分"""
    score = calculate_compatibility(
        {"interests": ["a"], "values": ["x"]},
        {"interests": ["b"], "values": ["y"]},
    )
    assert score < 30
```

### 5.2 前端组件测试

```dart
// test/call_notifier_test.dart
void main() {
  test('CallNotifier initial state is idle', () {
    final notifier = CallNotifier(
      currentUserId: 'user_123',
      onSendSignal: (userId, signal) {},
    );
    expect(notifier.value.status, CallStatus.idle);
  });

  test('HangUp transitions to hangUp state', () async {
    final notifier = CallNotifier(
      currentUserId: 'user_123',
      onSendSignal: (userId, signal) {},
    );
    notifier.value = notifier.value.copyWith(status: CallStatus.inCall);
    await notifier.hangUp();
    expect(notifier.value.status, CallStatus.hangUp);
  });
}

### 5.3 集成测试场景

| 场景 | 步骤 | 预期结果 |
|------|------|---------|
| 视频通话发起 | 用户A点击拨打 → 用户B收到振铃 | B 端 status=ringing, role=callee |
| 视频通话接听 | 用户B点击接听 | 双方 status=inCall, 建立 WebRTC 连接 |
| 麦克风静音 | 通话中点麦克风按钮 | isMicOn 翻转，对方听不到 |
| 摄像头切换 | 通话中点翻转摄像头 | isFrontCamera 翻转，手电筒重置 |
| 挂断通话 | 任意一方点挂断 | 双方 status=hangUp, 释放资源 |
| 滑动匹配 | A右滑B, B也右滑A | is_match=true, 创建 Match 记录 |
| Deck 推荐 | 请求下一个候选 | 返回按兼容性排序的候选，排除已滑动用户 |

---

## 六、待安装依赖清单

### 后端 Python

```
fastapi>=0.110.0
uvicorn>=0.29.0
sqlalchemy[asyncio]>=2.0.0
alembic>=1.13.0
asyncpg>=0.29.0        # PostgreSQL 异步驱动
redis>=5.0.0            # Redis 客户端（可选）
python-jose>=3.3.0      # JWT
pydantic>=2.0.0
```

### 前端 Flutter

```yaml
dependencies:
  flutter_webrtc: ^0.10.0       # 🔴 必需：WebRTC
  riverpod: ^2.5.0              # 🔴 必需：状态管理
  go_router: ^14.0.0            # 🔴 必需：路由
  dio: ^5.4.0                   # 🔴 必需：HTTP 客户端
  equatable: ^2.0.0             # 🟡 推荐：值对象
  web_socket_channel: ^2.4.0    # 🟡 推荐：WebSocket 客户端
  livekit_client: ^2.0.0        # 🟢 可选：LiveKit（替代自建 WebRTC）
  freezed: ^2.5.0               # 🟢 可选：数据类生成
  freezed_annotation: ^2.4.0    # 🟢 可选：数据类注解
```

---

## 七、变更影响范围

```
当前项目文件结构：
workplace1app/
├── backend/
│   └── app/
│       ├── domain/
│       │   ├── entities/
│       │   │   └── swipe.py          ← 🆕 新增
│       │   └── services/
│       │       ├── compatibility.py   ← ✅ 已有（不变）
│       │       └── haversine.py       ← ✅ 已有（不变）
│       ├── application/
│       │   └── use_cases/
│       │       ├── swipe.py           ← 🆕 新增
│       │       └── deck.py            ← 🆕 新增
│       └── api/
│           └── websocket.py           ← ✅ 已有
├── lib/
│   ├── feature/
│   │   └── call/
│   │       ├── call_notifier.dart     ← 🆕 新增
│   │       └── call_page.dart         ← 🆕 新增
│   └── services/
│       ├── websocket_service.dart     ← ✅ 已有
│       └── call/
│           └── livekit_service.dart   ← 🆕 新增
├── tier1_source_analysis.md           ← 🆕 新增
├── project_comparison_report.md       ← ✅ 已有
├── agent_config.md                    ← ✅ 已有
├── agents_overview.md                 ← ✅ 已有
├── mcp_config.md                      ← ✅ 已有
├── project_workflow.md                ← ✅ 已有
└── research_report.md                 ← ✅ 已有
```

> 说明：所有新增/修改的文件均不影响原有 `app/domain/services/compatibility.py`、`app/domain/services/haversine.py`、`app/api/websocket.py`、`lib/services/websocket_service.dart` 的功能逻辑。

---

## 八、Bloc → Riverpod 迁移对照表

| flutter_chat (Bloc) | → | 当前项目 (Riverpod) |
|---------------------|---|--------------------|
| `CallBloc` + `WebRTCBloc` | → | `CallNotifier` (合并) |
| `BlocProvider<CallBloc>` | → | `StateNotifierProvider<CallNotifier, CallState>` |
| `bloc.add(RequestCall(...))` | → | `callNotifier.startVideoCall(...)` |
| `bloc.add(AnswerCallRequested())` | → | `callNotifier.acceptCall()` |
| `bloc.add(HangUpCallRequested(...))` | → | `callNotifier.hangUp()` |
| `BlocBuilder<WebRTCBloc, WebRTCState>` | → | `ValueListenableBuilder<CallState>` |
| `state.copyWith(status: ...)` | → | 相同（保留） |
| `mapEventToState()` | → | Notifier 内部方法 + `value = value.copyWith(...)` |
| `close()` | → | `disposeResources()` + `ref.onDispose()` |

---

> 生成时间：2026-06-29 | 编码：UTF-8
