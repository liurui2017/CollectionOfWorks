"""作品 schema — 契约核心。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.category import CategoryRef
from app.schemas.enums import WorkStatus, WorkType
from app.schemas.media import MediaOut
from app.schemas.tag import TagRef


class WorkListItem(BaseModel):
    """列表卡片用：不含正文。"""
    id: int
    title: str
    slug: str
    type: WorkType
    summary: str | None = None
    cover: MediaOut | None = None
    category: CategoryRef | None = None
    tags: list[TagRef] = Field(default_factory=list)
    is_featured: bool = False
    view_count: int = 0
    published_at: datetime | None = None


class WorkDetail(WorkListItem):
    """详情页用。"""
    content: str | None = None
    video: MediaOut | None = None
    images: list[MediaOut] = Field(default_factory=list)
    # status 在后台列表才有意义，但详情回填需要；前台接口会在返回前剥掉
    status: WorkStatus | None = None


class WorkCreate(BaseModel):
    """创建 / 更新共用（更新为全量 PUT）。"""
    title: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)
    type: WorkType
    summary: str | None = Field(default=None, max_length=300)
    content: str | None = None
    category_id: int | None = None
    tag_ids: list[int] = Field(default_factory=list)
    cover_media_id: int | None = None
    video_media_id: int | None = None
    gallery_media_ids: list[int] = Field(default_factory=list)
    is_featured: bool = False
    status: WorkStatus = WorkStatus.draft
    sort_order: int = 0
    published_at: datetime | None = None


# 更新与创建同构
class WorkUpdate(WorkCreate):
    pass


class WorkAnalyticsSnapshot(BaseModel):
    """后台列表聚合数据，不单独暴露。"""
    work_id: int
    views_today: int
    views_last_7d: int


__all__ = ["WorkListItem", "WorkDetail", "WorkCreate", "WorkUpdate", "WorkAnalyticsSnapshot"]
