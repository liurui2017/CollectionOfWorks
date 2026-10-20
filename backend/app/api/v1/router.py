"""API v1 总路由。路由模块各自 Router，这里统一 include。"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, public_works, admin_works, catalog, site, media

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(public_works.router, prefix="", tags=["works"])
api_router.include_router(admin_works.router, prefix="/admin", tags=["admin-works"])
api_router.include_router(catalog.router, prefix="", tags=["catalog"])
api_router.include_router(site.router, prefix="", tags=["site"])
api_router.include_router(media.router, prefix="/admin", tags=["admin-media"])

__all__ = ["api_router"]
