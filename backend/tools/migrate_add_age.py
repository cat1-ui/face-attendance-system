"""数据迁移 - 给 students 表补 age 列与 gender/age 的 CHECK 约束（不丢数据）

背景：
    表结构的唯一来源是 data/schema.sql，但其中的 CREATE TABLE **IF NOT EXISTS**
    对已经存在的 students 表不生效 —— 所以老库必须单独迁移一次。
    SQLite 又不支持 ALTER TABLE ADD CONSTRAINT，加 CHECK 只能走"重建表"。

做法（SQLite 官方推荐的重建流程）：
    备份 → 关外键 → 建新表 → 拷数据 → 删旧表 → 改名 → 提交 → 开外键 → 校验
    一次把 age 列 + gender/age 的 CHECK 全部补齐，并把脏数据洗成 NULL。

用法（先关掉后端，再在 backend 目录下运行）：
    .venv/Scripts/python.exe tools/migrate_add_age.py
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "data" / "db.sqlite"

# 新表结构：与 data/schema.sql 里的 students 保持一致
NEW_TABLE_DDL = """
CREATE TABLE students_new (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    student_no  VARCHAR(20) NOT NULL UNIQUE,
    name        VARCHAR(50) NOT NULL,
    gender      VARCHAR(10) CHECK (gender IS NULL OR gender IN ('男','女')),
    age         INTEGER CHECK (age IS NULL OR (age BETWEEN 18 AND 28)),
    class_name  VARCHAR(50),
    major       VARCHAR(50),
    enroll_year INTEGER,
    phone       VARCHAR(20),
    face_status INTEGER DEFAULT 0,
    created_at  DATETIME DEFAULT (datetime('now','localtime')),
    updated_at  DATETIME DEFAULT (datetime('now','localtime'))
)
"""

# 老表有的列（age 是新列，不在其中，拷过去为 NULL）
COPY_COLS = "id, student_no, name, gender, class_name, major, enroll_year, phone, face_status, created_at, updated_at"


def _has_column(cur, table: str, column: str) -> bool:
    """判断某表是否已有某列"""
    return any(row[1] == column for row in cur.execute(f"PRAGMA table_info({table})"))


def _backup() -> Path | None:
    """把 WAL 落盘后整库备份，返回备份文件路径"""
    if not DB_FILE.exists():
        return None
    # WAL 模式下，数据可能还在 -wal 文件里，先 checkpoint 再拷才是完整数据
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.commit()
    finally:
        conn.close()

    backup = DB_FILE.with_name(f"db.backup-{datetime.now():%Y%m%d-%H%M%S}.sqlite")
    shutil.copy2(DB_FILE, backup)
    return backup


def migrate() -> None:
    if not DB_FILE.exists():
        print(f"[跳过] 数据库不存在：{DB_FILE}")
        print("       直接运行 tools/init_db.py 建新库即可（schema.sql 已含 age 与 CHECK）")
        return

    backup = _backup()
    print(f"[备份] {backup.name}")

    conn = sqlite3.connect(DB_FILE)
    conn.isolation_level = None  # 关掉 Python 的隐式事务，由我们手工 BEGIN/COMMIT
    cur = conn.cursor()
    try:
        if _has_column(cur, "students", "age"):
            print("[跳过] students 表已有 age 列，无需迁移")
            return

        before = cur.execute("SELECT COUNT(*) FROM students").fetchone()[0]

        # 外键必须在事务外关闭，否则 faces/attendance 的外键会挡住 DROP TABLE
        cur.execute("PRAGMA foreign_keys = OFF")
        cur.execute("BEGIN")
        cur.execute(NEW_TABLE_DDL)
        # 拷数据：gender 非法值洗成 NULL，避免撞上新加的 CHECK
        cur.execute(f"""
            INSERT INTO students_new ({COPY_COLS})
            SELECT id, student_no, name,
                   CASE WHEN gender IN ('男','女') THEN gender ELSE NULL END,
                   class_name, major, enroll_year, phone, face_status, created_at, updated_at
            FROM students
        """)
        # 删旧表 + 改名：改名后 faces/attendance 里按表名引用的外键自动指向新表
        cur.execute("DROP TABLE students")
        cur.execute("ALTER TABLE students_new RENAME TO students")
        cur.execute("COMMIT")
        cur.execute("PRAGMA foreign_keys = ON")

        after = cur.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        broken = cur.execute("PRAGMA foreign_key_check").fetchall()
        cols = [row[1] for row in cur.execute("PRAGMA table_info(students)")]

        print(f"[OK] 迁移完成：students {before} 行 → {after} 行（数据已保留）")
        print(f"[OK] 当前列：{cols}")
        print(f"[OK] 外键校验：{'通过' if not broken else f'发现 {len(broken)} 处异常 {broken}'}")
    except Exception:
        conn.rollback()
        print("[失败] 迁移出错已回滚，原始数据未受影响；可从上面的备份文件恢复")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
