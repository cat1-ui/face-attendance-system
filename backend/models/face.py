"""脸照表 ORM 实体（对应 faces 表，向量存 Milvus）"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Face(Base):
    """脸照元数据实体：一行 = 一张脸照（embedding 向量在 Milvus）"""

    __tablename__ = "faces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    face_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)   # 桥接 Milvus 的 face_id
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )                                                                            # 所属学生(级联删除)
    image_path: Mapped[str | None] = mapped_column(String(255))                   # 脸照文件路径
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now)
