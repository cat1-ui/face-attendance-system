"""考勤 DTO（对应 DTO/VO）"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttendanceCreate(BaseModel):
    """新增考勤请求体（签到/签退共用）"""

    check_type: str = "checkin"   # checkin签到 / checkout签退


class AttendanceOut(BaseModel):
    """考勤记录返回体（含学生姓名/学号，方便前端直接展示）"""

    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    check_time: datetime | None = None
    check_type: str
    similarity: float | None = None
    status: str
    remark: str | None = None
    # 冗余学生信息（由 service 层填充，不从 ORM 直接来）
    student_name: str | None = None
    student_no: str | None = None


class CheckinResult(BaseModel):
    """签到/签退识别结果"""

    matched: bool                          # 是否识别出学生
    student_id: int | None = None
    student_name: str | None = None
    student_no: str | None = None
    similarity: float | None = None        # 相似度
    status: str | None = None              # normal/late/early
    check_time: datetime | None = None
    reason: str | None = None              # 未匹配时的提示
