"""认证与授权：密码哈希 + JWT 签发/校验 + 依赖注入

选型说明：
- 密码用 bcrypt：自带随机 salt、cost 可调，抗彩虹表；绝不用 md5/sha1
- JWT 用 HS256 对称签名：服务端持密钥，载荷只放 sub/username/role/exp，不放敏感信息
- 密钥从环境变量 JWT_SECRET 读取；缺省值仅供本地开发，启动会告警
"""
import os
import warnings
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.db import get_db
from models import User

SECRET_KEY = os.getenv("JWT_SECRET", "")
if not SECRET_KEY:
    SECRET_KEY = "dev-only-insecure-secret-change-me"
    warnings.warn("未设置 JWT_SECRET，正在使用开发默认密钥，切勿用于生产")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 默认 8 小时

# tokenUrl 指向登录接口，Swagger 右上角 Authorize 才能直接登录试用
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(raw: str) -> str:
    """生成 bcrypt 哈希（每次结果不同，因为 salt 随机）"""
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    """校验明文与哈希是否匹配；哈希格式非法时返回 False 而不是抛异常"""
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """解码并校验签名/过期时间；失败统一抛 401"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "登录已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "登录凭证无效",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """从 Bearer token 解析出当前用户；用户被删了也要拦住"""
    payload = decode_token(token)
    try:
        uid = int(payload.get("sub", 0))
    except (TypeError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录凭证无效")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "用户不存在或已被删除",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """写接口守卫：只有 admin 能改数据，viewer 只能看"""
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要管理员权限")
    return user
