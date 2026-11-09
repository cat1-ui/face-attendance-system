"""考勤数据层（对应 @Repository）"""
from datetime import datetime, date, timedelta

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from models.attendance import Attendance
from models.student import Student


class AttendanceRepository:
    """考勤记录增查，不碰业务逻辑。session 由外部注入"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, attendance: Attendance) -> Attendance:
        """新增（不 commit，事务边界在 Service 层）"""
        self.session.add(attendance)
        self.session.flush()
        return attendance

    def get_by_id(self, attendance_id: int) -> Attendance | None:
        """按主键查询"""
        return self.session.get(Attendance, attendance_id)

    def list_all(self, skip: int = 0, limit: int = 20) -> list[Attendance]:
        """分页查询（按打卡时间倒序）"""
        return list(
            self.session.scalars(
                select(Attendance).order_by(Attendance.check_time.desc()).offset(skip).limit(limit)
            )
        )

    def search(self, skip: int = 0, limit: int = 20, **filters) -> list[Attendance]:
        """组合查询：可按学生、类型、状态、日期筛选"""
        stmt = select(Attendance)
        stmt = self._apply_filters(stmt, filters)
        stmt = stmt.order_by(Attendance.check_time.desc()).offset(skip).limit(limit)
        return list(self.session.scalars(stmt))

    def count(self, **filters) -> int:
        """统计总数（配合分页用）"""
        stmt = select(func.count(Attendance.id))
        stmt = self._apply_filters(stmt, filters)
        return self.session.scalar(stmt) or 0

    @staticmethod
    def _apply_filters(stmt, filters: dict):
        """过滤条件：student_id 精确、check_type/status 精确、日期范围"""
        student_id = filters.get("student_id")
        check_type = filters.get("check_type")
        status = filters.get("status")
        day = filters.get("day")  # 形如 "2026-10-12"

        if student_id is not None:
            stmt = stmt.where(Attendance.student_id == student_id)
        if check_type:
            stmt = stmt.where(Attendance.check_type == check_type)
        if status:
            stmt = stmt.where(Attendance.status == status)
        if day:
            # 按当天 00:00 ~ 次日 00:00 过滤
            d = datetime.strptime(day, "%Y-%m-%d")
            next_day = datetime(d.year, d.month, d.day) + timedelta(days=1)
            stmt = stmt.where(Attendance.check_time >= d, Attendance.check_time < next_day)
        return stmt

    def has_today_record(self, student_id: int, check_type: str) -> bool:
        """判断某学生当天是否已有某种打卡记录（签到/签退各一次，防重复）"""
        today = date.today()
        start = datetime(today.year, today.month, today.day)
        stmt = select(func.count(Attendance.id)).where(
            Attendance.student_id == student_id,
            Attendance.check_type == check_type,
            Attendance.check_time >= start,
        )
        return (self.session.scalar(stmt) or 0) > 0
