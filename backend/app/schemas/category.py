"""分类 schema。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class CategoryRef(BaseModel):
    """列表/详情里的紧凑引用，不带聚合字段。"""
    model_config = {"from_attributes": True}
    id: int
    name: str
    slug: str


class CategoryOut(CategoryRef):
    description: str | None = None
    sort_order: int
    work_count: int = 0


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    slug: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    slug: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)
    sort_order: int | None = None


__all__ = ["CategoryRef", "CategoryOut", "CategoryCreate", "CategoryUpdate"]
