-- MatchMate P1 用户身份系统迁移
-- 创建验证码表，支持短信/邮件验证码

-- 验证码表
CREATE TABLE IF NOT EXISTS verification_codes (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    target TEXT NOT NULL,           -- 手机号 或 邮箱
    code VARCHAR(10) NOT NULL,      -- 验证码（6位数字或激活Token）
    purpose VARCHAR(30) NOT NULL,   -- register / login / reset_password / activate_email
    channel VARCHAR(10) NOT NULL,   -- sms / email
    used BOOLEAN DEFAULT FALSE,     -- 是否已使用
    expires_at TIMESTAMPTZ NOT NULL, -- 过期时间
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 索引：按 target + purpose 快速查找
CREATE INDEX IF NOT EXISTS idx_vcode_target_purpose ON verification_codes(target, purpose);
-- 索引：清除过期验证码
CREATE INDEX IF NOT EXISTS idx_vcode_expires ON verification_codes(expires_at);

-- 定期清理过期验证码（PostgreSQL 定时任务，可选）
-- 开发环境可手动清理，生产环境建议配置 pg_cron
