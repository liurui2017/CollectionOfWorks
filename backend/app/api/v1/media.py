"""媒体上传 + 删除。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.media import Media
from app.models.relations import WorkMedia
from app.models.user import User
from app.schemas.media import MediaOut
from app.services.upload import delete_media_file, save_upload

router = APIRouter()


@router.post("/media", response_model=MediaOut, status_code=status.HTTP_201_CREATED)
async def upload(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> MediaOut:
    media = await save_upload(db, file)
    return MediaOut.model_validate(media)


@router.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    media_id: int,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(get_current_user)],
) -> None:
    media = db.get(Media, media_id)
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="媒体不存在")
    # 检查是否被作品引用
    used = db.scalar(select(WorkMedia.id).where(WorkMedia.media_id == media_id).limit(1))
    if used is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该媒体正被作品引用，无法删除",
        )
    delete_media_file(media)
    db.delete(media)
    db.commit()
