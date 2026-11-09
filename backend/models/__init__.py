"""models 包统一导出，方便外部 from models import Student / Face / Notice / Attendance"""
from .base import Base
from .student import Student
from .face import Face
from .notice import Notice
from .attendance import Attendance

__all__ = ["Base", "Student", "Face", "Notice", "Attendance"]
