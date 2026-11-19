"""生成压测用的基准数据集（独立文件 data/bench.db，不碰真实 db.sqlite）。

用法：
    .venv/Scripts/python.exe tools/bench_seed.py --students 500 --days 20

生成内容：
    - 500 名学生（10 个班、3 个专业，约 80% 标记为已录入人脸）
    - 20 天 × 500 人 × 2 次的考勤记录（签到 + 签退）
    - 50 条公告

为什么要单独一个库：
    压测要造大量数据，直接写真实库会污染已有数据；
    配置支持 DATABASE_URL 环境变量后，压测跑在 bench.db 上即可。
"""
import argparse
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA = BASE_DIR / "data" / "schema.sql"
BENCH_DB = BASE_DIR / "data" / "bench.db"

SURNAMES = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
GIVEN = "伟芳娜秀英敏静丽强磊洋艳勇军杰娟涛明超秀霞平刚桂英"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--students", type=int, default=500)
    ap.add_argument("--days", type=int, default=20)
    ap.add_argument("--reset", action="store_true", help="先删掉旧 bench.db")
    args = ap.parse_args()

    if args.reset and BENCH_DB.exists():
        BENCH_DB.unlink()
    BENCH_DB.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(BENCH_DB)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))

    classes = [f"计算机{c}班" for c in ["2301", "2302", "2303", "2304", "2305"]]
    majors = ["计算机科学与技术", "软件工程", "数据科学与大数据技术"]

    students = []
    for i in range(1, args.students + 1):
        no = f"2023{i:04d}"
        name = SURNAMES[i % len(SURNAMES)] + GIVEN[i % len(GIVEN)]
        students.append((
            no, name,
            "男" if i % 2 else "女",
            18 + i % 5,
            classes[i % len(classes)],
            majors[i % len(majors)],
            2023,
            f"138{i:08d}",
            1 if i % 5 != 0 else 0,
        ))
    conn.executemany(
        "INSERT INTO students (student_no,name,gender,age,class_name,major,enroll_year,phone,face_status) "
        "VALUES (?,?,?,?,?,?,?,?,?)", students
    )

    # 考勤：每天每人一条签到 + 一条签退
    rows = []
    for d in range(args.days):
        date = f"2026-10-{d % 28 + 1:02d}"
        for sid in range(1, args.students + 1):
            late = "late" if sid % 17 == 0 else "normal"
            rows.append((sid, f"{date} 08:{sid % 50:02d}:00", "checkin", 0.5 + (sid % 40) / 100, late, None))
            rows.append((sid, f"{date} 18:{sid % 50:02d}:00", "checkout", 0.5 + (sid % 40) / 100, "normal", None))
    conn.executemany(
        "INSERT INTO attendance (student_id,check_time,check_type,similarity,status,remark) "
        "VALUES (?,?,?,?,?,?)", rows
    )

    notices = [(f"第{i}周考勤安排", f"本周考勤说明内容 {i}", "教务") for i in range(1, 51)]
    conn.executemany(
        "INSERT INTO notices (title,content,publisher) VALUES (?,?,?)", notices
    )

    conn.commit()
    n_stu = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    n_att = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    conn.close()
    size_mb = BENCH_DB.stat().st_size / 1024 / 1024
    print(f"bench.db 就绪：学生 {n_stu} 条，考勤 {n_att} 条，公告 50 条，{size_mb:.1f} MB")


if __name__ == "__main__":
    main()
