"""全局异常处理器 - 横切层（common/）

三层兜底，保证对外永远看不到库内部的报错信息：
① 业务异常 HTTPException → 友好中文提示
② 校验异常 RequestValidationError → 英文转中文
③ 兜底异常 Exception → 藏细节，真实错误只进日志
"""
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from common.response import RespCode

logger = logging.getLogger(__name__)


def _error(code: int, message: str) -> JSONResponse:
    """统一错误响应格式"""
    return JSONResponse(status_code=code, content={"code": code, "message": message, "data": None})


async def http_exception_handler(request: Request, exc: HTTPException):
    """① 业务异常：转统一格式"""
    return _error(exc.status_code, str(exc.detail))


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """② 校验异常：英文错误转中文提示"""
    msgs = []
    for e in exc.errors():
        # loc 形如 ('body', 'name') 或 ('query', 'id')，取最后一截作为字段名
        field = ".".join(str(x) for x in e.get("loc", []))
        err_type = e.get("type", "")
        if err_type == "int_parsing":
            msgs.append(f"参数「{field}」必须是整数")
        elif err_type == "missing":
            msgs.append(f"参数「{field}」不能为空")
        elif err_type in ("greater_than_equal", "less_than_equal"):
            msgs.append(f"参数「{field}」超出范围")
        else:
            msgs.append(f"参数「{field}」校验失败")
    return _error(RespCode.VALIDATION_ERROR, "；".join(msgs))


async def unhandled_exception_handler(request: Request, exc: Exception):
    """③ 兜底异常：真实错误进日志，前端只看到笼统提示（防止泄露表名/字段/SQL/traceback）"""
    logger.error(f"未预期异常: {exc}", exc_info=True)
    return _error(RespCode.SERVER_ERROR, "服务器内部错误")


def register_exceptions(app: FastAPI) -> None:
    """一行装配三个异常处理器，main.py 保持干净"""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
