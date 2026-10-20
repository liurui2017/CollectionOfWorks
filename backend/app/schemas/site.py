"""站点设置 schema。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.media import MediaOut


class SocialLink(BaseModel):
    label: str = Field(min_length=1, max_length=40)
    url: str = Field(min_length=1, max_length=500)


class SiteProfileOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    site_name: str
    nickname: str
    headline: str | None = None
    bio: str | None = None
    avatar: MediaOut | None = None
    social_links: list[SocialLink] = Field(default_factory=list)
    footer_text: str | None = None
    updated_at: datetime


class SiteProfileUpdate(BaseModel):
    site_name: str | None = Field(default=None, max_length=60)
    nickname: str | None = Field(default=None, max_length=40)
    headline: str | None = Field(default=None, max_length=120)
    bio: str | None = None
    avatar_media_id: int | None = None
    social_links: list[SocialLink] | None = None
    footer_text: str | None = Field(default=None, max_length=200)


__all__ = ["SocialLink", "SiteProfileOut", "SiteProfileUpdate"]
