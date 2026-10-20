"""媒体上传服务：校验、存盘、写 Media 记录。

v1 策略：
- 图片 ≤ 10MB，视频 ≤ 2GB（config 里可改）
- MIME 白名单：image/jpeg, image/png, image/webp, image/gif；video/mp4, video/quicktime, video/webm
- 文件名：UUID + 原扩展名，按 YYYY/MM/ 分目录
- v1 不做 ffprobe，width/height/duration_seconds 全部留空（避免引入 ffmpeg 依赖）
"""
from __future__ import annotations

import mimetypes
import uuid
from datetime import datetime
from pathlib import Path
from typing import Tuple

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.media import Media

settings = get_settings()

IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
VIDEO_MIMES = {"video/mp4", "video/quicktime", "video/webm"}
ALLOWED_MIMES = IMAGE_MIMES | VIDEO_MIMES


def _validate(mime: str, size: int) -> None:
    if mime not in ALLOWED_MIMES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"不支持的文件类型：{mime}。允许：{sorted(ALLOWED_MIMES)}",
        )
    if mime in IMAGE_MIMES and size > settings.MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"图片最大 {settings.MAX_IMAGE_SIZE_BYTES // 1024 // 1024}MB",
        )
    if mime in VIDEO_MIMES and size > settings.MAX_VIDEO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"视频最大 {settings.MAX_VIDEO_SIZE_BYTES // 1024 // 1024 // 1024}GB",
        )


def _build_storage_path(filename: str, now: datetime) -> Tuple[Path, str]:
    """返回 (磁盘绝对路径, 供数据库存的 url 路径如 /media/2026/09/xxx.mp4)。"""
    year = f"{now.year:04d}"
    month = f"{now.month:02d}"
    subdir = Path(year) / month
    abs_dir = Path(settings.MEDIA_ROOT) / subdir
    abs_dir.mkdir(parents=True, exist_ok=True)
    abs_path = abs_dir / filename
    url = f"{settings.MEDIA_URL_PREFIX}/{year}/{month}/{filename}"
    return abs_path, url


async def save_upload(db: Session, file: UploadFile) -> Media:
    """校验 MIME + 大小 → 生成 UUID 文件名 → 落盘 → 写 Media 记录。"""
    # 读取全部内容（v1 单文件上传，先简单处理；大文件流式写入可后续升级）
    content = await file.read()
    size = len(content)

    mime = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
    _validate(mime, size)

    ext = Path(file.filename or "file").suffix.lower() or mimetypes.guess_extension(mime) or ""
    new_filename = f"{uuid.uuid4().hex}{ext}"
    now = datetime.now()
    abs_path, url = _build_storage_path(new_filename, now)

    abs_path.write_bytes(content)

    kind = "image" if mime in IMAGE_MIMES else "video"
    media = Media(
        kind=kind,
        filename=new_filename,
        original_name=file.filename or new_filename,
        url=url,
        mime_type=mime,
        size_bytes=size,
        width=None,
        height=None,
        duration_seconds=None,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def delete_media_file(media: Media) -> None:
    """从磁盘删文件（不删 DB 记录；由调用方决定是否级联删 DB）。"""
    try:
        root = Path(settings.MEDIA_ROOT).resolve()
        # media.url 形如 /media/2026/09/xxx.jpg → 相对 root 的 2026/09/xxx.jpg
        rel = Path(*Path(media.url).parts[2:])  # 跳过 /media/
        abs_path = (root / rel).resolve()
        if root in abs_path.parents or abs_path == root:  # 防越界
            abs_path.unlink(missing_ok=True)
    except Exception:
        # 删文件失败不应阻断接口
        pass


__all__ = ["save_upload", "delete_media_file"]
