"""枚举定义 — Pydantic 用 `str, Enum`，序列化后前端直接拿到字符串联合。"""
from __future__ import annotations

from enum import Enum


class WorkType(str, Enum):
    video = "video"         # 短视频
    article = "article"     # Markdown 文章
    note = "note"           # 纯文本短文
    gallery = "gallery"     # 图集


class WorkStatus(str, Enum):
    draft = "draft"
    published = "published"


class MediaKind(str, Enum):
    image = "image"
    video = "video"


class MediaRole(str, Enum):
    cover = "cover"
    video = "video"
    gallery = "gallery"


__all__ = ["WorkType", "WorkStatus", "MediaKind", "MediaRole"]
