"""认证接口"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from common.response import ApiResponse
from core.db import get_db
from core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from models import User
from schemas.auth import LoginIn, UserOut

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """登录换 token。

    返回的是扁平结构（不是统一信封），因为 OAuth2 / Swagger Authorize
    约定的字段名就是 access_token / token_type，包一层它会读不到。
    """
    user = db.query(User).filter(User.username == form.username).first()
    # 用户不存在与密码错误返回同一句提示，避免被用来枚举用户名
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserOut.model_validate(user).model_dump(),
    }


@router.post("/login-json", response_model=ApiResponse[dict])
def login_json(payload: LoginIn, db: Session = Depends(get_db)):
    """JSON 版登录：前端表单直接提交 JSON，不必拼 form-data"""
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return ApiResponse(data={
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserOut.model_validate(user).model_dump(),
    })


@router.get("/me", response_model=ApiResponse[dict])
def me(user: User = Depends(get_current_user)):
    """当前登录用户信息（前端刷新页面后用它校验 token 是否还有效）"""
    return ApiResponse(data=UserOut.model_validate(user).model_dump())
