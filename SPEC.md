# SPEC.md — Borderless Meeting Planner

## 1. Overview

A Streamlit app that helps teams find a meeting window across cities in different
time zones.

- Stack: Python 3.14, Streamlit 1.66, pytest 9.1.1.
- Time zones: stdlib `zoneinfo` + `tzdata` (Windows has no IANA database of its own).
- This spec defines the domain logic (`logic.py`), its data structures, and the
  acceptance criteria (`test_logic.py` maps to §6, TC1–TC10; `test_app.py` maps
  to the app-layer cases TC13, while TC11–TC12 remain to be written).

## 2. UI layout (reference: provided screenshot)

- **Sidebar — "Cities"**: help text *Add or remove cities*; a chip multiselect
  (removable chips, e.g. `London ×` `Bali ×`); caption `N of 36 cities selected`.
- **Main**:
  - H1 `Borderless Meeting Planner`.
  - Subtitle `Find a window where every city is inside 09:00–17:00 local time.`
  - Metrics row: `Cities` (integer count) and
    `Overlapping hours (next 7 days)` (formatted to one decimal, e.g. `5.0 h`).
  - **Local clocks**: one card per selected city — city name, `HH:MM:SS` in large
    type, badge `↑ {weekday} · {UTC offset}` (e.g. `↑ Tuesday · UTC+1`).
    Clocks reflect the current time at each rerun (update on interaction only;
    no auto-refresh dependency).
  - **24-hour local view**: legend chips — `Working hours` (blue),
    `Overlapping hours` (green), `Outside working hours` (gray); then one row per
    city labelled `{City} — {Www} {YYYY-MM-DD} local` followed
    by 24 hour cells `00`–`23`.

## 3. Features

- **F1 — City catalog & selection**: a fixed catalog of exactly 36 cities with
  IANA time zones (§5). Users add/remove cities via the sidebar chips.
  Empty selection is allowed (see F6).
- **F2 — Metrics**: `Cities` = number of selected cities.
  `Overlapping hours (next 7 days)` = total hours in the next 7 days when *all*
  selected cities are inside working hours, displayed with one decimal (`5.0 h`).
  If the metric is `0.0 h` while at least one city is selected, the app shows a
  warning (empty selection never warns).
- **F3 — Local clocks**: current `HH:MM:SS`, weekday, and UTC offset per selected
  city, refreshed on interaction only.
- **F4 — 24-hour local view**: for each selected city, 24 hourly cells for that
  city's current local date, each cell classified `outside` / `working` (blue) /
  `overlap` (green).
- **F5 — Domain rules**: see §4.
- **F6 — Empty state**: 0 cities selected → `Cities` = `0`, overlap = `0.0 h`,
  no clock cards, no grid rows.

## 4. Domain rules

- Working hours: local time in the half-open interval **09:00 ≤ t < 17:00**.
  Cell `09` covers 09:00–10:00 (working); cell `17` starts at 17:00 (outside).
- An **hour cell** for city C on local date D is the absolute instant range
  `[D h:00 local, D h+1:00 local)` converted to UTC.
- Cell statuses:
  - `OUTSIDE` — the city is not working for the whole cell.
  - `WORKING` (blue) — the city is working for the whole cell, but it is not a
    full-cell overlap of all cities. Blue is a wall-clock fact and also appears
    on weekends.
  - `OVERLAP` (green) — **every** selected city is working for the whole cell,
    **and** the cell's UTC start date is a weekday (Mon–Fri). Weekend instants
    never produce overlap (global simplification; no per-city weekend calendars).
- An **overlap instant** is one where all selected cities are simultaneously
  inside their local working hours; overlap durations are exact (minute-level),
  not rounded to hours. Empty selection ⇒ no overlap.
- The 7-day metric: for the 7 UTC calendar dates `today … today+6` (today =
  UTC date of *now*), sum the overlap duration falling on each date; weekend
  dates contribute 0.
- All times derive from IANA zones per instant, so DST transitions are handled
  automatically (e.g. Europe/London leaves BST on 2026-10-25, changing the
  London–Bali overlap from 1 h/day to 0 h/day).
- Badges show the city's actual current local weekday (the screenshot's
  `Monday` badge against grid date `Tue 2026-10-13` is a mock inconsistency;
  tests use the real weekday).
- All instants passed to logic functions must be timezone-aware; they are
  normalized to UTC internally.

## 5. Data structures

### City

