"""管理端作品接口：CRUD + 发布/撤稿 + 列表（含 analytics 聚合）。"""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import PageMeta, Paginated
from app.schemas.enums import WorkStatus, WorkType
from app.schemas.work import WorkCreate, WorkDetail, WorkListItem
from app.services import works as works_svc

router = APIRouter()


@router.get("/works", response_model=Paginated[WorkListItem])
def admin_list(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
    status_filter: Annotated[Optional[WorkStatus], Query(alias="status")] = None,
    type: Annotated[Optional[WorkType], Query()] = None,
    category_id: Annotated[Optional[int], Query()] = None,
    q: Annotated[Optional[str], Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=60)] = 12,
) -> Paginated[WorkListItem]:
    items, total = works_svc.list_works(
        db,
        include_drafts=True,
        type=type,
        q=q,
        page=page,
        page_size=page_size,
        admin_category_id=category_id,
        status_filter=status_filter,
        sort="latest",
    )

    # 把 analytics 聚合贴到 items 的 model_dump 会破坏 schema；先只返回 items，
    # 如后端要带 views_today / views_last_7d，需要 WorkListItem schema 扩展字段或用另一个 response model。
    # v1 保持契约不变，聚合数据先不对外暴露（service 已留好接口）。
    return Paginated(
        items=items,
        meta=PageMeta(page=page, page_size=page_size, total=total, total_pages=max(1, (total + page_size - 1) // page_size)),
    )


@router.post("/works", response_model=WorkDetail, status_code=status.HTTP_201_CREATED)
def create(
    payload: WorkCreate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> WorkDetail:
    work = works_svc.create_work(db, payload)
    return works_svc.to_detail(db, work, include_status=True)


@router.get("/works/{work_id}", response_model=WorkDetail)
def get(
    work_id: int,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> WorkDetail:
    work = works_svc.get_work_by_id(db, work_id)
    if work is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="作品不存在")
    return works_svc.to_detail(db, work, include_status=True)


@router.put("/works/{work_id}", response_model=WorkDetail)
def update(
    work_id: int,
    payload: WorkCreate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> WorkDetail:
    work = works_svc.update_work(db, work_id, payload)
    return works_svc.to_detail(db, work, include_status=True)


@router.delete("/works/{work_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    work_id: int,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> None:
    works_svc.delete_work(db, work_id)


@router.post("/works/{work_id}/publish", response_model=WorkDetail)
def publish(
    work_id: int,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> WorkDetail:
    work = works_svc.publish_work(db, work_id)
    return works_svc.to_detail(db, work, include_status=True)


@router.post("/works/{work_id}/unpublish", response_model=WorkDetail)
def unpublish(
    work_id: int,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> WorkDetail:
    work = works_svc.unpublish_work(db, work_id)
    return works_svc.to_detail(db, work, include_status=True)
