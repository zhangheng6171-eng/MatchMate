# AI 开发团队 Agent 总览

> 项目：相亲 App（Flutter + FastAPI）
> 编码：UTF-8
> 更新日期：2026-06-29

---

## 团队架构

```
                    ┌─────────────────┐
                    │   CEO Agent     │  项目总规划 / 任务拆解 / 进度跟踪
                    └───────┬─────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────────┐
│GitHub Research   │ │  Flutter     │ │  Backend     │
│    Agent        │ │   Agent      │ │   Agent      │
│ 开源调研 / 技术选型 │ │ 移动端开发    │ │ 后端开发      │
└─────────────────┘ └──────┬───────┘ └──────┬───────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │   QA Agent     │  测试 / 质量保障
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │  DevOps Agent  │  部署 / CI/CD / 运维
                  └────────────────┘
```

---

## Agent 速览表

| # | Agent | 名称 | 技术栈 | 核心职责 | MCP 状态 |
|---|-------|------|--------|---------|---------|
| 1 | CEO Agent | `ceo-agent` | — | 需求分析 · 阶段规划 · 任务分配 · 进度跟踪 · 风险管理 | ⚠️ 部分缺失 |
| 2 | GitHub Research Agent | `github-research-agent` | — | 开源搜索 · 架构分析 · 最佳实践 · 模块推荐 | ❌ 大部分缺失 |
| 3 | Flutter Agent | `flutter-agent` | Flutter · Riverpod · GoRouter · Dio | 页面开发 · UI优化 · 状态管理 · 性能优化 | ⚠️ 部分缺失 |
| 4 | Backend Agent | `backend-agent` | FastAPI · PostgreSQL · Redis · SQLAlchemy | API设计 · 数据库设计 · 用户/聊天/推荐/会员系统 | ⚠️ 部分缺失 |
| 5 | QA Agent | `qa-agent` | — | 功能测试 · 回归测试 · 安全检查 · Bug定位 | ⚠️ 部分缺失 |
| 6 | DevOps Agent | `devops-agent` | Docker · GitHub Actions · Supabase · Cloudflare | 容器部署 · CI/CD · 监控告警 · 自动备份 | ⚠️ 部分缺失 |

---

## 各 Agent 调用时机

### CEO Agent
```
【用户输入】→ "我要做一个相亲App"
    ↓
【CEO Agent】分析需求 → 拆解阶段 → 分配任务
    ↓
【调度其他 Agent】
```

### GitHub Research Agent
```
【CEO 分配调研任务】
    ↓
【GitHub Research Agent】搜索 Flutter 相亲App 参考项目
    ↓
【输出】推荐仓库列表 + 可借鉴方案
```

### Flutter Agent + Backend Agent（并行开发）
```
【CEO 分配开发任务】
    ├──【Flutter Agent】开发登录页 / 个人资料页 / 匹配卡片
    └──【Backend Agent】开发用户API / 匹配API / 数据库表
    ↓
【联调】前后端 API 对接
```

### QA Agent
```
【开发完成通知】
    ↓
【QA Agent】功能测试 + 回归测试 + 安全检查
    ↓
【输出】Bug报告 / 通过验收
```

### DevOps Agent
```
【测试通过通知】
    ↓
【DevOps Agent】Docker 构建 → CI/CD 部署 → 配置监控
    ↓
【输出】部署完成 + 访问地址
```

---

## 完整开发阶段划分

| 阶段 | 名称 | 参与 Agent | 预计交付物 |
|------|------|-----------|-----------|
| P0 | 项目初始化 | CEO + DevOps | 项目骨架、Docker 环境、CI/CD 流水线 |
| P1 | 用户系统 | Backend + Flutter | 注册/登录/资料编辑 API 和页面 |
| P2 | 匹配系统 | Backend + Flutter | 推荐算法、滑动匹配、匹配列表 |
| P3 | 聊天系统 | Backend + Flutter | WebSocket 实时聊天、消息存储 |
| P4 | 会员系统 | Backend + Flutter | VIP 等级、支付集成、会员权益 |
| P5 | 后台管理 | Backend + Flutter | 管理后台 API 和 Web 页面 |
| P6 | 测试与上线 | QA + DevOps | 测试报告、生产部署、监控配置 |

---

## 交流规范

- **语言**：所有 Agent 之间使用中文交流
- **编码**：所有代码和文档统一 UTF-8
- **文档格式**：Markdown（CommonMark 规范）
- **任务分配**：由 CEO Agent 统一调度
- **状态同步**：每个 Agent 完成任务后向 CEO Agent 汇报
