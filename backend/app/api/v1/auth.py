"""鉴权：登录 + 当前管理员。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import create_access_token, get_current_user, verify_password
from app.models.user import User
from app.schemas.auth import AdminUserOut, LoginRequest, TokenOut

router = APIRouter()


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)], request: Request) -> TokenOut:
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    # 记录最后登录时间
    from app.services.helpers import utcnow
    user.last_login_at = utcnow()
    db.commit()

    from app.core.config import get_settings
    settings = get_settings()
    token = create_access_token(user.id)
    return TokenOut(access_token=token, expires_in=settings.JWT_EXPIRE_HOURS * 3600)


@router.get("/me", response_model=AdminUserOut)
def me(current: Annotated[User, Depends(get_current_user)]) -> AdminUserOut:
    return AdminUserOut(
        id=current.id,
        username=current.username,
        last_login_at=current.last_login_at,
    )