| Field     | Type | Meaning                                   |
|-----------|------|-------------------------------------------|
| `name`    | str  | Display name, unique in the catalog        |
| `iana_tz` | str  | IANA zone key, resolvable via `zoneinfo`   |

`CITIES` — ordered tuple of the 36 catalog cities:

| # | City | IANA zone | # | City | IANA zone |
|---|------|-----------|---|------|-----------|
| 1 | London | Europe/London | 19 | Tokyo | Asia/Tokyo |
| 2 | Bali | Asia/Makassar | 20 | Seoul | Asia/Seoul |
| 3 | Jakarta | Asia/Jakarta | 21 | Bangkok | Asia/Bangkok |
| 4 | New York | America/New_York | 22 | Ho Chi Minh City | Asia/Ho_Chi_Minh |
| 5 | Los Angeles | America/Los_Angeles | 23 | Manila | Asia/Manila |
| 6 | Chicago | America/Chicago | 24 | Perth | Australia/Perth |
| 7 | Denver | America/Denver | 25 | Sydney | Australia/Sydney |
| 8 | São Paulo | America/Sao_Paulo | 26 | Melbourne | Australia/Melbourne |
| 9 | Buenos Aires | America/Argentina/Buenos_Aires | 27 | Auckland | Pacific/Auckland |
| 10 | Mexico City | America/Mexico_City | 28 | Nairobi | Africa/Nairobi |
| 11 | Toronto | America/Toronto | 29 | Cape Town | Africa/Johannesburg |
| 12 | Vancouver | America/Vancouver | 30 | Cairo | Africa/Cairo |
| 13 | Dubai | Asia/Dubai | 31 | Lagos | Africa/Lagos |
| 14 | Mumbai | Asia/Kolkata | 32 | Istanbul | Europe/Istanbul |
| 15 | Karachi | Asia/Karachi | 33 | Moscow | Europe/Moscow |
| 16 | Singapore | Asia/Singapore | 34 | Berlin | Europe/Berlin |
| 17 | Hong Kong | Asia/Hong_Kong | 35 | Paris | Europe/Paris |
| 18 | Shanghai | Asia/Shanghai | 36 | Amsterdam | Europe/Amsterdam |

### Enums & view models

- `HourStatus` — `OUTSIDE` | `WORKING` | `OVERLAP` (string enum).
- `LocalClock` — `city`, `time_str` (`"16:22:21"`), `weekday` (`"Tuesday"`),
  `utc_offset` (`"UTC+1"`, `"UTC+5:30"`), derived `badge`
  (`"↑ Tuesday · UTC+1"`).

### Constants

`WORK_START = 9`, `WORK_END = 17`, `OVERLAP_WINDOW_DAYS = 7`.

### Function contracts (implemented in `logic.py`)

| Function | Args → Returns | Notes |
|----------|----------------|-------|
| `is_working` | `(instant_utc, city) → bool` | local hour in `[9, 17)` |
| `all_working` | `(instant_utc, cities) → bool` | `False` for empty list |
| `hour_status` | `(cell_start_utc, city, cities) → HourStatus` | cell = 1 h from `cell_start_utc`; green needs full-cell overlap + weekday |
| `daily_grid` | `(day, city, cities) → list[HourStatus]` | 24 entries for the city's local date `day` |
| `overlap_hours_on_day` | `(day_utc, cities) → float` | exact hours within `day_utc 00:00–24:00` UTC; `0.0` if weekend or empty |
| `overlap_hours` | `(now_utc, cities) → float` | sum over `today … today+6` (UTC dates), weekends `0.0` |
| `local_clock` | `(now_utc, city) → LocalClock` | F3 fields |

## 6. Acceptance criteria (example test cases)

### TC1 — Catalog integrity
- **Given** the city catalog
- **When** it is inspected
- **Then** it contains exactly 36 unique names, every `iana_tz` resolves via
  `zoneinfo`, `London → Europe/London`, and `Bali → Asia/Makassar`.

### TC2 — Local clocks (reference values)
- **Given** frozen now = `2026-10-13T15:22:21Z`
- **When** clocks are computed for London and Bali
- **Then** London shows `16:22:21`, `Tuesday`, `UTC+1`, badge
  `↑ Tuesday · UTC+1`; Bali shows `23:22:21`, `Tuesday`, `UTC+8`.

