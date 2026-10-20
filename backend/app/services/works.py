"""作品业务服务：查询、聚合、CRUD、发布状态切换。

所有返回给路由层的都是 Pydantic schema（WorkListItem / WorkDetail），
ORM 对象不外溢到路由层。
"""
from __future__ import annotations

from datetime import datetime, timedelta, UTC
from typing import Annotated, Literal, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.analytics import AnalyticsEvent
from app.models.category import Category
from app.models.media import Media
from app.models.relations import WorkMedia, WorkTag
from app.models.tag import Tag
from app.models.work import Work
from app.schemas.enums import MediaRole, WorkStatus, WorkType
from app.schemas.work import WorkCreate, WorkDetail, WorkListItem
from app.services.helpers import utcnow

SortKey = Literal["latest", "oldest", "views"]


# ──────────────────────────────────────────────
# 私有：ORM → Schema 装配
# ──────────────────────────────────────────────

def _load_work_relations(db: Session, work_ids: list[int]) -> dict[int, dict]:
    """一次性把一批 work 的 cover / video / gallery / tags / category 全加载回来。"""
    if not work_ids:
        return {}

    # category
    cat_stmt = select(Category).where(Category.id.in_(
        select(Work.category_id).where(Work.id.in_(work_ids)).distinct()
    ))
    cats = {c.id: c for c in db.scalars(cat_stmt).all()}

    # tags via work_tags
    wt_stmt = select(WorkTag).where(WorkTag.work_id.in_(work_ids))
    wts = db.scalars(wt_stmt).all()
    tag_ids = sorted({wt.tag_id for wt in wts})
    tags = {t.id: t for t in db.scalars(select(Tag).where(Tag.id.in_(tag_ids))).all()} if tag_ids else {}
    work_tags_map: dict[int, list[Tag]] = {}
    for wt in wts:
        work_tags_map.setdefault(wt.work_id, []).append(tags[wt.tag_id])

    # media via work_media（按 role 分组）
    wm_stmt = select(WorkMedia).where(WorkMedia.work_id.in_(work_ids)).order_by(WorkMedia.sort_order)
    wms = db.scalars(wm_stmt).all()
    media_ids = sorted({wm.media_id for wm in wms})
    media_by_id = {m.id: m for m in db.scalars(select(Media).where(Media.id.in_(media_ids))).all()} if media_ids else {}

    work_cover: dict[int, Media] = {}
    work_video: dict[int, Media] = {}
    work_gallery: dict[int, list[Media]] = {}
    for wm in wms:
        m = media_by_id.get(wm.media_id)
        if m is None:
            continue
        if wm.role == MediaRole.cover.value:
            work_cover.setdefault(wm.work_id, m)
        elif wm.role == MediaRole.video.value:
            work_video.setdefault(wm.work_id, m)
        elif wm.role == MediaRole.gallery.value:
            work_gallery.setdefault(wm.work_id, []).append(m)

    result: dict[int, dict] = {}
    for wid in work_ids:
        result[wid] = {
            "category": cats.get(None),  # placeholder, replace below
            "cover": work_cover.get(wid),
            "video": work_video.get(wid),
            "images": work_gallery.get(wid, []),
            "tags": work_tags_map.get(wid, []),
        }
    # 正确的 category 关联
    work_cat_stmt = select(Work.id, Work.category_id).where(Work.id.in_(work_ids))
    for wid, cid in db.execute(work_cat_stmt).all():
        result[wid]["category"] = cats.get(cid)
    return result


def _to_list_item(work: Work, ctx: dict) -> WorkListItem:
    cat = ctx.get("category")
    cover: Media | None = ctx.get("cover")
    tags: list[Tag] = ctx.get("tags", [])
    return WorkListItem(
        id=work.id,
        title=work.title,
        slug=work.slug,
        type=WorkType(work.type),
        summary=work.summary,
        cover=MediaOut.model_validate(cover) if cover else None,
        category=CategoryRef.model_validate(cat) if cat else None,
        tags=[TagRef.model_validate(t) for t in tags],
        is_featured=work.is_featured,
        view_count=work.view_count,
        published_at=work.published_at,
    )


def _to_detail(work: Work, ctx: dict, include_status: bool) -> WorkDetail:
    item = _to_list_item(work, ctx)
    video: Media | None = ctx.get("video")
    images: list[Media] = ctx.get("images", [])
    return WorkDetail(
        **item.model_dump(),
        content=work.content,
        video=MediaOut.model_validate(video) if video else None,
        images=[MediaOut.model_validate(m) for m in images],
        status=WorkStatus(work.status) if include_status else None,
    )


# 这些 schema 依赖在函数底部导入避免循环
from app.schemas.media import MediaOut
from app.schemas.category import CategoryRef
from app.schemas.tag import TagRef


# ──────────────────────────────────────────────
# 查询
# ──────────────────────────────────────────────

