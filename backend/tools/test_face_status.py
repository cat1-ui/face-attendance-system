"""删脸照后 face_status 回写的回归测试（用临时库，不碰真实数据）

为什么单独建库：不能拿真实 db.sqlite 做删改实验。
用法：.venv/Scripts/python.exe tools/test_face_status.py
做法：把 schema.sql 落到临时库，造一个学生 + 一张脸照，调用真实的 FaceService.delete_face。
"""
import os
import pathlib
import sys
import tempfile

BACKEND = pathlib.Path(r"D:/project/face_attendance_system/backend")
os.chdir(BACKEND)
sys.path.insert(0, str(BACKEND))

tmp_db = pathlib.Path(tempfile.gettempdir()) / "attendance_test_facestatus.db"
if tmp_db.exists():
    tmp_db.unlink()

# 必须先设 DATABASE_URL，再 import core.db（引擎在导入时创建）
os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db}"

import sqlite3  # noqa: E402

conn = sqlite3.connect(tmp_db)
conn.executescript((BACKEND / "data" / "schema.sql").read_text(encoding="utf-8"))
conn.execute(
    "INSERT INTO students (student_no,name,gender,age,class_name,major,enroll_year,phone,face_status) "
    "VALUES ('TEST001','测试学生','男',20,'测试班','软件工程',2023,'13800000000',1)"
)
conn.execute(
    "INSERT INTO faces (face_id, student_id, image_path) VALUES (9001, 1, NULL)"
)
conn.commit()
conn.close()

from core.db import SessionLocal  # noqa: E402
from models import Student  # noqa: E402
from service.service import FaceService  # noqa: E402

ok = fail = 0


def check(desc, cond):
    global ok, fail
    print(("  [PASS] " if cond else "  [FAIL] ") + desc)
    ok, fail = (ok + 1, fail) if cond else (ok, fail + 1)


def main():
    db = SessionLocal()
    try:
        s = db.query(Student).first()
        check(f"初始 face_status=1（实得 {s.face_status}）", s.face_status == 1)

        deleted = FaceService(db).delete_face(9001)
        check("delete_face 返回 True", deleted is True)

        db.expire_all()
        s = db.query(Student).first()
        check(f"删除后 face_status 回写为 0（实得 {s.face_status}）", s.face_status == 0)

        # 再删一次：不存在应返回 False，且不能报错、不能把状态改乱
        check("重复删除返回 False", FaceService(db).delete_face(9001) is False)
        db.expire_all()
        check("重复删除后状态仍为 0", db.query(Student).first().face_status == 0)
    finally:
        db.close()
        # Windows 下 SQLite 文件被连接池占用时无法删除，必须先释放引擎
        from core.db import engine

        engine.dispose()
        try:
            if tmp_db.exists():
                tmp_db.unlink()
        except PermissionError:
            pass
        print(f"\n结果：{ok} 通过 / {fail} 失败")


if __name__ == "__main__":
    main()
