"""分类 / 标签业务服务：带 work_count 聚合。"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.relations import WorkTag
from app.models.tag import Tag
from app.models.work import Work
from app.schemas.enums import WorkStatus
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.tag import TagCreate, TagUpdate


# ─────────────────────
# Category
# ─────────────────────

def list_categories(db: Session) -> list[dict]:
    """返回 [{"category": Category, "work_count": int}, ...] 按 sort_order 倒序。"""
    # 聚合已发布作品数
    sub = (
        select(Work.category_id.label("cid"), func.count(Work.id).label("cnt"))
        .where(Work.status == WorkStatus.published.value)
        .group_by(Work.category_id)
        .subquery()
    )
    stmt = (
        select(Category, func.coalesce(sub.c.cnt, 0))
        .outerjoin(sub, Category.id == sub.c.cid)
        .order_by(Category.sort_order.desc(), Category.id.asc())
    )
    return [{"category": cat, "work_count": int(cnt)} for cat, cnt in db.execute(stmt).all()]


def create_category(db: Session, payload: CategoryCreate) -> Category:
    _check_dup(db, Category, payload.slug, payload.name)
    cat = Category(name=payload.name, slug=payload.slug, description=payload.description, sort_order=payload.sort_order)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def update_category(db: Session, cat_id: int, payload: CategoryUpdate) -> Category:
    cat = db.get(Category, cat_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    if payload.name is not None:
        cat.name = payload.name
    if payload.slug is not None:
        cat.slug = payload.slug
    if payload.description is not None:
        cat.description = payload.description
    if payload.sort_order is not None:
        cat.sort_order = payload.sort_order
    db.commit()
    db.refresh(cat)
    return cat


def delete_category(db: Session, cat_id: int) -> None:
    cat = db.get(Category, cat_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    db.delete(cat)
    db.commit()


# ─────────────────────
# Tag
# ─────────────────────

def list_tags(db: Session, *, limit: Optional[int] = None) -> list[dict]:
    """按已发布作品引用数倒序。"""
    wt_sub = select(WorkTag.tag_id.label("tid"), func.count(WorkTag.work_id).label("cnt")).subquery()
    stmt = (
        select(Tag, func.coalesce(wt_sub.c.cnt, 0))
        .outerjoin(wt_sub, Tag.id == wt_sub.c.tid)
        .order_by(func.coalesce(wt_sub.c.cnt, 0).desc(), Tag.id.asc())
    )
    if limit:
        stmt = stmt.limit(limit)
    return [{"tag": tag, "work_count": int(cnt)} for tag, cnt in db.execute(stmt).all()]


def create_tag(db: Session, payload: TagCreate) -> Tag:
    _check_dup(db, Tag, payload.slug, payload.name)
    tag = Tag(name=payload.name, slug=payload.slug)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def update_tag(db: Session, tag_id: int, payload: TagUpdate) -> Tag:
    tag = db.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签不存在")
    if payload.name is not None:
        tag.name = payload.name
    if payload.slug is not None:
        tag.slug = payload.slug
    db.commit()
    db.refresh(tag)
    return tag


def delete_tag(db: Session, tag_id: int) -> None:
    tag = db.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签不存在")
    db.delete(tag)
    db.commit()


# ─────────────────────
# 通用：重名校验
# ─────────────────────

def _check_dup(db: Session, model, slug: str, name: str) -> None:
    stmt = select(model).where(or_(model.slug == slug, model.name == name))
    if db.scalar(stmt) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"名称或 slug 已存在")


__all__ = [
    "list_categories", "create_category", "update_category", "delete_category",
    "list_tags", "create_tag", "update_tag", "delete_tag",
]
