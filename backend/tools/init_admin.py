"""创建/重置登录账号。

用法：
    .venv/Scripts/python.exe tools/init_admin.py
    .venv/Scripts/python.exe tools/init_admin.py --username admin --password Admin@12345 --role admin

注意：
- 密码用 bcrypt 哈希后入库，命令行明文不会落盘
- 用户名已存在时默认报错；加 --reset 可重置该用户密码
- 生产环境请务必改掉默认密码，并通过环境变量 JWT_SECRET 设置签名密钥
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.db import SessionLocal  # noqa: E402
from core.security import hash_password  # noqa: E402
from models import User  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--username", default="admin")
    ap.add_argument("--password", default="Admin@12345")
    ap.add_argument("--role", default="admin", choices=["admin", "viewer"])
    ap.add_argument("--reset", action="store_true", help="用户已存在时重置密码与角色")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == args.username).first()
        if user and not args.reset:
            print(f"用户「{args.username}」已存在。若要重置密码请加 --reset")
            return
        if user:
            user.password_hash = hash_password(args.password)
            user.role = args.role
            print(f"已重置用户「{args.username}」的密码，角色 {args.role}")
        else:
            db.add(User(
                username=args.username,
                password_hash=hash_password(args.password),
                role=args.role,
            ))
            print(f"已创建用户「{args.username}」，角色 {args.role}")
        db.commit()
        print(f"登录密码：{args.password}（请尽快修改）")
    finally:
        db.close()


if __name__ == "__main__":
    main()
