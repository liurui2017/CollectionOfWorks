"""FastAPI 入口：应用创建、CORS、静态媒体挂载、启动时初始化管理员、注册路由。"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.db import SessionLocal, engine
from app.core.security import hash_password
from app.models.base import Base
from app.models.site_profile import SiteProfile
from app.models.user import User

settings = get_settings()


def _ensure_admin() -> None:
    """首次启动时若 users 表为空，写入环境变量指定的默认管理员（幂等）。"""
    with SessionLocal() as db:
        existing = db.scalar(select(User).limit(1))
        if existing is None:
            db.add(User(username=settings.ADMIN_USERNAME, password_hash=hash_password(settings.ADMIN_PASSWORD)))
            db.commit()


def _ensure_site_profile() -> None:
    """单行表 site_profile 若不存在则写入默认值（id=1，幂等）。"""
    with SessionLocal() as db:
        sp = db.get(SiteProfile, 1)
        if sp is None:
            db.add(SiteProfile(
                id=1,
                site_name="我的作品集",
                nickname="",
                headline=None,
                bio=None,
                avatar_media_id=None,
                social_links=[],
                footer_text=None,
            ))
            db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 开发期：自动建表；生产用 Alembic 迁移。
    Base.metadata.create_all(bind=engine)
    # 确保媒体目录存在
    Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
    _ensure_admin()
    _ensure_site_profile()
    try:
        yield
    finally:
        pass


def create_app() -> FastAPI:
    # StaticFiles 在 mount 时就会检查目录存在，需提前创建
    Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        description="个人作品集站点后端 — 仅脚手架，业务路由待实现。",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 静态媒体：前端通过 /media/... 直接访问上传的视频与图片
    app.mount(settings.MEDIA_URL_PREFIX, StaticFiles(directory=settings.MEDIA_ROOT), name="media")

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
