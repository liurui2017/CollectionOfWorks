"""分类 / 标签：公开列表 + 管理 CRUD。"""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.schemas.tag import TagCreate, TagOut, TagUpdate
from app.services import catalog as cat_svc

router = APIRouter()


# ───────────── 公开 ─────────────

@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Annotated[Session, Depends(get_db)]) -> list[CategoryOut]:
    rows = cat_svc.list_categories(db)
    return [
        CategoryOut(
            id=r["category"].id,
            name=r["category"].name,
            slug=r["category"].slug,
            description=r["category"].description,
            sort_order=r["category"].sort_order,
            work_count=r["work_count"],
        )
        for r in rows
    ]


@router.get("/tags", response_model=list[TagOut])
def list_tags(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
) -> list[TagOut]:
    rows = cat_svc.list_tags(db, limit=limit)
    return [
        TagOut(id=r["tag"].id, name=r["tag"].name, slug=r["tag"].slug, work_count=r["work_count"])
        for r in rows
    ]


# ───────────── 管理 ─────────────

@router.post("/admin/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> CategoryOut:
    cat = cat_svc.create_category(db, payload)
    return CategoryOut(
        id=cat.id, name=cat.name, slug=cat.slug, description=cat.description, sort_order=cat.sort_order, work_count=0
    )


@router.put("/admin/categories/{cat_id}", response_model=CategoryOut)
def update_category(
    cat_id: int,
    payload: CategoryUpdate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> CategoryOut:
    cat = cat_svc.update_category(db, cat_id, payload)
    return CategoryOut(
        id=cat.id, name=cat.name, slug=cat.slug, description=cat.description, sort_order=cat.sort_order, work_count=0
    )


@router.delete("/admin/categories/{cat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    cat_id: int,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> None:
    cat_svc.delete_category(db, cat_id)


@router.post("/admin/tags", response_model=TagOut, status_code=status.HTTP_201_CREATED)
def create_tag(
    payload: TagCreate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> TagOut:
    tag = cat_svc.create_tag(db, payload)
    return TagOut(id=tag.id, name=tag.name, slug=tag.slug, work_count=0)


@router.put("/admin/tags/{tag_id}", response_model=TagOut)
def update_tag(
    tag_id: int,
    payload: TagUpdate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> TagOut:
    tag = cat_svc.update_tag(db, tag_id, payload)
    return TagOut(id=tag.id, name=tag.name, slug=tag.slug, work_count=0)


@router.delete("/admin/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> None:
    cat_svc.delete_tag(db, tag_id)
