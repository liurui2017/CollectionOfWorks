"""站点设置（单行表）。"""
from __future__ import annotations

from sqlalchemy import CheckConstraint, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SiteProfile(Base, TimestampMixin):
    __tablename__ = "site_profile"

    # 单行约束：id 固定为 1
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    site_name: Mapped[str] = mapped_column(String(60), default="我的作品集", nullable=False)
    nickname: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    headline: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_media_id: Mapped[int | None] = mapped_column(nullable=True)
    social_links: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    footer_text: Mapped[str | None] = mapped_column(String(200), nullable=True)

    __table_args__ = (CheckConstraint("id = 1", name="site_profile_single_row"),)


__all__ = ["SiteProfile"]
