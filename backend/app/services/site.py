"""站点设置：单行表 site_profile 读写。"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.media import Media
from app.models.site_profile import SiteProfile
from app.schemas.site import SiteProfileUpdate


DEFAULT_PROFILE = dict(
    id=1,
    site_name="我的作品集",
    nickname="",
    headline=None,
    bio=None,
    avatar_media_id=None,
    social_links=[],
    footer_text=None,
)


def get_or_create(db: Session) -> SiteProfile:
    sp = db.get(SiteProfile, 1)
    if sp is None:
        sp = SiteProfile(**DEFAULT_PROFILE)
        db.add(sp)
        db.commit()
        db.refresh(sp)
    return sp


def update(db: Session, payload: SiteProfileUpdate) -> SiteProfile:
    sp = get_or_create(db)
    data = payload.model_dump(exclude_unset=True)
    # 头像若被引用，校验 media 存在性
    if "avatar_media_id" in data and data["avatar_media_id"] is not None:
        if db.get(Media, data["avatar_media_id"]) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="头像媒体不存在")
    for k, v in data.items():
        setattr(sp, k, v)
    db.commit()
    db.refresh(sp)
    return sp


__all__ = ["get_or_create", "update", "DEFAULT_PROFILE"]
