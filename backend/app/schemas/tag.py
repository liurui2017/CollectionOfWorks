"""标签 schema。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class TagRef(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    slug: str


class TagOut(TagRef):
    work_count: int = 0


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    slug: str = Field(min_length=1, max_length=50)


class TagUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    slug: str | None = Field(default=None, min_length=1, max_length=50)


__all__ = ["TagRef", "TagOut", "TagCreate", "TagUpdate"]
