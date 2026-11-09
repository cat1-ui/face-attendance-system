"""ORM 基类（对应 JPA 的 Entity 基类）"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有 ORM 实体的基类，通过它统一建表、映射"""
