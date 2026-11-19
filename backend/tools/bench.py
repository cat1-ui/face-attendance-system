"""接口压测脚本（零额外依赖：requests + 标准库，不引 locust）。

用途：给简历拿真实数字——QPS、P50/P95/P99 延迟，而不是只写「23 个接口」。

用法：
    # 1) 造基准数据（独立库，不碰真实数据）
    .venv/Scripts/python.exe tools/bench_seed.py --students 500 --days 20

    # 2) 自动起服务 + 压测 + 关服务（推荐）
    .venv/Scripts/python.exe tools/bench.py --spawn --concurrency 20 --requests 2000

    # 也可以压已经在跑的服务
    .venv/Scripts/python.exe tools/bench.py --url http://127.0.0.1:8000 --concurrency 20

口径说明：
    - 先预热 100 次再计时，避免把首请求的模型/连接初始化算进去
    - QPS = 总请求数 / 总墙钟时间（含客户端排队，偏保守）
    - 延迟为客户端观测的端到端耗时（含网络与 JSON 解析）
"""
import argparse
import os
import platform
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
BENCH_DB = BASE_DIR / "data" / "bench.db"

# 只压只读接口：写接口（签到）要带人脸图片，且会改数据，单独处理
ENDPOINTS = [
    ("GET /api/students", "/api/students?page=1&page_size=20"),
    ("GET /api/students/{id}", "/api/students/1"),
    ("GET /api/attendance", "/api/attendance?page=1&page_size=20"),
    ("GET /api/attendance/stats", "/api/attendance/stats"),
    ("GET /api/stats/summary", "/api/stats/summary"),
    ("GET /api/stats/face-coverage", "/api/stats/face-coverage"),
    ("GET /api/notices", "/api/notices"),
    ("GET /api/enums", "/api/enums"),
]


def wait_ready(url, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if requests.get(f"{url}/api/enums", timeout=2).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def run_one(session, url, timeout=15):
    t0 = time.perf_counter()
    try:
        r = session.get(url, timeout=timeout)
        cost = (time.perf_counter() - t0) * 1000
        return r.status_code, cost
    except Exception:
        return -1, (time.perf_counter() - t0) * 1000


def pct(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    k = max(0, min(len(sorted_vals) - 1, int(round((len(sorted_vals) - 1) * p))))
    return sorted_vals[k]


def worker(url, n, barrier):
    """一个线程跑 n 次请求，复用同一个 Session（连接复用，避免把 TCP 握手算进延迟）"""
    out = []
    with requests.Session() as s:
        s.get(url, timeout=15)  # 每线程先建一次连接
        barrier.wait()          # 所有线程就绪后同时开跑，避免起跑时间差
        for _ in range(n):
            out.append(run_one(s, url))
    return out


def bench_endpoint(url, total, concurrency):
    per = max(1, total // concurrency)
    threads = concurrency if total >= concurrency else 1
    import threading
    barrier = threading.Barrier(threads)
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=threads) as pool:
        futures = [pool.submit(worker, url, per, barrier) for _ in range(threads)]
        results = [r for f in futures for r in f.result()]
    wall = time.perf_counter() - t0
    return results, wall


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8001")
    ap.add_argument("--concurrency", type=int, default=20)
    ap.add_argument("--requests", type=int, default=2000, help="每个接口的请求总数")
    ap.add_argument("--spawn", action="store_true", help="自动起 uvicorn（用 bench.db）再压")
    ap.add_argument("--workers", type=int, default=1, help="uvicorn worker 进程数（仅 --spawn 生效）")
    args = ap.parse_args()

    proc = None
    if args.spawn:
        if not BENCH_DB.exists():
            sys.exit("缺少 data/bench.db，请先跑 tools/bench_seed.py")
        env = dict(os.environ)
        env["DATABASE_URL"] = f"sqlite:///{BENCH_DB}"
        print(f"启动服务（bench.db 隔离库，{args.workers} worker）: {args.url}")
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8001",
             "--workers", str(args.workers)],
            cwd=BASE_DIR, env=env,
        )

    try:
        if not wait_ready(args.url):
            sys.exit("服务未就绪，压测中止")
        print("服务就绪，开始预热…")

        # 预热
        with requests.Session() as s:
            for name, path in ENDPOINTS:
                for _ in range(12):
                    run_one(s, args.url + path)

        print(f"线程数 {args.concurrency}，每接口 {args.requests} 次请求\n")
        header = f"{'端点':<28}{'请求':>6}{'错误':>6}{'P50/ms':>9}{'P95/ms':>9}{'P99/ms':>9}{'QPS':>8}"
        print(header)
        print("-" * len(header.encode("gbk", errors="ignore")))

        all_lat, all_err, all_n = [], 0, 0
        for name, path in ENDPOINTS:
            url = args.url + path
            results, wall = bench_endpoint(url, args.requests, args.concurrency)

            codes = [c for c, _ in results]
            lat = sorted(d for c, d in results if c == 200)
            err = sum(1 for c in codes if c != 200)
            qps = len(results) / wall
            print(f"{name:<28}{len(results):>6}{err:>6}"
                  f"{pct(lat, .50):>9.1f}{pct(lat, .95):>9.1f}{pct(lat, .99):>9.1f}{qps:>8.0f}")
            all_lat += lat
            all_err += err
            all_n += len(results)

        all_lat.sort()
        print("-" * 70)
        print(f"{'合计':<28}{all_n:>6}{all_err:>6}"
              f"{pct(all_lat, .50):>9.1f}{pct(all_lat, .95):>9.1f}{pct(all_lat, .99):>9.1f}")
        print(f"\n平均延迟 {statistics.mean(all_lat):.1f} ms   "
              f"CPU {os.cpu_count()} 核  {platform.system()} {platform.release()}  "
              f"Python {platform.python_version()}")
    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            print("服务已停止")


if __name__ == "__main__":
    main()