### TC3 — Working-hour boundaries (London, BST)
- **Given** instants just inside/outside the local window
- **When** `is_working` is evaluated
- **Then** local 08:59:59 → not working, 09:00:00 → working,
  16:59:59 → working, 17:00:00 → not working.

### TC4 — 24-hour grid matches the screenshot
- **Given** frozen now = `2026-10-13T15:22:21Z`, cities = [London, Bali],
  grid date `2026-10-13`
- **When** `daily_grid` is computed for each city
- **Then** London: cell `09` → overlap, cells `10–16` → working, all others →
  outside; Bali: cells `09–15` → working, cell `16` → overlap, all others →
  outside; each grid has exactly 24 cells.

### TC5 — Overlapping hours, next 7 days
- **Given** frozen now = `2026-10-13T15:22:21Z`, cities = [London, Bali]
- **When** the 7-day metric is computed
- **Then** it equals `5.0` (5 weekdays × 1 h overlap; Sat 17 + Sun 18 excluded).

### TC6 — Weekends suppress overlap
- **Given** cities = [London, Bali]
- **When** overlap is evaluated for Sat `2026-10-17`, Sun `2026-10-18`, and the
  Saturday grid
- **Then** both days return `0.0 h`, the Saturday grid contains no
  `OVERLAP` cells (blue working cells may remain), and Mon `2026-10-19`
  returns `1.0 h`.

### TC7 — Disjoint cities
- **Given** cities = [Dubai (UTC+4), Los Angeles (UTC−7 in October)] — 11 h
  apart, so their 8 h windows never intersect
- **When** overlap and the daily grid are computed
- **Then** the metric is `0.0 h`, no cell is `OVERLAP`, and Dubai's own
  working cells remain `WORKING` (blue).

### TC8 — Fractional offsets
- **Given** cities = [London, Mumbai (UTC+5:30)]
- **When** overlap is evaluated on `2026-10-13` and for the 7-day metric
- **Then** the daily overlap is `3.5 h` (`08:00–11:30Z`), the metric is
  `17.5 h`, London's green cells are `{9, 10, 11}`, Mumbai's green cells are
  `{14, 15, 16}`, and Mumbai cell `13` (only half-overlapped) stays `WORKING`.

### TC9 — DST transition
- **Given** cities = [London, Bali] around the EU DST end (2026-10-25)
- **When** overlap is evaluated on Mon `2026-10-20` (BST, UTC+1) and Mon
  `2026-10-26` (GMT, UTC+0)
- **Then** Oct 20 returns `1.0 h`, Oct 26 returns `0.0 h` (offset exactly 8 h —
  windows only touch), the Oct 26 grid has no `OVERLAP` cells, and London's
  offset label changes from `UTC+1` to `UTC+0`.

### TC10 — Empty selection
- **Given** no cities selected
- **When** overlap functions are called
- **Then** `overlap_hours` and `overlap_hours_on_day` return `0.0`, and
  `all_working` on an empty list is `False`.

### TC11 — UI layout (app layer, future `test_app.py`)
- **Given** the app starts with an empty session
- **When** it renders
- **Then** the sidebar lists the 36 catalog cities, the title, subtitle, metric
  labels (`Cities`, `Overlapping hours (next 7 days)`), the three legend chips,
  and the per-city row label format `{City} — {Www} {YYYY-MM-DD} local`
  are present.

### TC12 — UI interaction (app layer, future `test_app.py`)
- **Given** the running app
- **When** the user selects London and Bali
- **Then** the caption shows `2 of 36 cities selected`, `Cities` = `2`,
  the overlap metric shows `5.0 h` (at the reference clock), two clock cards
  and two 24-cell grid rows render; deselecting everything returns the F6
  empty state.

### TC13 — Zero-overlap warning (app layer, `test_app.py`)
- **Given** the running app with Tokyo (UTC+9) and London selected — 8 h apart,
  so their 8 h working windows never intersect
- **When** the metrics render
- **Then** the overlap metric shows `0.0 h` and exactly one warning is
  displayed (message contains `No overlapping hours`); **and** no warning is
  shown when the overlap is positive (e.g. London + Bali) or when no cities
  are selected.

## 7. Non-goals

- No persistence, accounts, or sharing links.
- No per-city weekend calendars (weekends are a global Mon–Fri rule).
- No sub-hour grid cells (metric is exact, but the grid is hourly).
- No auto-refresh of clocks and no date picker (each row shows that city's
  current local date).
- No meetings shorter/longer than whole-hour grid cells.
