"""鉴权端到端自检（经 Nginx，覆盖登录/401/403/WebSocket）

覆盖：登录 / 未登录拒绝 / 伪造 token / 角色权限 / WebSocket 鉴权
密码运行时随机生成，不硬编码；跑完自动删除临时账号。
用法：先 docker compose up -d，再执行本脚本。

关键点：账号在**容器内**创建（docker exec），而不是在宿主机写库。
原因：Windows 绑定挂载下，容器已建立的 SQLite 连接看不到宿主新写入的行，
宿主灌数据必须重启容器；而在容器内写入，应用下次查询就能读到，省掉重启。
"""
import random
import string
import subprocess
import time

import requests
import websocket

BASE = "http://127.0.0.1:8080"
WS_BASE = "ws://127.0.0.1:8080/ws/notices"
CONTAINER = "attendance-backend"

SEED_SNIPPET = """
import sys
from core.db import SessionLocal
from core.security import hash_password
from models import User
u, p, r = sys.argv[1], sys.argv[2], sys.argv[3]
db = SessionLocal()
x = db.query(User).filter(User.username == u).first()
if x:
    x.password_hash, x.role = hash_password(p), r
else:
    db.add(User(username=u, password_hash=hash_password(p), role=r))
db.commit()
db.close()
print("seeded")
"""

DELETE_SNIPPET = """
from core.db import SessionLocal
from models import User
db = SessionLocal()
n = db.query(User).filter(User.username.in_(["e2e_admin", "e2e_view"])).delete(synchronize_session=False)
db.commit()
db.close()
print("deleted", n)
"""

ok = fail = 0


def check(desc, cond):
    global ok, fail
    print(("  [PASS] " if cond else "  [FAIL] ") + desc)
    if cond:
        ok += 1
    else:
        fail += 1


def gen_pw(n=16):
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(n))


def docker_py(snippet, *args):
    r = subprocess.run(["docker", "exec", CONTAINER, "python", "-c", snippet, *args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"容器内执行失败: {r.stderr[-400:]}")
    return r.stdout.strip()


def login_retry(u, p, tries=10, gap=2):
    last = ""
    for _ in range(tries):
        try:
            r = requests.post(f"{BASE}/api/auth/login-json", json={"username": u, "password": p}, timeout=10)
            if r.headers.get("content-type", "").startswith("application/json"):
                return r
            last = f"{r.status_code} {r.text[:60]}"
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(gap)
    raise RuntimeError(f"登录接口不可用：{last}")


def main():
    pw_a, pw_v = gen_pw(), gen_pw()
    docker_py(SEED_SNIPPET, "e2e_admin", pw_a, "admin")
    docker_py(SEED_SNIPPET, "e2e_view", pw_v, "viewer")
    try:
        r = login_retry("e2e_admin", gen_pw())
        check(f"错误密码被拒 401（实得 {r.status_code}）", r.status_code == 401)

        r = login_retry("e2e_admin", pw_a)
        check(f"admin 登录成功 200（实得 {r.status_code}）", r.status_code == 200)
        token = r.json()["data"]["access_token"]

        r = requests.get(f"{BASE}/api/students", params={"page": 1, "page_size": 1}, timeout=10)
        check(f"未登录访问 401（实得 {r.status_code}）", r.status_code == 401)

        r = requests.get(f"{BASE}/api/students", headers={"Authorization": "Bearer x.y.z"}, timeout=10)
        check(f"伪造 token 401（实得 {r.status_code}）", r.status_code == 401)

        h = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE}/api/students", params={"page": 1, "page_size": 1}, headers=h, timeout=10)
        check(f"admin 读取 200（实得 {r.status_code}）", r.status_code == 200)

        r = requests.get(f"{BASE}/health", timeout=10)
        check("Nginx 转发 /health 返回 JSON", r.status_code == 200 and r.json().get("status") == "ok")

        rv = login_retry("e2e_view", pw_v)
        vtoken = rv.json()["data"]["access_token"]
        hv = {"Authorization": f"Bearer {vtoken}"}
        r = requests.post(f"{BASE}/api/students", json={"student_no": "E2E9", "name": "t"}, headers=hv, timeout=10)
        check(f"viewer 写操作 403（实得 {r.status_code}）", r.status_code == 403)
        r = requests.get(f"{BASE}/api/students", params={"page": 1, "page_size": 1}, headers=hv, timeout=10)
        check(f"viewer 读操作 200（实得 {r.status_code}）", r.status_code == 200)

        try:
            ws = websocket.create_connection(WS_BASE, timeout=6)
            ws.close()
            check("WS 无 token 应被拒，实际却连上了", False)
        except Exception:
            check("WS 无 token 被拒", True)

        try:
            ws = websocket.create_connection(f"{WS_BASE}?token={token}", timeout=6)
            ws.send('{"type":"pong"}')
            msg = ws.recv()
            ws.close()
            check(f"WS 带 token 握手并通信成功（收到 {msg}）", "ping" in msg)
        except Exception as e:
            check(f"WS 带 token 失败：{type(e).__name__} {e}", False)
    finally:
        try:
            docker_py(DELETE_SNIPPET)
        except Exception as e:
            print("  清理临时账号失败:", e)
        print(f"\n结果：{ok} 通过 / {fail} 失败")


if __name__ == "__main__":
    main()
