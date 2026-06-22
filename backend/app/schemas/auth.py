from pydantic import BaseModel


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录成功返回 Token"""
    access_token: str
    token_type: str = "bearer"
