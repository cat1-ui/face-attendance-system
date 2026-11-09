"""汇总统计 + 脸库审计（ML 聚类）服务"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Student, Face


class StatsService:
    """汇总统计 - 纯 SQL 聚合，不做 ML（文档第 5 节明确）"""
    def __init__(self, db: Session):
        self.db = db

    def summary(self):
        total = self.db.query(func.count(Student.id)).scalar() or 0
        by_class = dict(self.db.query(Student.class_name, func.count(Student.id))
                        .filter(Student.class_name.isnot(None)).group_by(Student.class_name).all())
        by_gender = dict(self.db.query(Student.gender, func.count(Student.id))
                         .filter(Student.gender.isnot(None)).group_by(Student.gender).all())
        by_major = dict(self.db.query(Student.major, func.count(Student.id))
                        .filter(Student.major.isnot(None)).group_by(Student.major).all())
        return {"total_students": total, "by_class": by_class,
                "by_gender": by_gender, "by_major": by_major}

    def face_coverage(self):
        enrolled = self.db.query(func.count(Student.id)).filter(Student.face_status == 1).scalar() or 0
        total = self.db.query(func.count(Student.id)).scalar() or 0
        not_enrolled = total - enrolled
        coverage = round(enrolled / total, 4) if total else 0.0
        return {"enrolled": enrolled, "not_enrolled": not_enrolled, "coverage_rate": coverage}

    def face_count_dist(self):
        """按学生统计脸照数量：0张/1张/多张"""
        rows = self.db.query(Face.student_id, func.count(Face.id)).group_by(Face.student_id).all()
        cnt = {sid: c for sid, c in rows}
        total = self.db.query(func.count(Student.id)).scalar() or 0
        zero = one = multiple = 0
        for sid in self.db.query(Student.id).all():
            c = cnt.get(sid[0], 0)
            if c == 0:
                zero += 1
            elif c == 1:
                one += 1
            else:
                multiple += 1
        return {"zero_face": zero, "one_face": one, "multiple_faces": multiple}


class ClusterService:
    """脸库审计 - 人脸嵌入聚类（无监督 ML）

    原理：从 Milvus 拉出全部向量 → 两两算余弦相似度 → 找高相似度对。
    同一学号两张脸相似度极低 = 录错人；不同学号相似度极高 = 疑似一人多号。
    """
    def __init__(self, db: Session):
        self.db = db

    def find_duplicates(self, threshold: float = 0.85):
        import numpy as np
        from core import milvus
        from core.config import MILVUS_COLLECTION

        client = milvus.get_milvus()
        # 查询全部向量（带标量字段）
        results = client.query(
            collection_name=MILVUS_COLLECTION,
            filter="",  # 空过滤 = 全部
            output_fields=["face_id", "student_id", "embedding"],
            limit=10000,
        )

        if len(results) < 2:
            return {"duplicates": []}

        embeddings = np.array([r["embedding"] for r in results], dtype=np.float32)
        # L2 归一化后点积 = 余弦相似度
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        emb_norm = embeddings / norms
        sim_matrix = emb_norm @ emb_norm.T  # N×N 相似度矩阵

        duplicates = []
        n = len(results)
        for i in range(n):
            for j in range(i + 1, n):
                sim = float(sim_matrix[i, j])
                if sim >= threshold:
                    a, b = results[i], results[j]
                    # 跳过同一个学生的多张脸（那是正常的）
                    if a["student_id"] == b["student_id"]:
                        continue
                    duplicates.append({
                        "face_a": a["face_id"], "face_b": b["face_id"],
                        "student_a": a["student_id"], "student_b": b["student_id"],
                        "similarity": round(sim, 4),
                    })

        # 补学生姓名/学号
        student_map = {s.id: s for s in self.db.query(Student).all()}
        out = []
        for d in duplicates:
            sa = student_map.get(d["student_a"])
            sb = student_map.get(d["student_b"])
            out.append({
                "student_a": {"id": d["student_a"], "name": sa.name if sa else "?", "student_no": sa.student_no if sa else "?"},
                "student_b": {"id": d["student_b"], "name": sb.name if sb else "?", "student_no": sb.student_no if sb else "?"},
                "similarity": d["similarity"],
            })
        return {"duplicates": out}
