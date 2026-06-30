# 项目协作流程文档

> 项目：相亲 App（Flutter + FastAPI）
> 编码：UTF-8
> 更新日期：2026-06-29

---

## 一、总体协作流程

```
用户需求
    │
    ▼
┌──────────────────────────────────────────────┐
│                 CEO Agent                    │
│  分析需求 → 拆解任务 → 制定 Roadmap → 分配任务   │
└──────────────────────────────────────────────┘
    │
    ├──────────────────┐
    ▼                  ▼
┌────────────┐   ┌──────────────────────────────┐
│ GitHub     │   │      开发阶段（并行）            │
│ Research   │   │  ┌──────────┐ ┌──────────┐   │
│ Agent     │   │  │ Flutter   │ │ Backend   │   │
│ 技术调研    │   │  │ Agent    │ │ Agent     │   │
└─────┬──────┘   │  └────┬─────┘ └────┬─────┘   │
      │          └───────┼────────────┼─────────┘
      │                  │    联调     │
      │                  └─────┬──────┘
      │                        ▼
      │          ┌──────────────────────────┐
      └──────────►│       QA Agent           │
                  │  测试 → Bug报告 → 修复验证  │
                  └────────────┬─────────────┘
                               ▼
                  ┌──────────────────────────┐
                  │      DevOps Agent         │
                  │  构建 → 部署 → 监控告警     │
                  └──────────────────────────┘
```

---

## 二、阶段式开发流程

### 阶段 0：项目初始化（P0）

**触发**：用户提出相亲 App 开发需求

**流程**：
```
1. CEO Agent
   ├── 分析需求范围
   ├── 制定完整 Roadmap
   └── 输出《项目总体计划》

2. GitHub Research Agent
   ├── 调研 Flutter 相亲 App 开源项目
   ├── 调研 FastAPI 社交后端项目
   └── 输出《技术调研报告》

3. DevOps Agent
   ├── 初始化项目仓库
   ├── 创建 Docker 开发环境
   ├── 配置 CI/CD 流水线
   └── 输出《环境搭建文档》

4. Backend Agent（启动骨架）
   ├── 初始化 FastAPI 项目结构
   ├── 配置 PostgreSQL + Redis 连接
   └── 建立基础目录结构

5. Flutter Agent（启动骨架）
   ├── 初始化 Flutter 项目
   ├── 配置 Riverpod / GoRouter / Dio
   └── 建立基础目录结构
```

---

### 阶段 1：用户系统（P1）

**流程**：
```
1. Backend Agent
   ├── 设计 users / user_profiles 表
   ├── 实现注册 API（手机/邮箱）
   ├── 实现登录 API（JWT 认证）
   ├── 实现个人资料 CRUD API
   ├── 实现图片上传 API
   └── 输出《用户系统 API 文档》

2. Flutter Agent（并行）
   ├── 开发登录/注册页面
   ├── 开发个人资料编辑页面
   ├── 对接用户系统 API
   └── 实现登录态管理（Riverpod）

3. QA Agent
   ├── 测试注册/登录全流程
   ├── 测试 Token 刷新机制
   ├── 测试资料编辑和图片上传
   └── 输出《P1 测试报告》
```

---

### 阶段 2：匹配系统（P2）

**流程**：
```
1. GitHub Research Agent
   ├── 调研 Tinder/Hinge 匹配算法
   ├── 调研推荐系统方案
   └── 输出《匹配系统调研报告》

2. Backend Agent
   ├── 设计 user_swipes / matches 表
   ├── 实现滑动记录 API（左滑/右滑/超级喜欢）
   ├── 实现推荐算法（基于标签/位置/偏好）
   ├── 实现双向匹配检测
   └── 输出《匹配系统 API 文档》

3. Flutter Agent（并行）
   ├── 开发推荐卡片流页面（滑动动画）
   ├── 开发匹配列表页面
   ├── 对接匹配 API
   └── 实现匹配成功特效

4. QA Agent
   ├── 测试推荐算法准确性
   ├── 测试高并发滑动性能
   ├── 测试匹配通知
   └── 输出《P2 测试报告》
```

---

### 阶段 3：聊天系统（P3）

**流程**：
```
1. Backend Agent
   ├── 设计 conversations / messages 表
   ├── 实现 WebSocket 聊天服务
   ├── 实现消息存储和分页查询
   ├── 实现离线消息推送（FCM）
   └── 输出《聊天系统 API 文档》

2. Flutter Agent（并行）
   ├── 开发会话列表页面
   ├── 开发聊天页面（WebSocket 实时通讯）
   ├── 实现消息推送处理
   └── 实现图片/语音消息

3. QA Agent
   ├── 测试消息实时性
   ├── 测试多端消息同步
   ├── 测试离线消息推送
   └── 输出《P3 测试报告》
```

