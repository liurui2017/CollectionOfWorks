"""公开作品接口：列表 + 详情（详情访问会触发 analytics）。"""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.common import PageMeta, Paginated
from app.schemas.enums import MediaRole, WorkType
from app.schemas.work import WorkDetail, WorkListItem
from app.services import works as works_svc
from app.services.helpers import compute_visitor_hash

router = APIRouter()


@router.get("/works", response_model=Paginated[WorkListItem])
def list_works(
    db: Annotated[Session, Depends(get_db)],
    type: Annotated[Optional[WorkType], Query()] = None,
    category: Annotated[Optional[str], Query(alias="category")] = None,
    tag: Annotated[Optional[str], Query(alias="tag")] = None,
    q: Annotated[Optional[str], Query()] = None,
    featured: Annotated[Optional[bool], Query()] = None,
    sort: Annotated[str, Query()] = "latest",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=60)] = 12,
) -> Paginated[WorkListItem]:
    items, total = works_svc.list_works(
        db,
        include_drafts=False,
        type=type,
        category_slug=category,
        tag_slug=tag,
        q=q,
        featured=featured,
        sort=sort,  # type: ignore[arg-type]  # 内部校验
        page=page,
        page_size=page_size,
    )
    return Paginated(
        items=items,
        meta=PageMeta(page=page, page_size=page_size, total=total, total_pages=max(1, (total + page_size - 1) // page_size)),
    )


@router.get("/works/{slug}", response_model=WorkDetail)
def get_work(
    slug: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> WorkDetail:
    work = works_svc.get_work_by_slug(db, slug, include_drafts=False)
    if work is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="作品不存在")

    # 组装详情（不含 status — 前台看不到）
    detail = works_svc.to_detail(db, work, include_status=False)

    # 匿名浏览量 + analytics
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    cookie = request.cookies.get("_visit")  # 前端种的访客 cookie，没有就 None
    vhash = compute_visitor_hash(ip, ua, cookie)
    referer = request.headers.get("referer")
    works_svc.register_view(
        db,
        work=work,
        path=request.url.path,
        visitor_hash=vhash,
        referer=referer,
        user_agent=ua,
    )

    return detail
