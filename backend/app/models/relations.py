"""作品与媒体的关联（封面 / 视频主文件 / 图集图片）。"""
from __future__ import annotations

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class WorkMedia(Base):
    __tablename__ = "work_media"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    work_id: Mapped[int] = mapped_column(ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    media_id: Mapped[int] = mapped_column(ForeignKey("media.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(nullable=False)                      # cover | video | gallery
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)

    __table_args__ = (UniqueConstraint("work_id", "media_id", "role"),)


class WorkTag(Base):
    __tablename__ = "work_tags"

    work_id: Mapped[int] = mapped_column(ForeignKey("works.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


__all__ = ["WorkMedia", "WorkTag"]
