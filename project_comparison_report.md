# 候选开源项目对比分析报告

> 项目需求：相亲 App（Flutter + FastAPI），需支持**文字 + 语音 + 视频**全场景聊天
> 分析日期：2026-06-29
> 数据来源：GitHub MCP（mcp_GitHub）+ WebSearch 交叉验证

---

## 一、当前参考项目评分

### helloharendra/Complete-Dating-App（SparkMatch）

| 指标 | 评分 | 数据 |
|------|------|------|
| **Star 数** | ⭐ (1/5) | 2 stars |
| **Fork 数** | ⭐ (1/5) | 0 forks |
| **社区活跃度** | ⭐ (1/5) | 11 commits，2025年4月创建，2025年5月最后更新 → **已停止维护** |
| **代码质量** | ⭐⭐⭐ (3/5) | Clean Architecture 分层（core/data/domain/presentation），结构清晰 |
| **功能完整性** | ⭐⭐ (2/5) | 有 auth/admin/discover/match/message/profile，但均为基础实现 |
| **语音通话** | ❌ | **不支持** |
| **视频通话** | ❌ | **不支持** |
| **后端匹配度** | ⭐⭐ (2/5) | 声称 FastAPI + PostgreSQL，但仓库中无后端代码（仅 Flutter 前端） |
| **技术栈先进性** | ⭐⭐ (2/5) | Provider（非 Riverpod），pubspec 依赖极少 |
| **许可证** | ✅ | MIT |

**综合评价：D 级 —— 不适合作为主力参考项目**

> SparkMatch 是一个纯 Flutter 前端的展示项目（无后端代码），仅支持文字聊天，无语音/视频通话能力，且已停止维护。**无法满足你的全场景聊天需求。**

---

## 二、候选项目总览

经过 GitHub MCP + WebSearch 多轮检索，筛选出以下 8 个候选项目：

| # | 项目 | Stars | 技术栈 | 许可证 | 推荐优先级 |
|---|------|-------|--------|--------|-----------|
| 1 | **aliyazdi75/flutter_chat** | — | Flutter + SignalR + WebRTC | MIT | 🔴 Tier 1 |
| 2 | **akashmishra242/WhatsApp_clone** | — | Flutter + Riverpod 2.0 | 未标注 | 🔴 Tier 1 |
| 3 | **AhmedAbdoElhawary/flutter-clean-architecture-instagram** | — | Flutter + Firebase + Agora | 未标注 | 🟡 Tier 2 |
| 4 | **RodrigoBertotti/flutter_group_chat_app_with_firebase** | — | Flutter + Firebase + Agora | 未标注 | 🟡 Tier 2 |
| 5 | **shahshubh/Chatify** | — | Flutter + Firebase + Agora | 未标注 | 🟢 Tier 3 |
| 6 | **HeavenOSK/flutter_swipable_stack** | — | Flutter 组件库 | 未标注 | 🟢 Tier 3 |
| 7 | **livekit/client-sdk-flutter** | **402** | Flutter + WebRTC SFU | Apache 2.0 | 🔴 Tier 1 |
| 8 | **Connectly (dating-platform-api)** | — | FastAPI + PostgreSQL + Redis | MIT | 🔴 Tier 1 |

---

## 三、全场景聊天覆盖度对比（核心）

| 功能 | SparkMatch | flutter_chat | WhatsApp_clone | Instagram Clone | Group Chat | Chatify | LiveKit |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **文字聊天** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **语音通话** | ❌ | ✅ WebRTC | ✅ | ❌ | ❌ | ❌ | ✅ SFU |
| **视频通话** | ❌ | ✅ WebRTC | ✅ | ✅ Agora | ✅ Agora | ✅ Agora | ✅ SFU |
| **群聊** | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |
| **图片/文件** | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **消息推送** | ❌ | ❌ | ❌ | ❌ | ✅ FCM | ❌ | ❌ |
| **已读/正在输入** | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |

---

## 四、逐项详细分析

