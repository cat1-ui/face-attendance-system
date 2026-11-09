"""repository 包统一导出"""
from .student_repo import StudentRepository
from .face_repo import FaceRepository
from .notice_repo import NoticeRepository
from .attendance_repo import AttendanceRepository

__all__ = ["StudentRepository", "FaceRepository", "NoticeRepository", "AttendanceRepository"]
