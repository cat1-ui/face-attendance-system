# 后端镜像：多阶段构建
#   阶段 1（builder）：干净 venv 里装全部依赖（含 insightface 的 C 扩展编译）
#   阶段 2（runtime）：只带运行库和 venv，镜像里不留 gcc / 头文件
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 用独立 venv 而不是 --prefix：
# pip 会跳过"当前环境里已满足"的依赖，用 --prefix 时 numpy 这类
# 被前置安装过的包会漏装，导致运行期 import numpy 失败
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build

# insightface 的 sdist 构建时 import numpy 和 cython，必须先装
RUN pip install --no-cache-dir numpy==1.26.4 cython

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Debian 官方源在国内极慢（实测 apt 这一步耗掉 22 分钟），换成清华镜像
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' \
        /etc/apt/sources.list.d/debian.sources 2>/dev/null || true

# opencv 需要 libgl / libglib，onnxruntime 需要 libgomp（OpenMP）
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY . .

EXPOSE 8000

# 单容器内 2 worker：本机压测 1 worker 在 10 并发下 P95 28ms，
# 4 worker 可降到 9ms，但每个 worker 独立加载一份 insightface 模型（约 360MB）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
