"""考勤记录表 ORM 实体（对应 attendance 表 / Java @Entity）"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Attendance(Base):
    """考勤实体：一行 = 一次打卡（签到或签退）"""

    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )                                                                          # 识别出的学生(级联删除)
    check_time: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now)   # 打卡时间
    check_type: Mapped[str] = mapped_column(String(10), default="checkin")      # checkin签到 / checkout签退
    similarity: Mapped[float | None] = mapped_column(Float)                     # 识别相似度(0~1)
    status: Mapped[str] = mapped_column(String(10), default="normal")           # normal正常/late迟到/early早退/absent缺勤
    remark: Mapped[str | None] = mapped_column(String(200))                     # 备注
