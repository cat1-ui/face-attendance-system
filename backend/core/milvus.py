"""向量存储客户端 - 纯 numpy 内存检索实现

背景：
    Milvus Lite 官方不支持 Windows（pymilvus 依赖里明确 sys_platform != "win32"），
    在 Windows 上无论用哪个版本都有兼容性问题。本项目数据量小（一个班几十人），
    因此用「numpy 内存暴力检索」替代 Milvus，功能等价、代码可控。

设计：
    - 向量持久化到 SQLite（复用现有 db.sqlite 的 face_vectors 表），重启不丢数据
    - 启动时把全部向量加载进内存（numpy 矩阵），检索用矩阵乘法算余弦相似度
    - 对外接口（insert/delete/query/search_face）与 MilvusClient 兼容，
      业务层代码无需改动

面试口径：
    「为什么小数据量下用内存暴力检索而非向量数据库？」
    - 数据量小（<1万条 512 维向量）时，暴力检索耗时是毫秒级，性能无瓶颈
    - 向量数据库的价值在「海量向量 + 近似最近邻索引(HNSW)」，
      数据量小反而引入额外的服务/依赖/序列化开销
    - 工程上遵循「够用就好」，避免过度设计
"""
from __future__ import annotations

import json
import threading

import numpy as np
from sqlalchemy import text

from core.db import engine

_lock = threading.Lock()


class _NumpyVectorClient:
    """兼容 MilvusClient 接口的轻量向量存储（内存 numpy + SQLite 持久化）

    通过 SQLAlchemy engine 访问 db.sqlite（与 ORM 共享同一连接池），
    避免独立 sqlite3 连接与 ORM 并发写时产生 database is locked。
    """

    def __init__(self):
        self._ensure_table()
        self._embeddings: dict[int, np.ndarray] = {}   # face_id -> 512 维向量
        self._student_ids: dict[int, int] = {}         # face_id -> student_id
        self._created_ats: dict[int, int] = {}         # face_id -> 创建时间
        self._load_all()

    # ---------- 内部 ----------
    def _ensure_table(self):
        """建向量表（face_id 主键，embedding 存 JSON 字符串）"""
        with engine.begin() as conn:
            conn.execute(text(
                """
                CREATE TABLE IF NOT EXISTS face_vectors (
                    face_id     INTEGER PRIMARY KEY,
                    student_id  INTEGER NOT NULL,
                    embedding   TEXT NOT NULL,
                    created_at  INTEGER
                )
                """
            ))

    def _load_all(self):
        """启动时把库里的向量全量加载进内存"""
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT face_id, student_id, embedding, created_at FROM face_vectors"
            )).fetchall()
        for face_id, student_id, emb_json, created_at in rows:
            self._embeddings[face_id] = np.array(json.loads(emb_json), dtype=np.float32)
            self._student_ids[face_id] = student_id
            self._created_ats[face_id] = created_at

    # ---------- 对外接口（与 MilvusClient 兼容） ----------
    def insert(self, collection_name: str, data: list[dict]):
        """插入向量。data 形如 [{"face_id":1,"student_id":2,"embedding":[...],"created_at":...}]"""
        with engine.begin() as conn:
            for row in data:
                face_id = int(row["face_id"])
                emb = np.array(row["embedding"], dtype=np.float32)
                student_id = int(row["student_id"])
                created_at = int(row.get("created_at", 0))
                conn.execute(text(
                    "INSERT OR REPLACE INTO face_vectors (face_id, student_id, embedding, created_at) "
                    "VALUES (:face_id, :student_id, :embedding, :created_at)"
                ), {"face_id": face_id, "student_id": student_id,
                    "embedding": json.dumps(emb.tolist()), "created_at": created_at})
                self._embeddings[face_id] = emb
                self._student_ids[face_id] = student_id
                self._created_ats[face_id] = created_at

    def delete(self, collection_name: str, ids: list[int]):
        """按 face_id 批量删除"""
        with engine.begin() as conn:
            for fid in ids:
                fid = int(fid)
                conn.execute(text("DELETE FROM face_vectors WHERE face_id = :face_id"), {"face_id": fid})
                self._embeddings.pop(fid, None)
                self._student_ids.pop(fid, None)
                self._created_ats.pop(fid, None)

    def query(self, collection_name: str, filter: str = "", output_fields: list[str] | None = None,
              limit: int = 10000) -> list[dict]:
        """查询全部（或部分）向量记录，供脸库审计聚类使用"""
        output_fields = output_fields or ["face_id", "student_id", "embedding"]
        results = []
        for face_id in sorted(self._embeddings.keys()):
            row = {
                "face_id": face_id,
                "student_id": self._student_ids[face_id],
                "embedding": self._embeddings[face_id].tolist(),
                "created_at": self._created_ats.get(face_id, 0),
            }
            results.append({k: row[k] for k in output_fields if k in row})
            if len(results) >= limit:
                break
        return results


_client: _NumpyVectorClient | None = None


def get_milvus() -> _NumpyVectorClient:
    """返回全局唯一向量客户端（懒加载 + 线程安全）

    函数名保留 get_milvus 以兼容现有业务代码，内部实现已换成 numpy 方案。
    """
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                _client = _NumpyVectorClient()
    return _client


def search_face(embedding: list[float], top_k: int = 1) -> list[dict]:
    """向量检索：给定一张脸的 512 维向量，返回最相似的 top_k 条

    返回：
        [{"face_id": int, "student_id": int, "distance": float}, ...]
    - distance 即余弦相似度（0~1），越接近 1 越相似
    - 空向量库时返回空列表
    """
    client = get_milvus()
    if not client._embeddings:
        return []

    query = np.array(embedding, dtype=np.float32)
    q_norm = np.linalg.norm(query)
    if q_norm == 0:
        return []
    query = query / q_norm

    face_ids = list(client._embeddings.keys())
    matrix = np.stack([client._embeddings[fid] for fid in face_ids])   # (N, 512)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    matrix = matrix / norms
    sims = matrix @ query                                              # (N,)

    top_indices = np.argsort(-sims)[:top_k]
    return [
        {
            "face_id": int(face_ids[i]),
            "student_id": int(client._student_ids[face_ids[i]]),
            "distance": float(sims[i]),
        }
        for i in top_indices
    ]
