"""学生表 ORM 实体（对应 students 表 / Java @Entity）"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Student(Base):
    """学生实体：一行 = 一个学生

    说明：本类只做 ORM 映射，不负责建表——建表 SQL 以 data/schema.sql 为唯一来源。
    因此 gender / age 的 CHECK 约束写在 schema.sql 里，这里仅保留同义注释。
    """

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)   # 学号(唯一)
    name: Mapped[str] = mapped_column(String(50), nullable=False)                      # 姓名
    gender: Mapped[str | None] = mapped_column(String(10))                             # 性别(只能男/女，DB CHECK)
    age: Mapped[int | None] = mapped_column(Integer)                                   # 年龄(18~28，DB CHECK)
    class_name: Mapped[str | None] = mapped_column(String(50))                         # 班级(程序枚举约束)
    major: Mapped[str | None] = mapped_column(String(50))                              # 专业(程序枚举约束)
    enroll_year: Mapped[int | None] = mapped_column(Integer)                           # 入学年份
    phone: Mapped[str | None] = mapped_column(String(20))                              # 联系方式
    face_status: Mapped[int] = mapped_column(Integer, default=0, nullable=False)       # 人脸录入状态 0未录/1已录
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
