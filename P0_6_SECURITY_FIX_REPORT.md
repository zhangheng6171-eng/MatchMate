# P0_6_SECURITY_FIX_REPORT.md
## MatchMate P0.6 Security Emergency Fix 报告

**日期**: 2026-07-02
**阶段**: P0.6 Beta Stability Hardening
**目标**: 修复全部 P0 安全阻塞项，不开发任何新功能

---

## 修改概要

| 任务 | 修改文件 | 状态 |
|------|----------|------|
| A. Secret Rotation | `app/core/config.py` | 完成 |
| B. Rate Limit | `app/main.py`, `app/api/auth.py`, `app/core/limiter.py`, `requirements.txt` | 完成 |
| C. Login Protection | `app/api/auth.py`, `supabase/migrations/004_security_hardening.sql` | 完成 |
| D. Registration Protection | `app/api/auth.py` | 完成 |
| E. Error Monitoring | `app/main.py`, `requirements.txt` | 完成 |

---

## 任务A: Secret Rotation

### 修改: `app/core/config.py`

1. JWT_SECRET_KEY: 删除硬编码默认值 `"dev-jwt-secret-change-in-production"` → `""`
2. SUPABASE_SERVICE_KEY: 删除硬编码真实密钥 `"eyJhbGciOi..."` → `""`
3. 新增 `_validate_critical_secrets()`: 缺失环境变量时启动失败
4. 保留 SUPABASE_ANON_KEY (公开密钥)

### 产出: `SECRET_ROTATION_GUIDE.md`
- Supabase Service Key 轮换步骤
- Vercel 环境变量配置
- Git 历史清理
- 部署验证检查清单

---

## 任务B: Rate Limit

### 新增: `app/core/limiter.py`
共享 Limiter 实例

### 修改: `app/main.py`
- 注册 slowapi 中间件
- `/api/deck/explore` 限流 60/minute

### 修改: `app/api/auth.py`
| 端点 | 限制 |
|------|------|
| POST /api/auth/send-code | 3/minute/IP |
| POST /api/auth/login | 5/minute/IP |
| POST /api/auth/register/code | 3/minute/IP |

### 修改: `requirements.txt`
- +slowapi>=0.1.9

---

## 任务C: Login Protection

### 迁移: `supabase/migrations/004_security_hardening.sql`
- users 表新增: `login_attempts INTEGER DEFAULT 0`, `locked_until TIMESTAMPTZ`
- 索引: `idx_users_locked`
- **已应用到 Supabase**

### 修改: `app/api/auth.py` login_with_password
- 登录前检查 locked_until → 锁定则返回 429
- 密码失败: login_attempts += 1, 达到5次 → 设置 locked_until = now + 15min
- 登录成功: login_attempts = 0, locked_until = NULL
- 常量: LOGIN_MAX_ATTEMPTS = 5, LOCK_DURATION_MINUTES = 15

---

## 任务D: Registration Protection

### 修改: `app/api/auth.py`
- **移除**: `POST /api/auth/register` 端点（密码注册无需验证码）
- **保留**: `POST /api/auth/register/code`（需要验证码）+ 3/min 限流
- 用户只能通过验证码注册

---

## 任务E: Error Monitoring

### 修改: `app/main.py`
- 条件启用 Sentry (仅当 SENTRY_DSN 环境变量存在)
- send_default_pii=False
- traces_sample_rate=0.1

### 修改: `requirements.txt`
- +sentry-sdk>=2.0.0

### 产出: `MONITORING_SETUP.md`
- Sentry 注册步骤
- DSN 获取
- Vercel 环境变量配置
- 验证方法

---

## 测试结果

| 检查项 | 结果 |
|--------|------|
| 硬编码 SERVICE_KEY 移除 | PASS |
| 硬编码 JWT_SECRET_KEY 移除 | PASS |
| 启动校验函数 | PASS |
| slowapi 集成 | PASS |
| send-code 3/min 限流 | PASS |
| login 5/min 限流 | PASS |
| register/code 3/min 限流 | PASS |
| deck/explore 60/min 限流 | PASS |
| 登录失败计数 | PASS |
| 5次锁定 15 分钟 | PASS |
| 成功登录清零 | PASS |
| 移除无验证码注册端点 | PASS |
| Sentry 条件接入 | PASS |
| 数据库迁移应用 | PASS |

**通过率: 14/14 (100%)**

---

## 部署步骤

1. 按 `SECRET_ROTATION_GUIDE.md` 完成 Supabase Key 轮换（人工操作 - 尚未执行）
2. 配置 Vercel 环境变量: `SUPABASE_SERVICE_KEY`, `JWT_SECRET_KEY`
3. Push 代码 → Vercel 自动部署
4. 验证 `/api/health`
5. 验证限流 (多次快速调用 → 429)
6. 验证登录保护 (5次错误密码 → 锁定)
7. 验证注册保护 (POST /api/auth/register → 404)
8. (可选) 配置 `SENTRY_DSN`

---

## 文件清单

| 文件 | 操作 |
|------|------|
| `app/core/config.py` | MODIFIED |
| `app/core/limiter.py` | CREATED |
| `app/main.py` | MODIFIED |
| `app/api/auth.py` | MODIFIED |
| `requirements.txt` | MODIFIED |
| `supabase/migrations/004_security_hardening.sql` | CREATED |
| `SECRET_ROTATION_GUIDE.md` | CREATED |
| `MONITORING_SETUP.md` | CREATED |
| `P0_6_SECURITY_FIX_REPORT.md` | CREATED |

---

**P0.6 Security Emergency Fix Complete**
