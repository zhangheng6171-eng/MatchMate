-- MatchMate P0 核心模型迁移
-- 先清理旧表（无生产数据），再创建新的规范化表结构

-- ============================================
-- 1. 清理旧表（按外键依赖倒序删除）
-- ============================================
DROP TABLE IF EXISTS date_feedback CASCADE;
DROP TABLE IF EXISTS weekly_matches CASCADE;
DROP TABLE IF EXISTS match_history CASCADE;
DROP TABLE IF EXISTS likes CASCADE;
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS questionnaire_answers CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 同时清理可能存在的残留枚举
DROP TYPE IF EXISTS gender_enum CASCADE;
DROP TYPE IF EXISTS looking_for_enum CASCADE;
DROP TYPE IF EXISTS message_type_enum CASCADE;
DROP TYPE IF EXISTS message_status_enum CASCADE;
DROP TYPE IF EXISTS call_type_enum CASCADE;
DROP TYPE IF EXISTS call_status_enum CASCADE;

-- ============================================
-- 2. 创建枚举类型
-- ============================================
CREATE TYPE gender_enum AS ENUM ('male', 'female', 'other');
CREATE TYPE looking_for_enum AS ENUM ('casual', 'serious', 'marriage', 'friendship');
CREATE TYPE message_type_enum AS ENUM ('text', 'image', 'system');
CREATE TYPE message_status_enum AS ENUM ('sent', 'delivered', 'read');
CREATE TYPE call_type_enum AS ENUM ('voice', 'video');
CREATE TYPE call_status_enum AS ENUM ('ringing', 'in_progress', 'ended', 'missed', 'rejected', 'busy');

-- ============================================
-- 3. 创建核心表
-- ============================================

-- 用户认证表
CREATE TABLE users (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(255) UNIQUE,
    hashed_password VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMPTZ,
    refresh_token_version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 用户资料表
CREATE TABLE profiles (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    nickname VARCHAR(50),
    avatar_url VARCHAR(500),
    bio TEXT,
    gender gender_enum,
    birthday DATE,
    age INTEGER,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    city VARCHAR(100),
    interests TEXT[],
    hobbies TEXT[],
    looking_for looking_for_enum,
    preferred_age_min INTEGER DEFAULT 18,
    preferred_age_max INTEGER DEFAULT 60,
    preferred_distance_km INTEGER DEFAULT 30,
    personality_quiz TEXT,
    is_profile_public BOOLEAN DEFAULT TRUE,
    show_distance BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 匹配关系表
CREATE TABLE matches (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user1_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user2_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user1_decision BOOLEAN,
    user2_decision BOOLEAN,
    is_mutual BOOLEAN DEFAULT FALSE,
    matched_at TIMESTAMPTZ,
    swipe_type VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_match_pair UNIQUE (user1_id, user2_id)
);

-- 消息表
CREATE TABLE messages (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    sender_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    message_type message_type_enum DEFAULT 'text',
    status message_status_enum DEFAULT 'sent',
    is_recalled BOOLEAN DEFAULT FALSE,
    is_deleted_by_sender BOOLEAN DEFAULT FALSE,
    is_deleted_by_receiver BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    recalled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 通话记录表
CREATE TABLE calls (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    caller_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    callee_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    call_type call_type_enum NOT NULL,
    status call_status_enum DEFAULT 'ringing',
    duration_seconds INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    quality_score INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================
-- 4. 创建索引
-- ============================================
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_created ON users(created_at);

CREATE INDEX idx_profiles_location ON profiles(latitude, longitude);
CREATE INDEX idx_profiles_city ON profiles(city);
CREATE INDEX idx_profiles_looking_for ON profiles(looking_for);

CREATE INDEX idx_match_user1 ON matches(user1_id);
CREATE INDEX idx_match_user2 ON matches(user2_id);
CREATE INDEX idx_match_mutual ON matches(is_mutual);

CREATE INDEX idx_message_conversation ON messages(sender_id, receiver_id);
CREATE INDEX idx_message_created ON messages(created_at);
CREATE INDEX idx_message_status ON messages(status);

CREATE INDEX idx_call_caller ON calls(caller_id);
CREATE INDEX idx_call_callee ON calls(callee_id);
CREATE INDEX idx_call_created ON calls(created_at);

-- ============================================
-- 5. updated_at 自动触发器
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_matches_updated_at BEFORE UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_messages_updated_at BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_calls_updated_at BEFORE UPDATE ON calls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
