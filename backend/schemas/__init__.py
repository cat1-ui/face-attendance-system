"""schemas 包统一导出"""
from .student import StudentBase, StudentCreate, StudentUpdate, StudentOut
from .face import FaceOut, FaceDetectResult
from .notice import NoticeBase, NoticeCreate, NoticeUpdate, NoticeOut
from .attendance import AttendanceCreate, AttendanceOut, CheckinResult

__all__ = [
    "StudentBase", "StudentCreate", "StudentUpdate", "StudentOut",
    "FaceOut", "FaceDetectResult",
    "NoticeBase", "NoticeCreate", "NoticeUpdate", "NoticeOut",
    "AttendanceCreate", "AttendanceOut", "CheckinResult",
]
