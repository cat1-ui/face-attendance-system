"""公告数据层（对应 @Repository）"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.notice import Notice


class NoticeRepository:
    """公告增删改查，不碰业务逻辑"""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, notice_id: int) -> Notice | None:
        """按主键查询"""
        return self.session.get(Notice, notice_id)

    def list_all(self, skip: int = 0, limit: int = 20) -> list[Notice]:
        """分页查询（按发布时间倒序）"""
        return list(
            self.session.scalars(
                select(Notice).order_by(Notice.created_at.desc()).offset(skip).limit(limit)
            )
        )

    def count(self) -> int:
        """统计总数（配合分页用）"""
        from sqlalchemy import func
        return self.session.scalar(select(func.count(Notice.id))) or 0

    def create(self, notice: Notice) -> Notice:
        """新增（不 commit，事务边界在 Service 层）"""
        self.session.add(notice)
        self.session.flush()
        return notice

    def delete(self, notice_id: int) -> None:
        """按主键删除（不 commit）"""
        notice = self.get_by_id(notice_id)
        if notice:
            self.session.delete(notice)
