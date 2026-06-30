# 开源项目调研报告

> 项目：相亲 App（Flutter + FastAPI）
> 调研时间：2026-06-29
> 调研方式：WebSearch + WebFetch（GitHub MCP 未安装，使用替代方案）

---

## 调研项目总览

| # | 项目 | Stars | 许可证 | 技术栈匹配度 | 推荐优先级 |
|---|------|-------|--------|------------|-----------|
| 1 | **Connectly (dating-platform-api)** | — | MIT | ⭐⭐⭐⭐⭐ | 🔴 最高 |
| 2 | **MIIRA-matchmaking** | — | 未标注 | ⭐⭐⭐⭐ | 🔴 最高 |
| 3 | **flutter-fastapi-websocket-chat** | — | MIT | ⭐⭐⭐⭐⭐ | 🟡 高 |
| 4 | **Card Swipper (Umaiir11)** | — | 未标注 | ⭐⭐⭐ | 🟡 高 |
| 5 | **2connectv1-ai** | — | 未标注 | ⭐⭐⭐⭐ | 🟢 中 |

---

## 1. Connectly (dating-platform-api)

- **仓库**：[Maksim-Volosh/dating-platform-api](https://github.com/Maksim-Volosh/dating-platform-api)
- **许可证**：MIT
- **259 次提交**

### 技术栈
| 层 | 技术 |
|---|------|
| 后端 | FastAPI + Python 3.12 |
| 数据库 | PostgreSQL + SQLAlchemy 2 (async) + Alembic |
| 缓存 | Redis |
| 容器化 | Docker + Docker Compose |
| 测试 | pytest + pytest-asyncio |
| AI | OpenRouter / OpenAI-compatible |

### 架构亮点（Clean Architecture）
```
domain/        → 纯业务逻辑（实体、接口、领域服务）
application/   → 用例编排层（use cases）
infrastructure/ → I/O适配器（SQLAlchemy仓储、Redis缓存）
api/           → FastAPI路由 + 依赖注入
```

### 核心可借鉴内容

#### A. Deck 候选推荐引擎
```
POST /api/v1/users → 注册后立即构建候选队列
↓ DeckBuilderService.build_for_user
  → bounding_box(user_location, radius_steps)
  → CandidateRepository.find_by_preferences_and_bbox
  → SwipeFilterService.filter（排除已滑动用户）
  → GeoCandidateFilterService.filter（距离/半径规则）
  → DeckCache.save(Redis LIST + TTL)
```

**关键设计**：
- 热路径 O(1) Redis `LPOP`，缓存未命中时再重建
- 支持多级半径扩展（[5, 10, 15, 20] km）
- 候选去重：已滑过的用户不会再次出现

#### B. Haversine 距离计算（领域服务）
```python
def haversine(lat1, lon1, lat2, lon2) -> float:
    """纯函数，无I/O依赖，放在 domain/services/"""
    ...
```

#### C. AI 辅助功能
- AI 个人资料分析
- AI 匹配开场白生成
- Redis 限流保护

### 适配建议
以上全部 Clean Architecture 分层思想可直接套用到本项目。详见生成的代码文件。

---

## 2. MIIRA-matchmaking

- **仓库**：[RZSayyad/MIIRA-matchmaking](https://github.com/RZSayyad/MIIRA-matchmaking)
- **154 次提交**
- **技术栈**：Flutter + Node.js/Express + MongoDB + Socket.IO

### 核心可借鉴内容

#### A. 兼容性匹配算法（compatibilityService.js）
总分 **100 分**，四维度加权：

| 维度 | 权重 | 计算方式 |
|------|------|---------|
| 共享兴趣 | 30 分 | `min(sharedCount/maxTags * 60, 30)` |
| 关系目标 | 20 分 | 完全匹配 20 分，否则退化为 5 分 |
| 人格测评 | 30 分 | 15题答案匹配比例 × 30 |
| 核心价值观 | 20 分 | `min(sharedValues/maxValues * 40, 20)` |

**关键细节**：
- 使用 `normalise()` 做大小写/空白标准化
- 双重叠加奖励（`×2`）以增加区分度
- 返回整数分值 `Math.round(Math.min(score, 100))`

#### B. 15题人格测评问卷
```
q1  社交能量（内向 vs 外向）
q2  沟通风格
q3  冲突处理
q4  自发性 vs 计划性
q5  情感表达
q6  爱的语言
q7  生活优先级
q8  周末偏好
q9  决策方式
q10 信任构建
q11 未来目标
q12 幽默风格
q13 压力应对
q14 社交圈
q15 底线/雷区
```

#### C. 数据模型
```
User → Like → Match → Message
     ↓
   personalityQuiz (Map<q1..q15>)
   discoveryPreferences (ageMin, ageMax, gender, maxDistance)
   values[] (up to 8 core values)
   profile { age, bio, interests[], hobbies[], education, lookingFor, profession }
```

### 适配建议
匹配算法可直接翻译为 Python（FastAPI），问卷体系完全可复用。

---

## 3. flutter-fastapi-websocket-chat

- **仓库**：[TechyCodex/flutter-fastapi-websocket-chat](https://github.com/TechyCodex/flutter-fastapi-websocket-chat)
- **许可证**：MIT
- **技术栈**：Flutter + FastAPI + WebSocket（与我们完全一致！）

### 核心代码分析

#### A. FastAPI WebSocket 服务端
```python
clients = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for client in clients:
                await client.send_text(data)
    except:
        clients.remove(websocket)
```

**可改进点**（我们适配时要加上）：
- 用 `dict[str, WebSocket]` 替代 `list`，支持按 user_id 私聊
- 添加 JWT 认证
- 添加消息持久化到 PostgreSQL

#### B. Flutter WebSocket 客户端
```dart
channel = WebSocketChannel.connect(Uri.parse("ws://IP:8080/ws"));
channel.stream.listen((data) {
    final parts = data.split(":");
    // sender: message 格式解析
    setState(() { _messages.add({...}); });
});
```

**可改进点**：
- 改用 JSON 格式替代 `sender: message` 纯文本
- 支持消息类型（text/image/system）
- 添加重连机制

---

## 4. Card Swipper (Umaiir11)

- **仓库**：[Umaiir11/cardswipper](https://github.com/Umaiir11/cardswipper)
- **技术栈**：Flutter + GetX

### 可借鉴内容
- Tinder 风格卡片滑动动画
- 左滑不喜欢/右滑喜欢
- 撤销上次滑动（Undo）
- 卡片耗尽时重置

---

## 5. 2connectv1-ai

- **仓库**：[temurkhan13/2connectv1-ai](https://github.com/temurkhan13/2connectv1-ai)
- **225 次提交**
- **技术栈**：FastAPI + PostgreSQL + Redis + SentenceTransformers

### 核心可借鉴内容
- **语义相似度匹配**：`all-MiniLM-L6-v2` 模型（384维向量嵌入）
- **Supabase 集成**
- **Alembic 迁移管理**
- **GitHub Actions CI/CD**

---

## 当前项目适配方案总结

### 可直接适配的代码模块

| 来源 | 模块 | 适配目标 | 适配难度 |
|------|------|---------|----------|
| Connectly | Clean Architecture 分层 | Backend 项目骨架 | 低 |
| Connectly | Haversine 距离计算 | domain/services/ | 低 |
| Connectly | Deck Builder 候选引擎 | application/use_cases/ | 中 |
| MIIRA | 兼容性匹配算法 | application/services/ | 低 |
| MIIRA | 15题人格问卷 | 数据模型 + API | 低 |
| FastAPI-Chat | WebSocket 服务端/客户端 | 聊天系统 | 中 |
| Card Swipper | 卡片滑动动画 | Flutter 匹配页 | 低 |
| 2connectv1-ai | Alembic CI/CD | DevOps | 低 |

### 许可证合规
- **MIT 许可证**：Connectly、flutter-fastapi-websocket-chat 可自由使用/修改
- **未标注**：MIIRA、Card Swipper、2connectv1-ai（代码量少，以参考架构思路为主，不直接复制大段代码）

### 风险说明
- Connectly 的 Clean Architecture 分层较多，初期可能过重；建议按需简化
- MIIRA 使用 Node.js/MongoDB，算法需翻译为 Python/PostgreSQL
- flutter-fastapi-websocket-chat 较简单，生产环境需大量增强
