"""小工具：slug 生成、visitor 指纹（SHA-256）、日期截断。"""
from __future__ import annotations

import hashlib
import re
from datetime import UTC, date, datetime

from unidecode import unidecode  # type: ignore[import-not-found]  # 可选，降级就用正则


def _slugify(text: str) -> str:
    """把任意字符串转成 URL 友好的 slug。"""
    # 尝试拼音/unicode 转英文（若未装 unidecode 就直接去非数字字母）
    try:
        text = unidecode(text)  # type: ignore[name-defined]
    except Exception:
        pass
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "untitled"


def slugify(text: str) -> str:
    return _slugify(text)


def compute_visitor_hash(ip: str | None, user_agent: str | None, cookie_id: str | None) -> str:
    """
    访客指纹：不可逆 SHA-256。不存原始 IP，仅用于 UV 区分。
    """
    raw = f"{ip or ''}|{user_agent or ''}|{cookie_id or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def today_utc() -> date:
    return datetime.now(UTC).date()


def utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = ["slugify", "compute_visitor_hash", "today_utc", "utcnow"]
