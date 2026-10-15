"""Domain logic for the Borderless Meeting Planner.

Pure functions over timezone-aware instants; no Streamlit imports here.
See SPEC.md for the rules this module implements.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from enum import Enum
from zoneinfo import ZoneInfo

WORK_START = 9
WORK_END = 17
OVERLAP_WINDOW_DAYS = 7

UTC = timezone.utc


@dataclass(frozen=True)
class City:
    name: str
    iana_tz: str


CITIES: tuple[City, ...] = (
    City("London", "Europe/London"),
    City("Bali", "Asia/Makassar"),
    City("Jakarta", "Asia/Jakarta"),
    City("New York", "America/New_York"),
    City("Los Angeles", "America/Los_Angeles"),
    City("Chicago", "America/Chicago"),
    City("Denver", "America/Denver"),
    City("São Paulo", "America/Sao_Paulo"),
    City("Buenos Aires", "America/Argentina/Buenos_Aires"),
    City("Mexico City", "America/Mexico_City"),
    City("Toronto", "America/Toronto"),
    City("Vancouver", "America/Vancouver"),
    City("Dubai", "Asia/Dubai"),
    City("Mumbai", "Asia/Kolkata"),
    City("Karachi", "Asia/Karachi"),
    City("Singapore", "Asia/Singapore"),
    City("Hong Kong", "Asia/Hong_Kong"),
    City("Shanghai", "Asia/Shanghai"),
    City("Tokyo", "Asia/Tokyo"),
    City("Seoul", "Asia/Seoul"),
    City("Bangkok", "Asia/Bangkok"),
    City("Ho Chi Minh City", "Asia/Ho_Chi_Minh"),
    City("Manila", "Asia/Manila"),
    City("Perth", "Australia/Perth"),
    City("Sydney", "Australia/Sydney"),
    City("Melbourne", "Australia/Melbourne"),
    City("Auckland", "Pacific/Auckland"),
    City("Nairobi", "Africa/Nairobi"),
    City("Cape Town", "Africa/Johannesburg"),
    City("Cairo", "Africa/Cairo"),
    City("Lagos", "Africa/Lagos"),
    City("Istanbul", "Europe/Istanbul"),
    City("Moscow", "Europe/Moscow"),
    City("Berlin", "Europe/Berlin"),
    City("Paris", "Europe/Paris"),
    City("Amsterdam", "Europe/Amsterdam"),
)

CITIES_BY_NAME: dict[str, City] = {city.name: city for city in CITIES}


class HourStatus(str, Enum):
    OUTSIDE = "outside"
    WORKING = "working"
    OVERLAP = "overlap"


@dataclass(frozen=True)
class LocalClock:
    city: str
    time_str: str
    weekday: str
    utc_offset: str

    @property
    def badge(self) -> str:
        return f"↑ {self.weekday} · {self.utc_offset}"


def get_city(name: str) -> City:
    return CITIES_BY_NAME[name]


def _as_utc(instant: datetime) -> datetime:
    if instant.tzinfo is None:
        raise ValueError("instant must be timezone-aware")
    return instant.astimezone(UTC)


def _tz(city: City) -> ZoneInfo:
    return ZoneInfo(city.iana_tz)


def is_working(instant_utc: datetime, city: City) -> bool:
    local = _as_utc(instant_utc).astimezone(_tz(city))
    return WORK_START <= local.hour < WORK_END


def all_working(instant_utc: datetime, cities: list[City]) -> bool:
    if not cities:
        return False
    return all(is_working(instant_utc, city) for city in cities)


def _clip(seg: tuple[datetime, datetime], a: datetime, b: datetime) -> tuple[datetime, datetime] | None:
    s = max(seg[0], a)
    e = min(seg[1], b)
    if s < e:
        return (s, e)
    return None


def _working_segments(city: City, a: datetime, b: datetime) -> list[tuple[datetime, datetime]]:
    """Absolute sub-intervals within [a, b) during which `city` is working."""
    tz = _tz(city)
    first = a.astimezone(tz).date() - timedelta(days=1)
    last = b.astimezone(tz).date() + timedelta(days=1)
    segs: list[tuple[datetime, datetime]] = []
    d = first
    while d <= last:
        ws = datetime.combine(d, time(WORK_START, 0), tzinfo=tz).astimezone(UTC)
        we = datetime.combine(d, time(WORK_END, 0), tzinfo=tz).astimezone(UTC)
        clipped = _clip((ws, we), a, b)
        if clipped is not None:
            segs.append(clipped)
        d += timedelta(days=1)
    return sorted(segs)


def _covers(segs: list[tuple[datetime, datetime]], a: datetime, b: datetime) -> bool:
    """True if the union of `segs` covers the whole interval [a, b)."""
    cursor = a
    for s, e in sorted(segs):
        if s > cursor:
            return False
        if e > cursor:
            cursor = e
        if cursor >= b:
            return True
    return cursor >= b


def _intersect(
    x: list[tuple[datetime, datetime]], y: list[tuple[datetime, datetime]]
) -> list[tuple[datetime, datetime]]:
    out: list[tuple[datetime, datetime]] = []
    i = j = 0
    while i < len(x) and j < len(y):
        s = max(x[i][0], y[j][0])
        e = min(x[i][1], y[j][1])
        if s < e:
            out.append((s, e))
        if x[i][1] < y[j][1]:
            i += 1
        else:
            j += 1
    return out


def hour_status(cell_start_utc: datetime, city: City, cities: list[City]) -> HourStatus:
    a = _as_utc(cell_start_utc)
    b = a + timedelta(hours=1)
    if not _covers(_working_segments(city, a, b), a, b):
        return HourStatus.OUTSIDE
    if cities and all(_covers(_working_segments(c, a, b), a, b) for c in cities):
        if a.date().weekday() < 5:
            return HourStatus.OVERLAP
    return HourStatus.WORKING


def daily_grid(day: date, city: City, cities: list[City]) -> list[HourStatus]:
    tz = _tz(city)
    cells: list[HourStatus] = []
    for h in range(24):
        cell_start_local = datetime.combine(day, time(h, 0), tzinfo=tz)
        cells.append(hour_status(cell_start_local.astimezone(UTC), city, cities))
    return cells


def overlap_hours_on_day(day_utc: date, cities: list[City]) -> float:
    if not cities or day_utc.weekday() >= 5:
        return 0.0
    a = datetime.combine(day_utc, time.min, tzinfo=UTC)
    b = a + timedelta(days=1)
    intervals: list[tuple[datetime, datetime]] = [(a, b)]
    for city in cities:
        intervals = _intersect(intervals, _working_segments(city, a, b))
        if not intervals:
            return 0.0
    return sum((e - s).total_seconds() for s, e in intervals) / 3600.0


def overlap_hours(now_utc: datetime, cities: list[City]) -> float:
    if not cities:
        return 0.0
    today = _as_utc(now_utc).date()
    total = 0.0
    for i in range(OVERLAP_WINDOW_DAYS):
        total += overlap_hours_on_day(today + timedelta(days=i), cities)
    return total


def _format_offset(offset: timedelta) -> str:
    total = int(offset.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    hours, rem = divmod(total, 3600)
    minutes = rem // 60
    if minutes:
        return f"UTC{sign}{hours}:{minutes:02d}"
    return f"UTC{sign}{hours}"


def local_clock(now_utc: datetime, city: City) -> LocalClock:
    local = _as_utc(now_utc).astimezone(_tz(city))
    return LocalClock(
        city=city.name,
        time_str=local.strftime("%H:%M:%S"),
        weekday=local.strftime("%A"),
        utc_offset=_format_offset(local.utcoffset() or timedelta(0)),
    )
