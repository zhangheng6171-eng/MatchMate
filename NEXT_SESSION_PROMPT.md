# MatchMate 下一阶段开发提示 (P1 — 用户身份系统)

## 当前状态
- **P0 核心基础设施层**：✅ 已完成
- **测试通过率**：8/8 (100%)
- **数据库**：Supabase PostgreSQL (5/5 表已创建)
- **部署**：Vercel 生产环境 `https://workplace1app.vercel.app`

## P0 完成成果
- 5 张核心数据模型：User / Profile / Match / Message / Call
- JWT access/refresh token 双令牌认证架构
- bcrypt 密码哈希 + 密码强度校验
- FastAPI 3 路由模块：auth / profile / match
- Alembic 数据库迁移工具配置
- SQLAlchemy 2.0 异步引擎（asyncpg）

## P1 开发目标

### 核心任务
1. **手机号注册** + 短信验证码（开发期 Console 模拟）
2. **邮箱注册** + 邮件验证码（开发期 Console 模拟）
3. **密码复杂度校验**（已实现 ✅，P1 复用）
4. **账号密码登录**（基础已实现 ✅）
5. **手机号验证码登录**（新增）
6. **JWT Token 自动刷新机制**（基础已实现 ✅）
7. **密码找回**（邮箱/短信验证码重置）
8. **邮箱激活验证**（发送激活链接）

### 技术栈
- python-jose (已有)
- bcrypt (已有)
- FastAPI (已有)
- Supabase Auth SMTP（可选）

### 未解决依赖
- **短信 API Key**（如 Twilio / 阿里云短信）：开发期用 Console 打印验证码代替
- **邮件 SMTP 服务**：可用 Supabase 内置邮件服务或本地 SMTP

## P1 验收标准
- [ ] 所有用户系统接口完成联调
- [ ] 异常场景返回合理错误码（重复注册/错误密码/过期验证码）
- [ ] JWT 签发/校验/刷新/注销全流程正常
- [ ] 未授权用户无法访问受限接口

## 关键文件索引
- 用户模型：`app/models/user.py`
- 认证 API：`app/api/auth.py`
- 安全模块：`app/core/security.py`
- 依赖注入：`app/core/deps.py`
- 配置：`app/core/config.py`
- Repository：`app/repositories/user.py`
- Schema：`app/schemas/auth.py`
