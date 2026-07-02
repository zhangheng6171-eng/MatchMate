# MONITORING_SETUP.md
## MatchMate 错误监控接入指南

**日期**: 2026-07-02
**监控方案**: Sentry (Free Tier)

---

## 当前状态

- `sentry-sdk>=2.0.0` 已添加到 `requirements.txt`
- `app/main.py` 已集成 Sentry 初始化代码
- 缺少: `SENTRY_DSN` 环境变量 → Sentry 当前未启用

---

## 步骤1: 注册 Sentry 账户

1. 打开 https://sentry.io/signup/
2. 使用 GitHub 账户注册（免费）
3. 创建新项目: FastAPI (Python)

---

## 步骤2: 获取 DSN

1. 项目创建后，Sentry 会显示 DSN
2. 格式: `https://<key>@sentry.io/<project_id>`
3. 复制此 DSN

---

## 步骤3: 配置 Vercel 环境变量

1. Vercel Dashboard → `workplace1app` → Settings → Environment Variables
2. 添加:

| Key | Value | Environment |
|-----|-------|-------------|
| `SENTRY_DSN` | `<你的 Sentry DSN>` | Production |

3. 重新部署生效

---

## 步骤4: 验证

```bash
# 触发测试错误
curl https://workplace1app.vercel.app/api/nonexistent
```

在 Sentry Dashboard → Issues 中应看到错误出现。

---

## Sentry Free Tier

| 项目 | 免费限制 |
|------|----------|
| 错误事件 | 5,000/月 |
| 保留期 | 30 天 |
| 通知 | Email |

---

## 代码已集成

```python
if os.getenv("SENTRY_DSN"):
    import sentry_sdk
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
```
