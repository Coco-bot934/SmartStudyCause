"""认证接口：登录获取 JWT"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """管理员登录：校验用户名密码，返回 JWT Token"""
    if body.username != settings.ADMIN_USER:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    user = db.query(User).filter(User.username == body.username).first()

    if user is None:
        # 首次登录：自动创建用户
        user = User(
            username=body.username,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
        )
        db.add(user)
        db.flush()
    elif not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    token = create_access_token(subject=user.username)
    return LoginResponse(access_token=token)
