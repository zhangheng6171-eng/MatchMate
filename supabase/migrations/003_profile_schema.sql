-- MatchMate P2 资料系统迁移
-- 1. 添加 profiles 新字段 (photos, profile_complete)
-- 2. 创建资料操作日志表

-- ============================================
-- 1. 扩展 profiles 表
-- ============================================
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS photos TEXT DEFAULT '[]';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS profile_complete BOOLEAN DEFAULT FALSE;

-- ============================================
-- 2. 创建资料操作日志表
-- ============================================
CREATE TABLE IF NOT EXISTS profile_operation_logs (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    details TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_operation_logs_user ON profile_operation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_created ON profile_operation_logs(created_at);
