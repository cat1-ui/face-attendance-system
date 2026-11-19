"""业务层 - 对应 Java 的 @Service

职责：业务逻辑、编排 Repository、事务边界（commit 在这里，不在 Repository）。
控制层（api）只调这里，不直接碰数据库。
"""
from __future__ import annotations

import os
import time

from sqlalchemy.orm import Session

from models import Student, Face, Notice
from repository import StudentRepository, FaceRepository, NoticeRepository
from schemas import StudentCreate, StudentUpdate, StudentOut
from core import milvus
from core.face_engine import extract_face_info
from core.config import FACE_IMAGE_DIR, MILVUS_COLLECTION


class StudentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = StudentRepository(db)
        self.face_repo = FaceRepository(db)

    def create(self, dto: StudentCreate) -> StudentOut:
        # ① 业务规则：学号查重
        if self.repo.get_by_student_no(dto.student_no):
            raise ValueError(f"学号 {dto.student_no} 已存在")
        # ② DTO → 实体
        student = Student(**dto.model_dump())
        # ③ 编排 repository（add + flush）
        self.repo.create(student)
        # ④ 事务提交
        self.db.commit()
        # ⑤ 实体 → DTO 返回
        return StudentOut.model_validate(student)

    def get(self, sid: int) -> StudentOut | None:
        student = self.repo.get_by_id(sid)
        return StudentOut.model_validate(student) if student else None

    def list(self, page: int, page_size: int, **filters) -> tuple[int, list[StudentOut]]:
        skip = (page - 1) * page_size
        total = self.repo.count(**filters)
        students = self.repo.search(skip=skip, limit=page_size, **filters)
        return total, [StudentOut.model_validate(s) for s in students]

    def update(self, sid: int, dto: StudentUpdate) -> StudentOut | None:
        student = self.repo.get_by_id(sid)
        if not student:
            return None
        # 只改传了的字段（学号不可改，schema 已不含该字段），靠 dirty tracking 自动 UPDATE
        for field in ("name", "gender", "age", "class_name", "major", "enroll_year", "phone"):
            value = getattr(dto, field)
            if value is not None:
                setattr(student, field, value)
        self.db.commit()
        self.db.refresh(student)
        return StudentOut.model_validate(student)

    def import_students(self, rows: list[dict]) -> dict:
        """批量导入：逐行校验学号查重 + 字段合法性，返回成功/失败统计

        rows: 每行是 {student_no, name, gender, age, class_name, major, enroll_year, phone}
        校验规则与单条新增保持一致：性别只能男/女，年龄 18~28
        """
        success = 0
        skipped = 0
        errors = []
        for idx, row in enumerate(rows, start=1):
            student_no = row.get("student_no")
            name = row.get("name")
            # 校验必填
            if not student_no or not name:
                skipped += 1
                errors.append(f"第{idx}行缺少学号或姓名")
                continue
            # 校验性别：留空可接受，填了就必须是男/女
            gender = row.get("gender")
            if gender in (None, ""):
                row["gender"] = gender = None
            elif gender not in ("男", "女"):
                skipped += 1
                errors.append(f"第{idx}行性别「{gender}」不合法，只能是男/女")
                continue
            # 校验年龄：留空可接受，填了就必须在 18~28
            age = row.get("age")
            if age is not None and not (18 <= age <= 28):
                skipped += 1
                errors.append(f"第{idx}行年龄「{age}」超出 18~28 范围")
                continue
            # 学号查重（数据库内 + 本次批次内）
            if self.repo.get_by_student_no(student_no):
                skipped += 1
                errors.append(f"学号 {student_no} 已存在")
                continue
            student = Student(**row)
            self.repo.create(student)
            success += 1
        self.db.commit()
        return {"success": success, "skipped": skipped, "errors": errors}

    def delete(self, sid: int):
        """级联删除：SQLite + Milvus + 磁盘文件 三处同步（难点 #5）"""
        student = self.repo.get_by_id(sid)
        if not student:
            return False

        # 1. 查出该学生所有脸照（删除前先收集，删完 SQLite 记录就找不到了）
        faces = self.face_repo.list_by_student(sid)

        # 2. 删 Milvus 向量
        if faces:
            face_ids = [f.face_id for f in faces]
            milvus.get_milvus().delete(
                collection_name=MILVUS_COLLECTION,
                ids=face_ids,
            )

        # 3. 删磁盘脸照文件
        for f in faces:
            if f.image_path and os.path.exists(f.image_path):
                os.remove(f.image_path)

        # 4. 删 SQLite 学生记录（faces 由 ORM 级联自动删）
        self.repo.delete(sid)
        self.db.commit()  # 事务边界：Service 层提交
        return True


class FaceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FaceRepository(db)
        self.student_repo = StudentRepository(db)

    def enroll(self, student_id: int, image_bytes: bytes, filename: str):
        """人脸录入主流程：
        图片字节 → OpenCV 解码 → insightface 检测 → 三处落库

        约束：每个学生只允许录 1 张脸照，已有脸照则拒绝（需先删除再重录）。
        """
        import numpy as np
        import cv2

        # 0. 校验学生是否存在
        student = self.student_repo.get_by_id(student_id)
        if not student:
            return {"detected": False, "face_id": None, "image_path": None, "reason": "学生不存在"}

        # 0.5 限制每人只录 1 张脸：已有脸照则拒绝（先查，省去后续无谓的解码/检测）
        existing = self.repo.list_by_student(student_id)
        if existing:
            return {"detected": False, "face_id": None, "image_path": None,
                    "reason": "该学生已录入人脸，请先删除旧脸照再重新录入"}

        # 1. 字节转 numpy 数组，再解码成 BGR 图片
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return {"detected": False, "face_id": None, "image_path": None, "reason": "图片格式无法解析"}

        # 2. insightface 检测 + 提取 512 维向量
        result = extract_face_info(img)
        if not result["detected"]:
            return {"detected": False, "face_id": None, "image_path": None, "reason": result["reason"]}

        # 3. 生成 face_id 和保存路径（按学号分目录）
        face_id = self.repo.next_face_id()
        student_dir = FACE_IMAGE_DIR / student.student_no
        student_dir.mkdir(parents=True, exist_ok=True)
        # 文件命名：face_id + 时间戳，避免重名
        ext = os.path.splitext(filename)[1] or ".jpg"
        image_path = student_dir / f"{face_id}_{int(time.time())}{ext}"

        # 4. 存磁盘文件
        cv2.imwrite(str(image_path), img)

        # 5. 存 SQLite 元数据
        face = Face(student_id=student_id, face_id=face_id, image_path=str(image_path))
        self.repo.create(face)

        # 6. 更新学生的人脸录入状态
        student.face_status = 1

        # 7. 事务边界：Service 层统一提交（先提交 ORM，释放 SQLite 写锁）
        self.db.commit()

        # 8. 存向量（在 ORM commit 之后写，避免两个连接并发写 SQLite 导致 database is locked）
        milvus.get_milvus().insert(
            collection_name=MILVUS_COLLECTION,
            data=[{
                "face_id": face_id,
                "student_id": student_id,
                "embedding": result["embedding"],
                "created_at": int(time.time()),
            }],
        )

        return {"detected": True, "face_id": face_id, "image_path": str(image_path), "reason": None}

    def list_faces(self, student_id: int):
        return self.repo.list_by_student(student_id)

    def delete_face(self, face_id: int):
        """删单张脸照：三处同步（向量库 / 磁盘 / SQLite），并回写学生的录入状态

        为什么要回写 face_status：
            它是为了省一次 join 而冗余在学生表上的字段，统计接口直接读它算覆盖率。
            如果只删脸照不动它，就会出现「统计说已录入 1 人，实际一张照片都没有」
            的不一致——冗余字段必须由唯一的数据源（faces 表）驱动更新。
        """
        face = self.repo.get_by_face_id(face_id)
        if not face:
            return False

        student_id = face.student_id

        # 删 Milvus（本地 numpy 实现，向量存 face_vectors 表）
        milvus.get_milvus().delete(collection_name=MILVUS_COLLECTION, ids=[face_id])
        # 删磁盘
        if face.image_path and os.path.exists(face.image_path):
            os.remove(face.image_path)
        # 删 SQLite
        self.repo.delete_by_face_id(face_id)
        # 注意：Session 是 autoflush=False 建的，session.delete() 只做标记，
        # 不 flush 的话下面那条 "还剩几张" 的查询看不到这次删除，会误判成还有脸照
        self.db.flush()

        # 该学生已无任何脸照 → 状态回写为未录入
        if not self.repo.list_by_student(student_id):
            student = self.student_repo.get_by_id(student_id)
            if student:
                student.face_status = 0

        self.db.commit()  # 事务边界：Service 层提交，四处改动要么一起成功要么都不生效
        return True


class NoticeService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NoticeRepository(db)

    def create(self, data: dict) -> Notice:
        notice = Notice(**data)
        result = self.repo.create(notice)
        self.db.commit()
        return result

    def get(self, nid: int):
        return self.repo.get_by_id(nid)

    def list(self, page: int, page_size: int):
        skip = (page - 1) * page_size
        total = self.repo.count()
        items = self.repo.list_all(skip=skip, limit=page_size)
        return total, items

    def update(self, nid: int, data: dict):
        notice = self.repo.get_by_id(nid)
        if not notice:
            return None
        for k, v in data.items():
            if v is not None:
                setattr(notice, k, v)
        self.db.commit()
        self.db.refresh(notice)
        return notice

    def delete(self, nid: int):
        notice = self.repo.get_by_id(nid)
        if not notice:
            return False
        self.repo.delete(nid)
        self.db.commit()
        return True
