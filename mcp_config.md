# MCP 配置文档

> 项目：相亲 App（Flutter + FastAPI）
> 编码：UTF-8
> 更新日期：2026-06-29

---

## 当前 Trae MCP 安装状态

### ✅ 已安装 MCP

| MCP Server | 工具列表 | 对应 Agent |
|------------|---------|-----------|
| `integrated_web-dev` | `supabase_get_project` / `supabase_get_tables` / `supabase_apply_migration` / `stripe_get_config` / `get_llm_config` / `deploy_to_remote` | Backend / DevOps |

### ❌ 缺失 MCP（需安装）

| MCP | 用途 | 使用 Agent | 优先级 |
|-----|------|-----------|--------|
| GitHub MCP | 仓库搜索、代码管理、Issue/PR 操作 | CEO / Research / Flutter / Backend / DevOps | 🔴 高 |
| Filesystem MCP | 标准文件读写操作 | 全部 Agent | 🔴 高 |
| Memory MCP | 持久化项目上下文和决策记录 | CEO | 🟡 中 |
| Browser MCP | 访问网页资源和技术文档 | GitHub Research | 🟡 中 |
| PostgreSQL MCP | 数据库直接管理（查询/建表/迁移） | Backend | 🟡 中 |
| Playwright MCP | 自动化 E2E 测试 | QA | 🟡 中 |
| Docker MCP | 容器和镜像管理 | DevOps | 🟢 低 |
| Cloudflare MCP | DNS/CDN/WAF 管理 | DevOps | 🟢 低 |

---

## MCP 安装方案

### 方案 1：Filesystem MCP

> Trae IDE 通常内置了文件操作能力，如果 Agent 无法访问文件系统，需单独配置。

**安装方式**：
```json
// 在 Trae MCP 配置中添加
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "e:/traeguojiban/workplace1app"]
    }
  }
}
```

### 方案 2：GitHub MCP

**前提**：需要 GitHub Personal Access Token（在 GitHub Settings > Developer settings 创建）

**安装方式**：
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<your_github_token>"
      }
    }
  }
}
```

**所需权限**：`repo`、`read:org`、`read:user`

### 方案 3：Memory MCP

**安装方式**：
```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

### 方案 4：Browser MCP（Puppeteer）

**安装方式**：
```json
{
  "mcpServers": {
    "browser": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    }
  }
}
```

### 方案 5：PostgreSQL MCP

**前提**：本地或远程 PostgreSQL 已运行

**安装方式**：
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "<DATABASE_URL>"]
    }
  }
}
```

**示例**：`postgresql://user:password@localhost:5432/dating_app`

### 方案 6：Playwright MCP

**安装方式**：
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic/playwright-mcp"]
    }
  }
}
```

### 方案 7：Docker MCP

**前提**：Docker Desktop 已安装并运行

**安装方式**：
```json
{
  "mcpServers": {
    "docker": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-v", "/var/run/docker.sock:/var/run/docker.sock", "mcp/docker"]
    }
  }
}
```

### 方案 8：Cloudflare MCP

**前提**：Cloudflare API Token（在 Cloudflare Dashboard 创建）

**安装方式**：
```json
{
  "mcpServers": {
    "cloudflare": {
      "command": "npx",
      "args": ["-y", "@anthropic/cloudflare-mcp"],
      "env": {
        "CLOUDFLARE_API_TOKEN": "<your_api_token>"
      }
    }
  }
}
```

---

## 推荐安装顺序

| 顺序 | MCP | 原因 |
|------|-----|------|
| 1 | **Filesystem MCP** | 所有 Agent 的基础依赖 |
| 2 | **GitHub MCP** | 代码管理和开源调研的基础 |
| 3 | **Memory MCP** | CEO Agent 需要持久化上下文 |
| 4 | **PostgreSQL MCP** | Backend Agent 数据库操作必需 |
| 5 | **Browser MCP** | GitHub Research Agent 网页调研 |
| 6 | **Playwright MCP** | QA Agent 自动化测试 |
| 7 | **Docker MCP** | DevOps Agent 容器管理 |
| 8 | **Cloudflare MCP** | 生产环境部署（后期需要） |

---

## 配置文件位置

所有 MCP 配置通过 Trae IDE 的 MCP 管理界面添加，或直接编辑：
```
C:\Users\zhang\.trae\mcps\
```

---

> **注意**：`npm`（Node.js）是大多数 MCP Server 的运行依赖，请确保系统已安装 Node.js 18+。
