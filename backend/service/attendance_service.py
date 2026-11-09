"""考勤业务层（对应 Java 的 @Service）

核心职责：
1. 识别：上传图片 → insightface 提取向量 → Milvus 检索找人
2. 判定：相似度 >= 阈值才算匹配；按时间规则判定 normal/late/early
3. 落库：写 attendance 表（事务边界在 Service 层）
"""
from __future__ import annotations

from datetime import datetime, date

import numpy as np
import cv2
from sqlalchemy.orm import Session

from models import Student, Attendance
from repository import AttendanceRepository, StudentRepository
from schemas import CheckinResult
from core import milvus
from core.face_engine import extract_face_info
from core.config import ATTENDANCE_THRESHOLD, CHECKIN_DEADLINE, CHECKOUT_START


class AttendanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AttendanceRepository(db)
        self.student_repo = StudentRepository(db)

    def checkin(self, image_bytes: bytes, check_type: str = "checkin") -> CheckinResult:
        """签到/签退主流程：
        图片字节 → 解码 → 提取向量 → Milvus 检索 → 阈值判定 → 时间规则 → 落库
        """
        # 1. 字节转图片
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return CheckinResult(matched=False, reason="图片格式无法解析")

        # 2. 提取人脸向量（复用现有 face_engine）
        result = extract_face_info(img)
        if not result["detected"]:
            return CheckinResult(matched=False, reason=result["reason"])

        # 3. Milvus 检索最相似的人脸
        hits = milvus.search_face(result["embedding"], top_k=1)
        if not hits:
            return CheckinResult(matched=False, reason="脸库为空，请先录入学生人脸")
        best = hits[0]
        similarity = best["distance"]  # COSINE 度量下 distance 即相似度(0~1)

        # 4. 阈值判定
        if similarity < ATTENDANCE_THRESHOLD:
            return CheckinResult(matched=False, reason="未匹配到该学生，请重新采集或先录入人脸")

        # 5. 查出学生
        student = self.student_repo.get_by_id(best["student_id"])
        if not student:
            return CheckinResult(matched=False, reason="学生记录不存在")

        # 6. 防重复：当天同类型只允许一次
        if self.repo.has_today_record(student.id, check_type):
            label = "签到" if check_type == "checkin" else "签退"
            return CheckinResult(matched=False, reason=f"该学生今天已{label}，无需重复")

        # 7. 时间规则判定状态
        status = self._judge_status(check_type)

        # 8. 落库
        attendance = Attendance(
            student_id=student.id,
            check_type=check_type,
            similarity=round(similarity, 4),
            status=status,
        )
        self.repo.create(attendance)
        self.db.commit()

        return CheckinResult(
            matched=True,
            student_id=student.id,
            student_name=student.name,
            student_no=student.student_no,
            similarity=round(similarity, 4),
            status=status,
            check_time=attendance.check_time,
        )

    @staticmethod
    def _judge_status(check_type: str) -> str:
        """按当前时间判定考勤状态"""
        now = datetime.now().strftime("%H:%M")
        if check_type == "checkin":
            # 晚于签到截止时间 = 迟到
            return "late" if now > CHECKIN_DEADLINE else "normal"
        else:
            # 早于签退起始时间 = 早退
            return "early" if now < CHECKOUT_START else "normal"

    def list_records(self, page: int, page_size: int, **filters) -> tuple[int, list[dict]]:
        """分页查询考勤记录（附学生姓名/学号）"""
        skip = (page - 1) * page_size
        total = self.repo.count(**filters)
        records = self.repo.search(skip=skip, limit=page_size, **filters)
        # 只查当前页涉及的学生，避免全量拉取
        student_ids = {r.student_id for r in records}
        student_map = {}
        if student_ids:
            student_map = {
                s.id: s for s in self.db.query(Student).filter(Student.id.in_(student_ids)).all()
            }
        items = []
        for r in records:
            s = student_map.get(r.student_id)
            items.append({
                "id": r.id,
                "student_id": r.student_id,
                "student_name": s.name if s else "?",
                "student_no": s.student_no if s else "?",
                "check_time": r.check_time,
                "check_type": r.check_type,
                "similarity": r.similarity,
                "status": r.status,
                "remark": r.remark,
            })
        return total, items

    def today_stats(self) -> dict:
        """今日考勤统计：应到/实到/缺勤/出勤率"""
        from sqlalchemy import func

        total_students = self.student_repo.count() or 0

        # 今天有签到记录的学生（去重）
        today = date.today()
        start = datetime(today.year, today.month, today.day)
        checked_in = self.db.query(func.count(func.distinct(Attendance.student_id))).filter(
            Attendance.check_time >= start,
            Attendance.check_type == "checkin",
        ).scalar() or 0

        absent = max(total_students - checked_in, 0)
        rate = round(checked_in / total_students, 4) if total_students else 0.0

        return {
            "total_students": total_students,
            "checked_in": checked_in,
            "absent": absent,
            "attendance_rate": rate,
        }
