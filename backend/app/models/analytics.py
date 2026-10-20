"""访问事件（浏览量数据底座）。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)   # work_view
    work_id: Mapped[int | None] = mapped_column(ForeignKey("works.id", ondelete="SET NULL"), nullable=True)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    visitor_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256，不可逆
    referer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_events_work_day", "work_id", "created_at"),
        Index("idx_events_created", "created_at"),
        Index("idx_events_visitor", "visitor_hash", "created_at"),
    )


__all__ = ["AnalyticsEvent"]
