"""公告 DTO（对应 DTO/VO）"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NoticeBase(BaseModel):
    """公告公共字段"""

    title: str
    content: str | None = None
    publisher: str | None = None


class NoticeCreate(NoticeBase):
    """新增公告请求体"""


class NoticeUpdate(BaseModel):
    """更新公告请求体：所有字段可选（支持部分更新）"""

    title: str | None = None
    content: str | None = None
    publisher: str | None = None


class NoticeOut(NoticeBase):
    """查询公告返回体"""

    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime | None = None
