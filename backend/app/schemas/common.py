"""通用包装：分页、错误体。"""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    meta: PageMeta


class ErrorOut(BaseModel):
    detail: str


__all__ = ["PageMeta", "Paginated", "ErrorOut"]
