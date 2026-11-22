"""IST clock. Everything date-related in Vaani is Asia/Kolkata (matches vaani_today() in SQL).

Tests can monkeypatch `now_ist` to pin the time.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
WINDOW_DAYS = 7  # slots exist for today .. today + 6


def now_ist() -> datetime:
    return datetime.now(IST)


def today_ist() -> date:
    return now_ist().date()


def window() -> tuple[date, date]:
    t = today_ist()
    return t, t + timedelta(days=WINDOW_DAYS - 1)


def in_window(d: date) -> bool:
    lo, hi = window()
    return lo <= d <= hi


def is_past(d: date, t: time) -> bool:
    return datetime.combine(d, t, IST) <= now_ist()


def iso_ts(dt: datetime | None = None) -> str:
    return (dt or now_ist()).isoformat(timespec="seconds")
