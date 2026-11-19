-- ============================================
-- 学生刷脸考勤系统 - 建表 SQL（表结构的唯一来源）
-- 由 tools/init_db.py 执行落库
-- ============================================

-- 学生表
-- student_no 加 UNIQUE：学号不可重复
-- gender 加 CHECK：只允许「男」/「女」（NULL 表示未填，不受限）
-- age    加 CHECK：只允许 18~28（NULL 表示未填，不受限）
-- face_status 冗余字段：快速统计"已录/未录"，不必 join faces 表
-- 注意：本文件是表结构的唯一来源；改了这里的老库需要跑 tools/migrate_add_age.py
CREATE TABLE IF NOT EXISTS students (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,          -- 主键自增
    student_no  VARCHAR(20) NOT NULL UNIQUE,                -- 学号(唯一)
    name        VARCHAR(50) NOT NULL,                       -- 姓名
    gender      VARCHAR(10) CHECK (gender IS NULL OR gender IN ('男','女')),  -- 性别(只能男/女)
    age         INTEGER CHECK (age IS NULL OR (age BETWEEN 18 AND 28)),       -- 年龄(18~28)
    class_name  VARCHAR(50),                                -- 班级
    major       VARCHAR(50),                                -- 专业
    enroll_year INTEGER,                                    -- 入学年份
    phone       VARCHAR(20),                                -- 联系方式
    face_status INTEGER DEFAULT 0,                          -- 人脸录入状态 0未录/1已录
    created_at  DATETIME DEFAULT (datetime('now','localtime')),  -- 创建时间
    updated_at  DATETIME DEFAULT (datetime('now','localtime'))   -- 更新时间
);

-- 脸照元数据表（人脸向量存在 Milvus，这里只存元数据）
-- face_id 加 UNIQUE：桥接 Milvus 的 face_id，一一对应
-- student_id 外键：ON DELETE CASCADE 删学生自动删脸照
CREATE TABLE IF NOT EXISTS faces (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    face_id     INTEGER NOT NULL UNIQUE,                    -- 桥接 Milvus 的 face_id
    student_id  INTEGER NOT NULL,                           -- 所属学生
    image_path  VARCHAR(255),                               -- 脸照文件路径
    created_at  DATETIME DEFAULT (datetime('now','localtime')),  -- 录入时间
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- 公告表
CREATE TABLE IF NOT EXISTS notices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       VARCHAR(100) NOT NULL,                      -- 标题
    content     TEXT,                                       -- 内容
    publisher   VARCHAR(50),                                -- 发布人
    created_at  DATETIME DEFAULT (datetime('now','localtime'))   -- 发布时间
);

-- 考勤记录表（刷脸签到/签退）
-- student_id 外键：ON DELETE CASCADE 删学生自动删考勤记录
-- check_type：checkin签到 / checkout签退
-- status：normal正常 / late迟到 / early早退 / absent缺勤
-- similarity：识别相似度(0~1)，用于追溯识别质量
CREATE TABLE IF NOT EXISTS attendance (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id  INTEGER NOT NULL,                           -- 识别出的学生
    check_time  DATETIME DEFAULT (datetime('now','localtime')),  -- 打卡时间
    check_type  VARCHAR(10) DEFAULT 'checkin',              -- checkin签到 / checkout签退
    similarity  REAL,                                       -- 识别相似度(0~1)
    status      VARCHAR(10) DEFAULT 'normal',               -- normal正常 / late迟到 / early早退 / absent缺勤
    remark      VARCHAR(200),                               -- 备注
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- 用户表（登录鉴权）
-- password_hash 存 bcrypt 哈希（含随机 salt），绝不存明文
-- role：admin 可写 / viewer 只读，接口层用依赖注入判断
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    role          VARCHAR(20) NOT NULL DEFAULT 'viewer',
    created_at    DATETIME DEFAULT (datetime('now','localtime'))
);
