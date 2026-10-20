"""媒体资源 schema。"""
from __future__ import annotations

from pydantic import BaseModel

from app.schemas.enums import MediaKind


class MediaOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    kind: MediaKind
    url: str
    original_name: str
    mime_type: str
    size_bytes: int
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None


__all__ = ["MediaOut"]
