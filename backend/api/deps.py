"""依赖注入 - 对应 Java 的 @Autowired

把 Service 实例注入到路由函数里。
FastAPI 的 Depends 会自动处理数据库会话的打开/关闭。
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from core.db import get_db
from service.service import StudentService, FaceService, NoticeService
from service.attendance_service import AttendanceService


def get_student_service(db: Session = Depends(get_db)) -> StudentService:
    return StudentService(db)


def get_face_service(db: Session = Depends(get_db)) -> FaceService:
    return FaceService(db)


def get_notice_service(db: Session = Depends(get_db)) -> NoticeService:
    return NoticeService(db)


def get_attendance_service(db: Session = Depends(get_db)) -> AttendanceService:
    return AttendanceService(db)
