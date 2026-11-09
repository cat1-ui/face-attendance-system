"""insightface 单例 - 模型常驻内存，避免每次请求重复加载

关键点（文档难点 #7）：模型加载要好几秒，
所以用「单例 + 启动时加载一次」的模式，后续请求直接复用。
"""
import threading

import numpy as np
from insightface.app import FaceAnalysis

from core.config import FACE_MODEL_NAME

_lock = threading.Lock()
_engine: FaceAnalysis | None = None


def get_face_engine() -> FaceAnalysis:
    """返回全局唯一的 FaceAnalysis 实例（懒加载 + 线程安全）"""
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:  # 双重检查，防止并发重复初始化
                app = FaceAnalysis(name=FACE_MODEL_NAME, allowed_modules=["detection", "recognition"])
                app.prepare(ctx_id=0, det_size=(640, 640))  # ctx_id=0 表示用 CPU
                _engine = app
    return _engine


def extract_face_info(img_bgr: np.ndarray) -> dict:
    """从一张 BGR 图片里提取人脸信息

    返回：
        {"detected": bool, "embedding": list | None, "reason": str}
    - detected=False 表示没检测到人脸或图片里有多张脸取不到有效结果
    - 只取面积最大的那张脸（难点 #6：多脸只取最大脸）
    """
    engine = get_face_engine()
    faces = engine.get(img_bgr)

    if len(faces) == 0:
        return {"detected": False, "embedding": None, "reason": "未检测到人脸"}

    # 按人脸框面积排序，取最大的
    faces_sorted = sorted(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)
    largest = faces_sorted[0]

    # 置信度兜底：分数太低的视作无效
    if hasattr(largest, "det_score") and largest.det_score < 0.3:
        return {"detected": False, "embedding": None, "reason": "人脸质量过低，请重新拍摄"}

    # embedding 是 512 维 numpy 数组，转成 list 方便序列化
    emb = largest.embedding
    if emb is None:
        return {"detected": False, "embedding": None, "reason": "无法提取人脸特征"}

    return {"detected": True, "embedding": emb.tolist(), "reason": None}