def list_works(
    db: Session,
    *,
    include_drafts: bool = False,
    type: Optional[WorkType] = None,
    category_slug: Optional[str] = None,
    tag_slug: Optional[str] = None,
    q: Optional[str] = None,
    featured: Optional[bool] = None,
    sort: SortKey = "latest",
    page: int = 1,
    page_size: int = 12,
    admin_category_id: Optional[int] = None,
    status_filter: Optional[WorkStatus] = None,
) -> tuple[list[WorkListItem], int]:
    """返回 (items, total)。"""
    stmt = select(Work)
    count_stmt = select(func.count(Work.id))

    if not include_drafts:
        stmt = stmt.where(Work.status == WorkStatus.published.value)
        count_stmt = count_stmt.where(Work.status == WorkStatus.published.value)
    if status_filter:
        stmt = stmt.where(Work.status == status_filter.value)
        count_stmt = count_stmt.where(Work.status == status_filter.value)
    if type:
        stmt = stmt.where(Work.type == type.value)
        count_stmt = count_stmt.where(Work.type == type.value)
    if admin_category_id is not None:
        stmt = stmt.where(Work.category_id == admin_category_id)
        count_stmt = count_stmt.where(Work.category_id == admin_category_id)
    if featured is not None:
        stmt = stmt.where(Work.is_featured.is_(featured))
        count_stmt = count_stmt.where(Work.is_featured.is_(featured))
    if q:
        like = f"%{q}%"
        kw = or_(Work.title.ilike(like), Work.summary.ilike(like), Work.content.ilike(like))
        stmt = stmt.where(kw)
        count_stmt = count_stmt.where(kw)

    if category_slug:
        cat_sub = select(Category.id).where(Category.slug == category_slug)
        stmt = stmt.where(Work.category_id.in_(cat_sub))
        count_stmt = count_stmt.where(Work.category_id.in_(cat_sub))

    if tag_slug:
        tag_sub = select(Tag.id).where(Tag.slug == tag_slug)
        wt_sub = select(WorkTag.work_id).where(WorkTag.tag_id.in_(tag_sub))
        stmt = stmt.where(Work.id.in_(wt_sub))
        count_stmt = count_stmt.where(Work.id.in_(wt_sub))

    total = db.scalar(count_stmt) or 0

    # 排序
    if sort == "latest":
        stmt = stmt.order_by(Work.is_featured.desc(), Work.sort_order.desc(), (Work.published_at.desc()).nullslast(), Work.created_at.desc())
    elif sort == "oldest":
        stmt = stmt.order_by(Work.published_at.asc().nullslast(), Work.created_at.asc())
    elif sort == "views":
        stmt = stmt.order_by(Work.view_count.desc(), Work.published_at.desc().nullslast())

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    works = db.scalars(stmt).all()

    ctx = _load_work_relations(db, [w.id for w in works])
    items = [_to_list_item(w, ctx.get(w.id, {})) for w in works]
    return items, total


def get_work_by_slug(db: Session, slug: str, *, include_drafts: bool = False) -> Work | None:
    stmt = select(Work).where(Work.slug == slug)
    if not include_drafts:
        stmt = stmt.where(Work.status == WorkStatus.published.value)
    return db.scalar(stmt)


def get_work_by_id(db: Session, work_id: int) -> Work | None:
    return db.get(Work, work_id)


def to_detail(db: Session, work: Work, *, include_status: bool) -> WorkDetail:
    ctx = _load_work_relations(db, [work.id]).get(work.id, {})
    return _to_detail(work, ctx, include_status=include_status)


# ──────────────────────────────────────────────
# 浏览量 + analytics（同事务）
# ──────────────────────────────────────────────

def register_view(
    db: Session,
    *,
    work: Work,
    path: str,
    visitor_hash: str,
    referer: str | None,
    user_agent: str | None,
) -> None:
    """view_count 自增 + analytics_events 插入，同事务。"""
    work.view_count = Work.view_count + 1
    db.add(work)
    db.add(AnalyticsEvent(
        event_type="work_view",
        work_id=work.id,
        path=path,
        visitor_hash=visitor_hash,
        referer=referer,
        user_agent=user_agent,
        created_at=utcnow(),
    ))
    db.commit()


# ──────────────────────────────────────────────
# CRUD
# ──────────────────────────────────────────────

def _check_slug_conflict(db: Session, slug: str, exclude_id: int | None = None) -> None:
    stmt = select(Work.id).where(Work.slug == slug)
    if exclude_id is not None:
        stmt = stmt.where(Work.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"slug 已被占用：{slug}")


def _sync_work_media(db: Session, work_id: int, media_id: int | None, role: MediaRole, sort_order: int = 0) -> None:
    """设置某 role 的关联：先删旧的、再插新的。media_id 为 None 时只删旧的。"""
    db.query(WorkMedia).filter(
        WorkMedia.work_id == work_id,
        WorkMedia.role == role.value,
    ).delete()
    if media_id is not None:
        db.add(WorkMedia(work_id=work_id, media_id=media_id, role=role.value, sort_order=sort_order))


