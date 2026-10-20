"""应用全局配置。所有可配置项通过环境变量注入，生产环境禁止硬编码。"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 应用
    APP_NAME: str = "CollectionOfWorks"
    APP_VERSION: str = "0.1.0"
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:3000",
        ]
    )

    # 数据库 — 默认 SQLite（本地开发零依赖），生产切 PostgreSQL
    DATABASE_URL: str = "sqlite:///./collection.db"

    # JWT 鉴权
    JWT_SECRET: str = "change-me-in-production-please"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # 管理员初始化（首次启动时若 users 表为空则自动写入）
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change-me-on-first-login"

    # 媒体上传
    MEDIA_ROOT: str = "./media"
    MEDIA_URL_PREFIX: str = "/media"
    MAX_IMAGE_SIZE_BYTES: int = 10 * 1024 * 1024   # 10 MB
    MAX_VIDEO_SIZE_BYTES: int = 2 * 1024 * 1024 * 1024  # 2 GB


@lru_cache
def get_settings() -> Settings:
    return Settings()
