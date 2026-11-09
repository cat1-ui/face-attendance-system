"""枚举容器 - 班级/专业的下拉选项来源

机制（文档第 9.2 节）：
1. 启动时用 pandas 读取 data/班级.csv 和 data/专业.csv
2. 填充到全局变量 CLASSES / MAJORS
3. 前端下拉、后端校验都从这两个变量取值
4. 改枚举 = 改 CSV + 重启，不改代码
"""
import pandas as pd

from core.config import CLASS_CSV, MAJOR_CSV

# 全局枚举容器（启动时填充）
CLASSES: list[str] = []
MAJORS: list[str] = []


def load_enums():
    """启动时调用：从 CSV 读入枚举值"""
    global CLASSES, MAJORS

    # 读 CSV，第一列就是枚举值
    if CLASS_CSV.exists():
        CLASSES = pd.read_csv(CLASS_CSV, header=None)[0].astype(str).tolist()
    if MAJOR_CSV.exists():
        MAJORS = pd.read_csv(MAJOR_CSV, header=None)[0].astype(str).tolist()

    # 去空、去重、保序
    CLASSES = [c.strip() for c in CLASSES if c.strip()]
    MAJORS = [m.strip() for m in MAJORS if m.strip()]
