# 学生刷脸考勤系统

一个部署在笔记本单机上的学生信息 + 人脸录入管理系统（第一阶段）。

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | FastAPI + SQLAlchemy 2.0 + SQLite |
| 人脸 | insightface (buffalo_l) + onnxruntime (CPU) |
| 向量库 | Milvus Lite |
| 分析 | pandas + scikit-learn |
| 前端 | Vue 3 + Element Plus + ECharts（待补充） |

## 目录结构

```
backend/
├── main.py            # 入口：装配路由 + 启动事件
├── core/              # 基础设施：配置、数据库、模型单例
├── models/            # ORM 实体（对应 @Entity）
├── schemas/           # DTO（对应 DTO/VO）
├── repository/        # 数据层（对应 @Repository）
├── service/           # 业务层（对应 @Service）
├── api/               # 控制层（对应 @RestController）
└── data/              # 枚举数据源（班级.csv / 专业.csv）
```

## 快速开始

1. **首次**：双击 `install.bat` 安装依赖（需已安装 Python 3.11，路径 `D:\python311\python.exe`）
2. **启动**：双击 `start.bat`
3. **接口文档**：浏览器打开 http://127.0.0.1:8000/docs

## 接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/students | 学生分页查询（支持搜索） |
| POST | /api/students | 新增学生 |
| PUT | /api/students/{id} | 更新学生 |
| DELETE | /api/students/{id} | 删除学生（级联删脸照） |
| GET | /api/enums | 班级/专业枚举 |
| POST | /api/students/{id}/faces | 上传脸照（人脸检测+落库） |
| GET | /api/students/{id}/faces | 学生脸照列表 |
| GET | /api/stats/summary | 汇总统计 |
| GET | /api/stats/face-coverage | 录入覆盖率 |
| GET | /api/audit/duplicates | 脸库审计（聚类） |

## 注意事项

- **Python 必须是 3.11**（insightface/onnxruntime 兼容要求）
- **numpy 锁 <2.0**
- insightface 模型需手动下载 buffalo_l 到 `~/.insightface/models/buffalo_l/`
