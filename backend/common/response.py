"""统一响应模型 - 横切层（common/）

所有接口统一返回 {code, message, data}，前端一套解析逻辑通吃。
- RespCode：状态码枚举（IntEnum，序列化自动变数字）
- ApiResponse：泛型响应模型（data 类型跟着接口走）
"""
from enum import IntEnum
from typing import Generic, TypeVar

from pydantic import BaseModel


class RespCode(IntEnum):
    """业务状态码（同时是 int，序列化成 JSON 自动变数字）"""
    SUCCESS = 0              # 成功
    BAD_REQUEST = 400        # 业务错误
    NOT_FOUND = 404          # 不存在
    VALIDATION_ERROR = 422   # 参数校验失败
    SERVER_ERROR = 500       # 服务器内部错误


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应模型：code + message + data"""
    code: int = RespCode.SUCCESS
    message: str = "ok"
    data: T | None = None
