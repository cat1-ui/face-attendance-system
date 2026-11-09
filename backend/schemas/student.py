"""学生 DTO（对应 DTO/VO，接口合同）

字段级校验（第二道防线，第一道在 data/schema.sql 的 CHECK）：
- gender：只允许「男」/「女」（Literal 枚举，其它值直接 422）
- age：18 ~ 28（Field 区间校验）
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StudentBase(BaseModel):
    """学生公共字段（新增/更新/返回共用）"""

    student_no: str
    name: str
    gender: Literal["男", "女"] | None = None      # 只能男/女
    age: int | None = Field(default=None, ge=18, le=28)  # 18~28
    class_name: str | None = None
    major: str | None = None
    enroll_year: int | None = None
    phone: str | None = None


class StudentCreate(StudentBase):
    """新增学生请求体：前端不传 face_status / 时间戳，由后端算"""


class StudentUpdate(BaseModel):
    """更新学生请求体：字段可选（不传不改），学号不可改（唯一键）"""

    name: str | None = None
    gender: Literal["男", "女"] | None = None
    age: int | None = Field(default=None, ge=18, le=28)
    class_name: str | None = None
    major: str | None = None
    enroll_year: int | None = None
    phone: str | None = None


class StudentOut(StudentBase):
    """查询学生返回体：含系统字段"""

    model_config = ConfigDict(from_attributes=True)  # 允许从 ORM 对象直接转换
    id: int
    face_status: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
