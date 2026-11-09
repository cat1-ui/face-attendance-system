"""学生数据层（对应 @Repository），封装 SQLAlchemy CRUD"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.student import Student


class StudentRepository:
    """学生增删改查，不碰业务逻辑。session 由外部注入（对应 @Autowired）"""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, student_id: int) -> Student | None:
        """按主键查询"""
        return self.session.get(Student, student_id)

    def get_by_student_no(self, student_no: str) -> Student | None:
        """按学号查询（唯一）"""
        return self.session.scalar(select(Student).where(Student.student_no == student_no))

    def list_all(self, skip: int = 0, limit: int = 20) -> list[Student]:
        """分页查询"""
        return list(self.session.scalars(select(Student).offset(skip).limit(limit)))

    def search(self, skip: int = 0, limit: int = 20, **filters) -> list[Student]:
        """组合查询 + 分页：多个条件用 AND 收窄（详见 _apply_filters）"""
        stmt = select(Student)
        stmt = self._apply_filters(stmt, filters)
        # 固定按 id 倒序，保证分页结果稳定（否则 SQLite 返回顺序不保证）
        stmt = stmt.order_by(Student.id.desc())
        return list(self.session.scalars(stmt.offset(skip).limit(limit)))

    def count(self, **filters) -> int:
        """统计总数（配合分页用）"""
        from sqlalchemy import func
        stmt = select(func.count(Student.id))
        stmt = self._apply_filters(stmt, filters)
        return self.session.scalar(stmt) or 0

    @staticmethod
    def _apply_filters(stmt, filters: dict):
        """把过滤条件拼到查询语句上（组合模糊查询）

        规则：
        - 字符串字段（name/student_no/phone/class_name/major）→ 模糊匹配 LIKE %值%
        - 其余字段（id/gender/age/enroll_year/face_status）→ 精确匹配 ==
        - 所有「填了值」的条件之间用 AND 连接：多填一个条件就多收窄一层。
          只填一个字段时等价于单条件查询（"只知道其中一个字段也能查到"）。
        """
        fuzzy_fields = {"name", "student_no", "phone", "class_name", "major"}

        for key, value in filters.items():
            # 空值视为"该条件没填"，跳过（保持前端清空输入框即可不生效）
            if value is None or value == "":
                continue
            column = getattr(Student, key)
            if key in fuzzy_fields:
                stmt = stmt.where(column.contains(str(value)))   # 模糊：LIKE %值%
            else:
                stmt = stmt.where(column == value)               # 精确：=
        return stmt

    def create(self, student: Student) -> Student:
        """新增（不 commit，事务边界在 Service 层）"""
        self.session.add(student)
        self.session.flush()
        return student

    def delete(self, student_id: int) -> None:
        """按主键删除（不 commit，事务边界在 Service 层）"""
        student = self.get_by_id(student_id)
        if student:
            self.session.delete(student)

    # 说明：ORM 的 update 不需要显式方法——Service 层 get 出对象、改字段，
    #       session 自动脏检查(dirty tracking)，commit 时自动生成 UPDATE。
