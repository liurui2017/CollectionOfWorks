"""鉴权相关 schema。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=255)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminUserOut(BaseModel):
    id: int
    username: str
    last_login_at: datetime | None = None


__all__ = ["LoginRequest", "TokenOut", "AdminUserOut"]
