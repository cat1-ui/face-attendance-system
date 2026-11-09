"""建库脚本 - 手写 SQL 落库（只用 Python 标准库，零额外依赖）

职责：读 data/schema.sql → 执行建表 → 回读验证。
对应老师"第一步"的 7 个动作：
定位目录 → 连接(自动建文件) → 开外键 → 读 SQL → 执行 → 提交 → 回读验证

用法：在 backend 目录下运行
    .venv/Scripts/python.exe tools/init_db.py
"""
from pathlib import Path
import sqlite3

# 由脚本自身位置定位项目根目录（不依赖你在哪个目录运行）
BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_FILE = BASE_DIR / "data" / "schema.sql"
DB_FILE = BASE_DIR / "data" / "db.sqlite"


def init_db() -> list[str]:
    """执行建库，返回表名清单"""
    # 1. 确保数据库所在目录存在
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 2. 连接数据库（文件不存在时自动创建 —— SQLite 特性）
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # 3. 开启外键约束（SQLite 默认关闭，不手动开 ON DELETE CASCADE 就是摆设）
        cursor.execute("PRAGMA foreign_keys = ON")

        # 4. 读取建表 SQL
        sql = SCHEMA_FILE.read_text(encoding="utf-8")

        # 5. 一次执行多句 SQL（脚本化建表，幂等：IF NOT EXISTS 重复执行不报错）
        cursor.executescript(sql)

        # 6. 提交事务
        conn.commit()

        # 7. 回读验证：查 sqlite_master 拿表清单
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

    print(f"[OK] 数据库已创建: {DB_FILE}")
    print(f"[OK] 表清单: {tables}")
    return tables


if __name__ == "__main__":
    init_db()
