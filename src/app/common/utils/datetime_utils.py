"""
날짜/시간 유틸리티
"""

from datetime import datetime, timezone
from typing import Any

from zoneinfo import ZoneInfo


# 한국 시간대
KST = ZoneInfo("Asia/Seoul")


def utc_now() -> datetime:
    """현재 UTC 시간 반환"""
    return datetime.now(timezone.utc)


def kst_now() -> datetime:
    """현재 KST(한국 시간) 반환"""
    return datetime.now(KST)


def to_utc(dt: datetime) -> datetime:
    """datetime을 UTC로 변환"""
    if dt.tzinfo is None:
        # naive datetime을 UTC로 가정
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_kst(dt: datetime) -> datetime:
    """datetime을 KST로 변환"""
    if dt.tzinfo is None:
        # naive datetime을 UTC로 가정 후 변환
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KST)


def format_datetime(
    dt: datetime,
    fmt: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """datetime을 문자열로 포맷"""
    return dt.strftime(fmt)


def format_iso(dt: datetime) -> str:
    """datetime을 ISO 8601 형식으로 포맷"""
    return dt.isoformat()


def parse_datetime(
    value: str,
    fmt: str | None = None,
) -> datetime:
    """
    문자열을 datetime으로 파싱

    Args:
        value: 날짜 문자열
        fmt: 포맷 문자열 (None이면 ISO 8601로 파싱)

    Returns:
        datetime 객체
    """
    if fmt:
        return datetime.strptime(value, fmt)
    return datetime.fromisoformat(value)


def timestamp_to_datetime(ts: int | float) -> datetime:
    """Unix timestamp를 datetime으로 변환"""
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def datetime_to_timestamp(dt: datetime) -> float:
    """datetime을 Unix timestamp로 변환"""
    return dt.timestamp()


def serialize_datetime(dt: datetime | None) -> str | None:
    """JSON 직렬화용 datetime 변환"""
    if dt is None:
        return None
    return format_iso(dt)


def deserialize_datetime(value: Any) -> datetime | None:
    """JSON 역직렬화용 datetime 변환"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return parse_datetime(value)
    raise ValueError(f"Cannot convert {type(value)} to datetime")

