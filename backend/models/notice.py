"""公告表 ORM 实体（对应 notices 表）"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Notice(Base):
    """公告实体：一行 = 一条公告"""

    __tablename__ = "notices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)   # 标题
    content: Mapped[str | None] = mapped_column(Text)                 # 内容
    publisher: Mapped[str | None] = mapped_column(String(50))         # 发布人
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now)
