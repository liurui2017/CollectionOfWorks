"""契约层统一导出。所有路由应从本模块引入 schema，避免路径混乱。"""
from app.schemas.common import ErrorOut, PageMeta, Paginated
from app.schemas.enums import MediaKind, MediaRole, WorkStatus, WorkType
from app.schemas.auth import AdminUserOut, LoginRequest, TokenOut
from app.schemas.media import MediaOut
from app.schemas.category import CategoryOut, CategoryRef, CategoryCreate, CategoryUpdate
from app.schemas.tag import TagOut, TagRef, TagCreate, TagUpdate
from app.schemas.work import (
    WorkAnalyticsSnapshot,
    WorkCreate,
    WorkDetail,
    WorkListItem,
    WorkUpdate,
)
from app.schemas.site import (
    SiteProfileOut,
    SiteProfileUpdate,
    SocialLink,
)

__all__ = [
    # common
    "ErrorOut", "PageMeta", "Paginated",
    # enums
    "WorkType", "WorkStatus", "MediaKind", "MediaRole",
    # auth
    "LoginRequest", "TokenOut", "AdminUserOut",
    # media
    "MediaOut",
    # category
    "CategoryOut", "CategoryRef", "CategoryCreate", "CategoryUpdate",
    # tag
    "TagOut", "TagRef", "TagCreate", "TagUpdate",
    # work
    "WorkListItem", "WorkDetail", "WorkCreate", "WorkUpdate", "WorkAnalyticsSnapshot",
    # site
    "SocialLink", "SiteProfileOut", "SiteProfileUpdate",
]
