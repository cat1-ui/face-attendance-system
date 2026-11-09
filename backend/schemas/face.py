"""脸照 DTO（对应 DTO/VO）"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FaceOut(BaseModel):
    """脸照对象（列表查询返回）"""

    model_config = ConfigDict(from_attributes=True)
    id: int
    face_id: int
    student_id: int
    image_path: str | None = None
    created_at: datetime | None = None


class FaceDetectResult(BaseModel):
    """人脸检测结果（上传脸照的响应）"""

    detected: bool
    face_id: int | None = None
    image_path: str | None = None
    reason: str | None = None
