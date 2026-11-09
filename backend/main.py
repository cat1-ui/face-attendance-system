"""入口文件 - 装配路由 + 中间件 + 启动事件

启动时做三件事：
1. 建表（执行 data/schema.sql 手写 SQL，表结构唯一来源）
2. 加载枚举（pandas 读 CSV）
3. 预热 insightface 模型单例（避免首次请求卡顿）
"""
from contextlib import asynccontextmanager
import os

# 关键：必须先于 pandas 加载 onnxruntime，避免 Windows 下
# onnxruntime 与 pyarrow（pandas 间接依赖）的 C++ DLL 冲突
# （先加载 pandas 会导致 onnxruntime 的 onnxruntime_pybind11_state DLL 初始化失败）
import onnxruntime  # noqa: F401

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core import enums
from common import register_exceptions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化，关闭时清理"""
    # 建表：用 tools/init_db.py 执行手写 schema.sql（幂等，表已存在则跳过）
    from tools.init_db import init_db
    init_db()
    # 加载枚举
    enums.load_enums()
    print(f"[启动] 班级枚举: {enums.CLASSES}")
    print(f"[启动] 专业枚举: {enums.MAJORS}")
    # 预热 insightface 模型（后台加载，避免首次请求卡几秒）
    try:
        from core.face_engine import get_face_engine
        get_face_engine()
        print("[启动] insightface 模型加载完成")
    except Exception as e:
        print(f"[警告] insightface 模型加载失败: {e}")
    yield
    # 关闭时无需特殊处理，SQLite 自动关闭


app = FastAPI(title="学生刷脸考勤系统", version="1.0.0", lifespan=lifespan)

# 跨域配置：只放行前端 dev 服务器（默认 Vite 5173）
# 换域名/端口时用环境变量 ALLOW_ORIGINS 覆盖，逗号分隔
ALLOW_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOW_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    # 接口不依赖 Cookie/凭据；开着 credentials 又配 "*" 属于无效且危险的组合
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 注册全局异常处理器（三层兜底）
register_exceptions(app)

# 注册路由
from api import students, faces, misc, stats, ws, attendance
app.include_router(students.router)
app.include_router(faces.router)
app.include_router(misc.router)
app.include_router(stats.router)
app.include_router(ws.router)
app.include_router(attendance.router)


@app.get("/")
def root():
    return {"code": 0, "message": "学生刷脸考勤系统后端运行中", "data": None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
