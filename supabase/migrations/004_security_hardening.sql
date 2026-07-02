-- MatchMate P0.6 安全加固迁移
-- 为 users 表添加登录保护字段

-- ============================================
-- 1. 添加登录保护字段
-- ============================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ;

-- ============================================
-- 2. 添加索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_users_locked ON users(locked_until) WHERE locked_until IS NOT NULL;