### 1. aliyazdi75/flutter_chat —— 🔴 全场景聊天最佳方案

| 维度 | 评分 | 说明 |
|------|------|------|
| 聊天功能 | ⭐⭐⭐⭐⭐ | **文字 + 语音 + 视频**，SignalR 信令 + WebRTC 媒体 |
| 架构 | ⭐⭐⭐⭐ | Bloc 状态管理，Call Bloc 专门处理通话状态 |
| WebRTC 集成 | ⭐⭐⭐⭐⭐ | Offer/Answer/Candidate/HangUp/Reject 完整握手 |
| 设备能力 | ⭐⭐⭐⭐ | 摄像头切换、麦克风/摄像头开关、手电筒控制 |
| 代码质量 | ⭐⭐⭐⭐ | Bloc Events/States 分离清晰 |
| 维护状态 | ⭐⭐ | 2021年最后更新，52 commits |
| 缺点 | — | 不是约会应用，需要自行集成匹配系统 |

**核心价值**：提供了完整的 WebRTC 音视频通话实现，包括信令、媒体协商、设备控制。可直接借鉴其 Bloc 层代码。

---

### 2. akashmishra242/WhatsApp_clone —— 🔴 Flutter 全功能聊天标杆

| 维度 | 评分 | 说明 |
|------|------|------|
| 聊天功能 | ⭐⭐⭐⭐⭐ | **文字 + 语音 + 视频 + 图片/GIF/表情/文件** |
| 技术栈 | ⭐⭐⭐⭐⭐ | **Riverpod 2.0**（与你选型一致）+ GoRouter |
| 群聊 | ✅ | 群聊支持 |
| 状态管理 | ⭐⭐⭐⭐⭐ | Riverpod 最佳实践 |
| 维护状态 | ⭐⭐ | 2023年最后更新 |
| 缺点 | — | 不包含约会匹配逻辑，后端非 FastAPI |

**核心价值**：与你的 Riverpod 技术选型完全一致，提供了文字/语音/视频/文件全场景聊天的 Flutter 实现参考。

---

### 3. AhmedAbdoElhawary/flutter-clean-architecture-instagram —— 🟡 Clean Architecture 参考

| 维度 | 评分 | 说明 |
|------|------|------|
| 架构 | ⭐⭐⭐⭐⭐ | 完整 Clean Architecture（data/domain/presentation） |
| 视频通话 | ✅ | Agora SDK 集成 |
| 社交功能 | ⭐⭐⭐⭐⭐ | 发帖/故事/点赞/评论/关注/搜索 |
| 维护状态 | ⭐⭐⭐⭐ | 2026年2月仍在更新 |
| 缺点 | — | Instagram 非约会，无匹配系统；后端 Firebase 非 FastAPI |

---

### 4. RodrigoBertotti/flutter_group_chat_app_with_firebase —— 🟡 群聊视频通话

| 维度 | 评分 | 说明 |
|------|------|------|
| 视频通话 | ✅ | Agora + 数字 UID 互斥锁 |
| 群聊管理 | ✅ | 群组创建/管理 |
| 推送通知 | ✅ | FCM 前后台通知 |
| 打字指示器 | ✅ | 正在输入状态 |
| 消息状态 | ✅ | 已收到/已读状态 |
| 维护状态 | ⭐⭐⭐ | 2025年3月更新 |

---

### 5. LiveKit client-sdk-flutter —— 🔴 生产级 WebRTC 基础设施

| 维度 | 评分 | 说明 |
|------|------|------|
| Stars | **402** | ⭐⭐⭐⭐⭐ 社区认可度最高 |
| 协议 | Apache 2.0 | 商业友好 |
| 功能 | SFU 架构 | 支持多人音视频会议 |
| 维护 | 活跃 | 2026年6月仍在更新 |
| 跨平台 | iOS/Android/Web/Desktop | 全覆盖 |

**核心价值**：如果你不想自己搭建 WebRTC 信令服务器，可以直接用 LiveKit 作为音视频通话基础设施。**这是开源社区中生产级 WebRTC Flutter SDK 的首选。**