---

### 阶段 4：会员系统（P4）

**流程**：
```
1. Backend Agent
   ├── 设计 memberships / payments 表
   ├── 实现会员等级和权益 API
   ├── 实现支付集成（Stripe）
   ├── 实现订阅管理（续费/取消）
   └── 输出《会员系统 API 文档》

2. Flutter Agent（并行）
   ├── 开发会员中心页面
   ├── 开发订阅购买页面
   ├── 对接支付 SDK
   └── 实现会员权益展示

3. QA Agent
   ├── 测试支付流程
   ├── 测试会员权益生效
   ├── 测试订阅续费/取消
   └── 输出《P4 测试报告》
```

---

### 阶段 5：后台管理（P5）

**流程**：
```
1. Backend Agent
   ├── 实现管理员认证
   ├── 实现用户管理 API
   ├── 实现数据统计 API
   ├── 实现内容审核 API
   └── 输出《后台管理 API 文档》

2. Flutter Agent / Web
   ├── 开发管理后台页面
   ├── 实现数据看板
   └── 实现审核工作流

3. QA Agent
   ├── 测试权限控制
   ├── 测试数据统计准确性
   └── 输出《P5 测试报告》
```

---

### 阶段 6：测试与上线（P6）

**流程**：
```
1. QA Agent
   ├── 全量功能回归测试
   ├── 安全漏洞扫描
   ├── 性能压力测试
   └── 输出《上线前测试报告》

2. DevOps Agent
   ├── 生产环境服务器配置
   ├── Docker 生产构建
   ├── 数据库生产部署
   ├── SSL 证书配置
   ├── 监控告警配置
   └── 输出《上线部署文档》

3. CEO Agent
   ├── 验收全部功能
   ├── 评估项目质量
   └── 输出《项目交付报告》
```

---

## 三、任务流转规范

### 正向流转（任务下发）

```
CEO Agent
  │
  │  任务指令格式：
  │  {
  │    "target_agent": "flutter-agent",
  │    "task_type": "page_development",
  │    "description": "开发登录页面",
  │    "spec": { ... },
  │    "priority": "high",
  │    "deadline": "P1"
  │  }
  │
  ▼
目标 Agent
```

### 反向汇报（结果上报）

```
Agent
  │
  │  汇报格式：
  │  {
  │    "from_agent": "flutter-agent",
  │    "status": "completed" | "blocked" | "in_progress",
  │    "summary": "登录页面开发完成",
  │    "artifacts": ["文件路径列表"],
  │    "blockers": ["阻塞项说明"],
  │    "next_agent": "qa-agent"
  │  }
  │
  ▼
CEO Agent
```

---

## 四、异常处理流程

### Bug 发现流程
```
QA Agent 发现 Bug
    │
    ├── 评估严重级别
    │   ├── 🔴 严重 → 立即通知 CEO + 对应开发 Agent
    │   ├── 🟡 中等 → 记录到 Bug 列表，排入下个迭代
    │   └── 🟢 低   → 记录，累积批量修复
    │
    └── 对应开发 Agent 修复 → QA 验证 → 关闭
```

### 技术阻塞流程
```
Agent 遇到技术阻塞
    │
    ├── 先尝试自行解决（30 分钟内）
    │
    ├── 无法解决 → 上报 CEO Agent
    │       │
    │       ├── 需要调研 → 通知 GitHub Research Agent
    │       └── 需要决策 → CEO 评估后给出方向
    │
    └── 解决后 → 继续执行任务
```

---

## 五、并行开发策略

允许同时进行的任务组合：

| 并行组 | Agent 1 | Agent 2 | Agent 3 | 条件 |
|--------|---------|---------|---------|------|
| A | Flutter Agent（P1 用户页面） | Backend Agent（P1 用户 API） | GitHub Research（P2 匹配调研） | P0 完成 |
| B | Flutter Agent（P2 匹配页面） | Backend Agent（P2 匹配 API） | QA Agent（P1 测试） | P1 开发完成 |
| C | Flutter Agent（P3 聊天页面） | Backend Agent（P3 聊天 API） | QA Agent（P2 测试） | P2 开发完成 |
| D | Flutter Agent（P4 会员页面） | Backend Agent（P4 会员 API） | DevOps（CI/CD 优化） | P3 完成后 |

**原则**：
- 同一模块的前后端可并行开发（已定义好 API 契约后）
- 上一阶段的 QA 测试可与下一阶段的开发并行
- DevOps 工作可在任何阶段并行推进
- GitHub Research 调研应提前于对应开发阶段 1 个周期

---

> 所有 Agent 使用中文交流 | 统一 UTF-8 编码
