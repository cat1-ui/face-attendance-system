# 学生刷脸考勤系统

单机部署的课堂考勤系统：学生信息管理 + 人脸录入 + 刷脸签到/签退 + 考勤统计。
后端 FastAPI 四层架构（api / service / repository / models），前端 Vue 3 + Element Plus。

## 功能

| 模块 | 说明 |
|---|---|
| 学生管理 | 增删改查、CSV 批量导入、按班级/专业筛选 |
| 人脸录入 | 上传照片 → insightface 检测并提取 512 维特征 → 三处落库（磁盘文件 / SQLite 元数据 / 向量表）；每人限一张，重录需先删除 |
| 刷脸签到 | 抓帧 → 提特征 → 余弦相似度比对 → 命中即写考勤，并通过 WebSocket 把结果实时推给前端 |
| 考勤记录 | 按日期、学号查询，区分正常 / 迟到 / 早退 |
| 信息汇总 | 出勤率、迟到次数、人脸录入覆盖率等图表 |
| 公告管理 | 发布与删除班级公告 |

## 技术栈

- 后端：Python 3.11 · FastAPI · SQLAlchemy 2.0 · SQLite · Pydantic v2
- 人脸：insightface（buffalo_l，512 维特征）+ onnxruntime（CPU）
- 向量检索：numpy 内存矩阵检索，向量持久化在 SQLite（实现说明见 `backend/core/milvus.py` 顶部注释）
- 前端：Vue 3 · Vite · Element Plus · ECharts · Pinia

规模：后端 2234 行（23 个 REST 接口 + 1 个 WebSocket）、4 张表；前端 1459 行 / 6 个页面。

## 目录结构

```text
backend/
  api/          路由层：students / faces / attendance / notices / stats / ws
  service/      业务逻辑与事务边界
  repository/   数据访问
  models/       SQLAlchemy ORM
  schemas/      Pydantic 出入参
  core/         配置、数据库会话、枚举、人脸引擎、向量检索、WS 管理器
  data/         schema.sql（建表脚本，唯一保留在仓库里的数据文件）
  tools/        建表与字段迁移脚本
frontend/src/
  views/        6 个页面
  api/          请求封装（走 vite 代理，不写死域名）
```

## 快速开始（Windows 单机）

### 1. 后端

```bat
cd backend
install.bat      :: 建虚拟环境 + 安装依赖
start.bat        :: 启动服务，接口文档 http://127.0.0.1:8000/docs
```

首次启动会自动执行 `data/schema.sql` 建表、加载枚举、预热 insightface 模型（buffalo_l 权重要联网下载，几百 MB，耗时取决于网络）。

### 2. 前端

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173，/api 由 vite 代理到 8000
```

## 配置

常量集中在 `backend/core/config.py`：识别阈值 0.45、签到截止 09:00、签退起始 18:00、数据库与脸照目录等。
跨域白名单可用环境变量 `ALLOW_ORIGINS` 覆盖（逗号分隔，默认只放行 `http://localhost:5173` 与 `http://127.0.0.1:5173`）。

## 数据与隐私

仓库**不含任何真实学生数据**：`backend/data/`（SQLite 库、backup、班级/专业名单 CSV）与 `backend/faces/`（人脸照片）都在 `.gitignore` 里，只单独放行了建表脚本 `backend/data/schema.sql`。克隆下来是一个空库，需自行导入数据。

## 安全说明

- 已修：`allow_origins=["*"]` 与 `allow_credentials=True` 的组合（浏览器会拒绝，且等于对任意站点放行）→ 改为显式白名单 + 关闭凭据
- 已修：`install.bat` 原来硬编码 `D:\python311\python.exe`，换台机器就装不上 → 改用 PATH 中的 `python`
- 人脸图片接口 `GET /api/faces/{id}/image` 的路径取自数据库、由服务端生成文件名，不接受用户传入路径

**未实现鉴权**：没有登录、没有 Token，任何能访问 8000 端口的人都能调接口。只适合本机或可信内网使用，**不要直接暴露到公网**。

## 已知限制

- 每人仅允许 1 张脸照；多人同框、强逆光、戴口罩等场景未做处理
- SQLite 单写者模型，高并发签到会排队
- 前端依赖 vite 代理访问后端，正式部署需自行配置反向代理
- insightface 首次加载模型有数秒延迟（已在启动时预热规避）

## 许可证

本项目源码采用 [MIT](./LICENSE)。

注意：`insightface` 的**代码**是 MIT，但它提供的**预训练模型（buffalo_l 等）仅限非商业学术研究用途**，商用需单独向 insightface 申请授权。模型权重未纳入本仓库，需要自行下载，使用时请一并遵守模型自身的许可条款。