---

### 6. Connectly (dating-platform-api) —— 🔴 后端最佳参考

| 维度 | 评分 | 说明 |
|------|------|------|
| 技术栈匹配 | ⭐⭐⭐⭐⭐ | FastAPI + PostgreSQL + Redis + SQLAlchemy 2 + Alembic |
| 架构 | ⭐⭐⭐⭐⭐ | Clean Architecture（domain/application/infrastructure/api） |
| 约会功能 | ⭐⭐⭐⭐ | Deck推荐引擎 + Swipe + Inbox + 地理过滤 |
| 测试 | ⭐⭐⭐⭐ | pytest + pytest-asyncio |
| 维护 | ⭐⭐⭐⭐ | 259 commits, MIT license |
| 缺点 | — | 无音视频聊天（只有 AI 辅助功能）；无 Flutter 前端 |

---

## 五、综合推荐方案

基于你的需求（文字 + 语音 + 视频全场景聊天），推荐采用**组合参考策略**：

```
┌─────────────────────────────────────────────────────────┐
│                   后端：FastAPI                           │
│                                                         │
│  参考 Connectly（MIT）                                    │
│  ├─ Clean Architecture 骨架                               │
│  ├─ Deck 推荐引擎 + Swipe 系统                            │
│  ├─ 兼容性匹配算法（改编自 MIIRA）                          │
│  └─ Haversine 地理距离计算                                │
│                                                         │
│  自建：WebRTC 信令服务（FastAPI WebSocket）                │
│  参考 flutter_chat 的 SignalR ↔ WebRTC 信令模式           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                 前端：Flutter                             │
│                                                         │
│  参考 WhatsApp_clone（Riverpod 2.0）                      │
│  ├─ 文字聊天 UI + 已读/正在输入状态                         │
│  ├─ 语音/视频通话 UI                                      │
│  └─ 图片/文件/GIF 消息                                    │
│                                                         │
│  参考 flutter_chat（WebRTC Bloc）                         │
│  ├─ Call Bloc 通话状态管理                                │
│  ├─ Offer/Answer/Candidate 信令                          │
│  └─ 摄像头/麦克风设备控制                                  │
│                                                         │
│  参考 LiveKit SDK（可选替代方案）                           │
│  └─ 生产级 SFU 音视频通话                                  │
│                                                         │
│  参考 SparkMatch（约会 UI）                               │
│  ├─ 卡片滑动匹配 UI                                       │
│  └─ 个人资料页面布局                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 六、关键决策建议

| 决策项 | 推荐方案 | 理由 |
|--------|---------|------|
| 文字聊天 | **FastAPI WebSocket（自建）** | 已创建基础代码，MateChat 架构可快速扩展 |
| 语音/视频通话 | **LiveKit SDK（推荐）** OR 自建 WebRTC | LiveKit = 402 stars + 生产级 + 维护活跃；自建 = 完全可控但工作量大 |
| 状态管理 | **Riverpod 2.x** | 与规划一致，WhatsApp_clone 提供最佳实践参考 |
| 后端架构 | **Connectly Clean Architecture** | MIT 许可，FastAPI + PostgreSQL + Redis 与规划完全一致 |
| 匹配算法 | **MIIRA 四维度算法 → Python** | 已验证的 100 分制兼容性评分模型 |

---

## 七、SparkMatch 不能作为主参考的原因总结

1. **仅 2 stars / 0 forks**，社区认可度极低
2. **11 commits，已停止维护**（2025年5月后无更新）
3. **仓库中没有后端代码**，声称 FastAPI 但未发布
4. **不支持语音/视频通话**，仅基础文字聊天
5. **使用 Provider**，与你的 Riverpod 规划不匹配
6. **pubspec 依赖极少**（仅 provider + font_awesome），功能覆盖严重不足

**结论**：SparkMatch 可作为 Flutter 约会 UI 的轻量参考，但**绝不能作为主力技术方案。**
