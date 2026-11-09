"""测试用例 demo：验证数据层 CRUD 真实落库

覆盖增(Create) / 查(Read) / 改(Update) / 删(Delete) 四步，
并演示 ORM 铁律：改属性 + commit 自动生成 UPDATE（dirty tracking）。

运行方式（在 backend 目录下）：
    .venv/Scripts/python.exe test/demo.py
"""
import sys
from pathlib import Path

# 项目根目录加入 sys.path，保证 from models / core / repository 能正常导入
# 注意：这行必须在所有项目模块 import 之前
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import Student
from core.db import SessionLocal
from repository import StudentRepository


def test_create():
    """增：构造实体 + create + commit"""
    db = SessionLocal()
    try:
        repo = StudentRepository(db)
        student = Student(
            student_no="2025090101", name="张三", gender="男",
            class_name="计算机1班", major="计算机科学与技术",
            enroll_year=2025, phone="13800138000", face_status=0,
        )
        repo.create(student)   # add + flush（不 commit）
        db.commit()            # 真正落库
        print(f"[PASS] 新增成功 id={student.id}")
    finally:
        db.close()


def test_read():
    """查：四种查询"""
    db = SessionLocal()
    try:
        repo = StudentRepository(db)
        s1 = repo.get_by_student_no("2025090101")
        print(f"[PASS] 按学号查: {s1.name if s1 else '无'}")

        all_students = repo.list_all(skip=0, limit=100)
        print(f"[PASS] 全查询: 共 {len(all_students)} 人")

        searched = repo.search(keyword="张")
        print(f"[PASS] 搜索'张': {len(searched)} 人")
    finally:
        db.close()


def test_update():
    """改：查出对象 + 改属性 + commit（dirty tracking 自动 UPDATE）"""
    db = SessionLocal()
    try:
        repo = StudentRepository(db)
        s = repo.get_by_student_no("2025090101")
        print(f"[查询] 修改前: 姓名={s.name}")
        s.name = "赵六"      # 改属性，标记 dirty
        db.commit()          # 自动生成 UPDATE
        print(f"[PASS] 修改后: 姓名={s.name}")

        # commit 后对象过期，重新查验证
        db.expire_all()
        s2 = repo.get_by_student_no("2025090101")
        print(f"[验证] 重新查: 姓名={s2.name}")
    finally:
        db.close()


def test_delete():
    """删：按主键删 + commit"""
    db = SessionLocal()
    try:
        repo = StudentRepository(db)
        s = repo.get_by_student_no("2025090101")
        if s:
            repo.delete(s.id)
            db.commit()
            print("[PASS] 删除成功")
    finally:
        db.close()


if __name__ == "__main__":
    print("===== 增 =====")
    test_create()
    print("===== 查 =====")
    test_read()
    print("===== 改 =====")
    test_update()
    print("===== 删 =====")
    test_delete()
    print("===== 删后全查询 =====")
    db = SessionLocal()
    try:
        repo = StudentRepository(db)
        print(f"剩余学生数: {len(repo.list_all(skip=0, limit=100))}")
    finally:
        db.close()
    print("===== 全部测试完成 =====")
