"""认证相关 DTO"""
from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str


class LoginIn(BaseModel):
    """JSON 登录入参（前端用；Swagger 的 Authorize 走表单，由 OAuth2PasswordRequestForm 接）"""

    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=64)
