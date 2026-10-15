"""Acceptance tests for logic.py (SPEC.md §6, TC1–TC10)."""

from datetime import date, datetime, timezone
from zoneinfo import available_timezones

import pytest

from logic import (
    CITIES,
    HourStatus,
    all_working,
    daily_grid,
    get_city,
    is_working,
    local_clock,
    overlap_hours,
    overlap_hours_on_day,
)

UTC = timezone.utc

# Reference clock from the screenshot: Tue 2026-10-13 15:22:21 UTC
NOW = datetime(2026, 10, 13, 15, 22, 21, tzinfo=UTC)

LONDON = get_city("London")
BALI = get_city("Bali")


def utc(y, m, d, hh, mm=0, ss=0):
    return datetime(y, m, d, hh, mm, ss, tzinfo=UTC)


def test_tc1_catalog_has_36_unique_cities_with_valid_timezones():
    assert len(CITIES) == 36
    names = [c.name for c in CITIES]
    assert len(set(names)) == len(names)
    zones = available_timezones()
    for c in CITIES:
        assert c.iana_tz in zones, f"{c.name}: unknown zone {c.iana_tz}"
    assert get_city("London").iana_tz == "Europe/London"
    assert get_city("Bali").iana_tz == "Asia/Makassar"


def test_tc2_local_clocks_match_reference():
    london = local_clock(NOW, LONDON)
    assert london.city == "London"
    assert london.time_str == "16:22:21"
    assert london.weekday == "Tuesday"
    assert london.utc_offset == "UTC+1"
    assert london.badge == "↑ Tuesday · UTC+1"

    bali = local_clock(NOW, BALI)
    assert bali.city == "Bali"
    assert bali.time_str == "23:22:21"
    assert bali.weekday == "Tuesday"
    assert bali.utc_offset == "UTC+8"
    assert bali.badge == "↑ Tuesday · UTC+8"


@pytest.mark.parametrize(
    "instant,expected",
    [
        (utc(2026, 10, 13, 7, 59, 59), False),  # London local 08:59:59
        (utc(2026, 10, 13, 8, 0, 0), True),  # London local 09:00:00
        (utc(2026, 10, 13, 15, 59, 59), True),  # London local 16:59:59
        (utc(2026, 10, 13, 16, 0, 0), False),  # London local 17:00:00
    ],
)
def test_tc3_working_hour_boundaries(instant, expected):
    assert is_working(instant, LONDON) is expected


def test_tc4_daily_grid_matches_reference_screenshot():
    cities = [LONDON, BALI]
    day = date(2026, 10, 13)

    london = daily_grid(day, LONDON, cities)
    assert len(london) == 24
    assert london[9] is HourStatus.OVERLAP
    assert all(london[h] is HourStatus.WORKING for h in range(10, 17))
    assert all(
        london[h] is HourStatus.OUTSIDE for h in list(range(0, 9)) + list(range(17, 24))
    )

    bali = daily_grid(day, BALI, cities)
    assert len(bali) == 24
    assert bali[16] is HourStatus.OVERLAP
    assert all(bali[h] is HourStatus.WORKING for h in range(9, 16))
    assert all(
        bali[h] is HourStatus.OUTSIDE for h in list(range(0, 9)) + list(range(17, 24))
    )


def test_tc5_overlap_hours_next_7_days_london_bali():
    assert overlap_hours(NOW, [LONDON, BALI]) == 5.0


def test_tc6_weekend_suppresses_overlap():
    cities = [LONDON, BALI]
    assert overlap_hours_on_day(date(2026, 10, 17), cities) == 0.0  # Saturday
    assert overlap_hours_on_day(date(2026, 10, 18), cities) == 0.0  # Sunday
    saturday_grid = daily_grid(date(2026, 10, 17), LONDON, cities)
    assert HourStatus.OVERLAP not in saturday_grid
    assert saturday_grid[9] is HourStatus.WORKING  # blue band remains
    assert overlap_hours_on_day(date(2026, 10, 19), cities) == 1.0  # Monday


def test_tc7_disjoint_cities_have_zero_overlap():
    cities = [get_city("Dubai"), get_city("Los Angeles")]
    assert overlap_hours(NOW, cities) == 0.0
    grid = daily_grid(date(2026, 10, 13), get_city("Dubai"), cities)
    assert HourStatus.OVERLAP not in grid
    assert grid[9] is HourStatus.WORKING  # own working band still blue


def test_tc8_fractional_offset_overlap():
    cities = [LONDON, get_city("Mumbai")]
    assert overlap_hours_on_day(date(2026, 10, 13), cities) == 3.5
    assert overlap_hours(NOW, cities) == 17.5

    london = daily_grid(date(2026, 10, 13), LONDON, cities)
    green_london = {h for h, s in enumerate(london) if s is HourStatus.OVERLAP}
    assert green_london == {9, 10, 11}

    mumbai = daily_grid(date(2026, 10, 13), get_city("Mumbai"), cities)
    green_mumbai = {h for h, s in enumerate(mumbai) if s is HourStatus.OVERLAP}
    assert green_mumbai == {14, 15, 16}
    assert mumbai[13] is HourStatus.WORKING  # only half-overlapped


def test_tc9_dst_transition_changes_overlap():
    cities = [LONDON, BALI]
    assert overlap_hours_on_day(date(2026, 10, 20), cities) == 1.0  # BST, UTC+1
    assert overlap_hours_on_day(date(2026, 10, 26), cities) == 0.0  # GMT, UTC+0
    assert HourStatus.OVERLAP not in daily_grid(date(2026, 10, 26), LONDON, cities)
    assert local_clock(utc(2026, 10, 24, 12, 0), LONDON).utc_offset == "UTC+1"
    assert local_clock(utc(2026, 10, 26, 12, 0), LONDON).utc_offset == "UTC+0"


def test_tc10_empty_selection_has_no_overlap():
    assert overlap_hours(NOW, []) == 0.0
    assert overlap_hours_on_day(date(2026, 10, 13), []) == 0.0
    assert all_working(NOW, []) is False
