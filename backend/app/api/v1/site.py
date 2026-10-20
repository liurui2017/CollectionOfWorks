"""站点设置：公开读取 + 管理更新。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.media import Media
from app.models.site_profile import SiteProfile
from app.models.user import User
from app.schemas.media import MediaOut
from app.schemas.site import SiteProfileOut, SiteProfileUpdate
from app.services import site as site_svc

router = APIRouter()


def _profile_to_out(sp: SiteProfile, avatar: Media | None) -> SiteProfileOut:
    social = sp.social_links or []
    return SiteProfileOut(
        id=sp.id,
        site_name=sp.site_name,
        nickname=sp.nickname,
        headline=sp.headline,
        bio=sp.bio,
        avatar=MediaOut.model_validate(avatar) if avatar else None,
        social_links=social,
        footer_text=sp.footer_text,
        updated_at=sp.updated_at,
    )


@router.get("/site/profile", response_model=SiteProfileOut)
def get_public(db: Annotated[Session, Depends(get_db)]) -> SiteProfileOut:
    sp = site_svc.get_or_create(db)
    avatar = db.get(Media, sp.avatar_media_id) if sp.avatar_media_id else None
    return _profile_to_out(sp, avatar)


@router.get("/admin/site/profile", response_model=SiteProfileOut)
def get_admin(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> SiteProfileOut:
    sp = site_svc.get_or_create(db)
    avatar = db.get(Media, sp.avatar_media_id) if sp.avatar_media_id else None
    return _profile_to_out(sp, avatar)


@router.put("/admin/site/profile", response_model=SiteProfileOut)
def update_admin(
    payload: SiteProfileUpdate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> SiteProfileOut:
    sp = site_svc.update(db, payload)
    avatar = db.get(Media, sp.avatar_media_id) if sp.avatar_media_id else None
    return _profile_to_out(sp, avatar)
