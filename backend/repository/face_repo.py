"""脸照数据层（对应 @Repository）"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.face import Face


class FaceRepository:
    """脸照元数据增删改查。向量(embedding)在 Milvus，本类只碰 SQLite 元数据"""

    def __init__(self, session: Session):
        self.session = session

    def list_by_student(self, student_id: int) -> list[Face]:
        """查某学生的所有脸照"""
        return list(self.session.scalars(select(Face).where(Face.student_id == student_id)))

    def get_by_face_id(self, face_id: int) -> Face | None:
        """按 face_id 查询（face_id 是 SQLite 与 Milvus 的桥接字段）"""
        return self.session.scalar(select(Face).where(Face.face_id == face_id))

    def create(self, face: Face) -> Face:
        """新增（不 commit，事务边界在 Service 层）"""
        self.session.add(face)
        self.session.flush()
        return face

    def delete_by_face_id(self, face_id: int) -> None:
        """按 face_id 删除（不 commit）"""
        face = self.get_by_face_id(face_id)
        if face:
            self.session.delete(face)

    def next_face_id(self) -> int:
        """生成下一个 face_id（用 max+1，避免和已删记录冲突）"""
        from sqlalchemy import func
        r = self.session.scalar(select(func.max(Face.face_id)))
        return (r or 0) + 1

    # TODO(后续步骤): 接入 Milvus 后，增加「从向量库拉 embedding」的方法，
    # 例如 query_vectors(student_id) -> list[float]，供聚类/审计使用。
