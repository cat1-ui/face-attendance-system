"""用户表 ORM 实体（对应 users 表）

为什么单独一张表而不是写死一个账号：
- 支持多角色（admin 可写 / viewer 只读），权限判断有实际落点
- 密码存 bcrypt 哈希，不存明文
"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)   # bcrypt 哈希，非明文
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="viewer")  # admin / viewer
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now)
