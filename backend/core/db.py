"""数据库连接 - 对应 Java 的 SessionFactory / DataSource

SQLAlchemy 2.0 的现代用法：
- create_engine 创建引擎（连接池）
- sessionmaker 创建会话工厂
- 每次请求用 with 拿一个 Session，用完关闭
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from core.config import DATABASE_URL
from models.base import Base

# 创建引擎。check_same_thread=False 是 SQLite 必须的（FastAPI 多线程访问）
# timeout=30：写锁等待 30 秒，避免多连接并发写时报 database is locked
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
    echo=False,  # 设为 True 可打印 SQL，调试时有用
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """开启 SQLite 外键约束 + WAL 模式
    - 外键约束默认关闭，不开启 ON DELETE CASCADE 不生效
    - WAL 模式允许多个连接同时读，减少写锁冲突
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()

# 会话工厂
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """依赖注入：FastAPI 通过 Depends(get_db) 拿到数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