def create_work(db: Session, payload: WorkCreate) -> Work:
    _check_slug_conflict(db, payload.slug)
    work = Work(
        title=payload.title,
        slug=payload.slug,
        type=payload.type.value,
        summary=payload.summary,
        content=payload.content,
        status=payload.status.value,
        category_id=payload.category_id,
        is_featured=payload.is_featured,
        sort_order=payload.sort_order,
        view_count=0,
        published_at=payload.published_at,
    )
    # 首次发布自动补 published_at
    if work.status == WorkStatus.published.value and work.published_at is None:
        work.published_at = utcnow()

    db.add(work)
    db.flush()  # 拿到 id

    # tags
    db.query(WorkTag).filter(WorkTag.work_id == work.id).delete()
    for tid in payload.tag_ids:
        db.add(WorkTag(work_id=work.id, tag_id=tid))

    # media 关联
    _sync_work_media(db, work.id, payload.cover_media_id, MediaRole.cover)
    _sync_work_media(db, work.id, payload.video_media_id, MediaRole.video)
    # gallery：先删再批量插，按 payload 顺序排
    db.query(WorkMedia).filter(
        WorkMedia.work_id == work.id, WorkMedia.role == MediaRole.gallery.value
    ).delete()
    for idx, mid in enumerate(payload.gallery_media_ids):
        db.add(WorkMedia(work_id=work.id, media_id=mid, role=MediaRole.gallery.value, sort_order=idx))

    db.commit()
    db.refresh(work)
    return work


def update_work(db: Session, work_id: int, payload: WorkCreate) -> Work:
    work = db.get(Work, work_id)
    if work is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="作品不存在")
    _check_slug_conflict(db, payload.slug, exclude_id=work_id)

    work.title = payload.title
    work.slug = payload.slug
    work.type = payload.type.value
    work.summary = payload.summary
    work.content = payload.content
    work.status = payload.status.value
    work.category_id = payload.category_id
    work.is_featured = payload.is_featured
    work.sort_order = payload.sort_order
    if payload.published_at is not None:
        work.published_at = payload.published_at
    elif work.status == WorkStatus.published.value and work.published_at is None:
        work.published_at = utcnow()

    # tags
    db.query(WorkTag).filter(WorkTag.work_id == work.id).delete()
    for tid in payload.tag_ids:
        db.add(WorkTag(work_id=work.id, tag_id=tid))

    _sync_work_media(db, work.id, payload.cover_media_id, MediaRole.cover)
    _sync_work_media(db, work.id, payload.video_media_id, MediaRole.video)
    db.query(WorkMedia).filter(
        WorkMedia.work_id == work.id, WorkMedia.role == MediaRole.gallery.value
    ).delete()
    for idx, mid in enumerate(payload.gallery_media_ids):
        db.add(WorkMedia(work_id=work.id, media_id=mid, role=MediaRole.gallery.value, sort_order=idx))

    db.commit()
    db.refresh(work)
    return work


def delete_work(db: Session, work_id: int) -> None:
    work = db.get(Work, work_id)
    if work is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="作品不存在")
    db.delete(work)
    db.commit()


def publish_work(db: Session, work_id: int) -> Work:
    work = db.get(Work, work_id)
    if work is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="作品不存在")
    work.status = WorkStatus.published.value
    if work.published_at is None:
        work.published_at = utcnow()
    db.commit()
    db.refresh(work)
    return work


def unpublish_work(db: Session, work_id: int) -> Work:
    work = db.get(Work, work_id)
    if work is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="作品不存在")
    work.status = WorkStatus.draft.value
    db.commit()
    db.refresh(work)
    return work


# ──────────────────────────────────────────────
# admin 列表的 analytics 聚合
# ──────────────────────────────────────────────

def get_analytics_snapshot(db: Session, work_ids: list[int]) -> dict[int, dict]:
    """返回 {work_id: {"views_today": int, "views_last_7d": int}}。

    SQLite 不支持 FILTER (WHERE ...)，用 CASE WHEN 兼容。
    """
    if not work_ids:
        return {}

    now = datetime.now(UTC)
    today_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
    week_start = today_start - timedelta(days=6)

    stmt = (
        select(
            AnalyticsEvent.work_id,
            func.sum(case((AnalyticsEvent.created_at >= today_start, 1), else_=0)).label("views_today"),
            func.sum(case((AnalyticsEvent.created_at >= week_start, 1), else_=0)).label("views_last_7d"),
        )
        .where(AnalyticsEvent.work_id.in_(work_ids))
        .group_by(AnalyticsEvent.work_id)
    )
    rows = db.execute(stmt).all()
    return {
        wid: {
            "views_today": int(today or 0),
            "views_last_7d": int(last7 or 0),
        }
        for wid, today, last7 in rows
    }


__all__ = [
    "list_works", "get_work_by_slug", "get_work_by_id", "to_detail",
    "register_view",
    "create_work", "update_work", "delete_work",
    "publish_work", "unpublish_work",
    "get_analytics_snapshot",
]
