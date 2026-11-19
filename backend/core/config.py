"""核心配置 - 对应 Java 的 application.yml"""
import os
from pathlib import Path

# 项目根目录（backend/ 的上一级）
BASE_DIR = Path(__file__).resolve().parent.parent

# SQLite 数据库文件位置（放在 data/ 目录，对齐老师结构）
# 可用环境变量 DATABASE_URL 覆盖，用于压测/测试环境隔离，不污染真实数据
DATABASE_URL = os.getenv(
    "DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'db.sqlite'}"
)

# 脸照图片存放目录
FACE_IMAGE_DIR = BASE_DIR / "faces"

# 枚举数据源（CSV）
DATA_DIR = BASE_DIR / "data"
CLASS_CSV = DATA_DIR / "班级.csv"
MAJOR_CSV = DATA_DIR / "专业.csv"

# insightface 模型名（buffalo_l：检测 + 5点 + 512维嵌入）
FACE_MODEL_NAME = "buffalo_l"
# 检测置信度阈值（低于这个分数视为没检测到人脸）
FACE_DET_THRESHOLD = 0.5

# ===== 考勤规则（改配置不改代码）=====
# 签到/签退识别阈值：相似度 >= 该值才判定为匹配成功
ATTENDANCE_THRESHOLD = 0.45
# 签到截止时间（HH:MM）：晚于该时间签到 = 迟到
CHECKIN_DEADLINE = "09:00"
# 签退起始时间（HH:MM）：早于该时间签退 = 早退
CHECKOUT_START = "18:00"

# Milvus Lite 数据文件
MILVUS_DB_FILE = str(BASE_DIR / "milvus_lite.db")
MILVUS_COLLECTION = "face_vectors"
# 嵌入维度（ArcFace 输出 512 维）
EMBED_DIM = 512

# 保证目录存在
FACE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
