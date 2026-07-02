# SECRET_ROTATION_GUIDE.md
## MatchMate 密钥轮换与安全加固指南

**日期**: 2026-07-02
**触发原因**: P0.6 安全审计发现 SUPABASE_SERVICE_KEY 以明文硬编码在源代码中，已推送至公开 GitHub 仓库

---

## 风险等级: CRITICAL

`SUPABASE_SERVICE_KEY` 是 Supabase 的 Service Role 密钥，拥有数据库的完全读写权限。该密钥当前在 GitHub 公开仓库中可见：
- https://github.com/zhangheng6171-eng/MatchMate/blob/master/app/core/config.py

---

## 步骤1: Supabase Service Role Key 轮换

### 1.1 登录 Supabase Dashboard
1. 打开 https://supabase.com/dashboard
2. 选择项目 `ntaqnyegiiwtzdyqjiwy` (MatchMate)
3. 进入 **Project Settings** → **API**

### 1.2 吊销旧密钥
1. 找到 `service_role` key 部分
2. 点击 **Revoke** 吊销当前密钥
3. 确认吊销操作

### 1.3 生成新密钥
1. 吊销后会自动生成新的 Service Role Key
2. 立即复制新密钥（这将是唯一看到它的机会）
3. 新密钥格式: `eyJhbGciOiJIUzI1NiIs...`

---

## 步骤2: Vercel 环境变量配置

### 2.1 登录 Vercel Dashboard
1. 打开 https://vercel.com/dashboard
2. 选择 `workplace1app` 项目

### 2.2 配置环境变量
1. 进入 **Settings** → **Environment Variables**
2. 添加以下变量:

| Key | Value | Environment |
|-----|-------|-------------|
| `SUPABASE_SERVICE_KEY` | `<新生成的 Service Role Key>` | Production |
| `JWT_SECRET_KEY` | `<生成一个强随机密钥 32+ 字符>` | Production |

JWT_SECRET_KEY 生成命令 (本地执行):
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2.3 重新部署
1. 环境变量更改后，Vercel 会自动触发重新部署
2. 或手动触发: **Deployments** → **Redeploy** (最新 commit)

---

## 步骤3: Git 历史清理

旧密钥仍存在于 Git 提交历史中，必须清除。

### 3.1 使用 BFG Repo-Cleaner (推荐)

```bash
# 创建 secrets.txt 文件，包含需要替换的密钥
# 在仓库中运行:
bfg --replace-text secrets.txt

# 清理并强制推送
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push origin --force --all
git push origin --force --tags
```

### 3.2 通知 GitHub
旧 commit 被 fork 后仍可访问。联系 GitHub Support 请求从缓存中删除敏感数据。

---

## 步骤4: 本地 .env 文件配置

在项目根目录创建 `.env`:
```bash
SUPABASE_SERVICE_KEY=eyJhbGciOi...（新密钥）
JWT_SECRET_KEY=<生成的强随机密钥>
ENVIRONMENT=development
```

验证:
```bash
python -c "from app.core.config import settings; print('SERVICE_KEY configured:', bool(settings.SUPABASE_SERVICE_KEY)); print('JWT_KEY configured:', bool(settings.JWT_SECRET_KEY))"
```

---

## 步骤5: 部署验证

### 5.1 Vercel 部署检查
```bash
curl https://workplace1app.vercel.app/api/health
```
预期: `{"status":"ok",...}`

### 5.2 检查清单
- [ ] Supabase Dashboard 吊销旧 Service Role Key
- [ ] 生成新 Service Role Key
- [ ] Vercel 环境变量配置 SUPABASE_SERVICE_KEY
- [ ] Vercel 环境变量配置 JWT_SECRET_KEY
- [ ] Vercel 自动重新部署成功
- [ ] 创建本地 .env 文件
- [ ] 本地启动验证通过
- [ ] 生产环境 API 健康检查通过
- [ ] Git 历史清理完成
