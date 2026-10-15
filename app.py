"""Streamlit UI for the Borderless Meeting Planner (SPEC.md §2)."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import streamlit as st

from logic import CITIES, HourStatus, daily_grid, local_clock, overlap_hours

st.set_page_config(page_title="Borderless Meeting Planner", layout="wide")

_CHIPS = {
    "working": ("Working hours", "#3b82f6", "#ffffff"),
    "overlap": ("Overlapping hours", "#16a34a", "#ffffff"),
    "outside": ("Outside working hours", "#e5e7eb", "#374151"),
}
_CELLS = {
    HourStatus.WORKING: ("#bfdbfe", "#1e3a8a"),
    HourStatus.OVERLAP: ("#16a34a", "#ffffff"),
    HourStatus.OUTSIDE: ("#f3f4f6", "#9ca3af"),
}


def _chip_html(kind: str) -> str:
    label, bg, fg = _CHIPS[kind]
    return (
        f"<span style='background:{bg};color:{fg};padding:2px 10px;"
        f"border-radius:4px;font-size:0.8rem'>{label}</span>"
    )


def _hour_cells_html(cells: list[HourStatus]) -> str:
    parts = []
    for hour, status in enumerate(cells):
        bg, fg = _CELLS[status]
        parts.append(
            f"<span style='background:{bg};color:{fg};padding:4px 0;"
            "border-radius:4px;min-width:1.9rem;text-align:center;"
            f"font-size:0.75rem'>{hour:02d}</span>"
        )
    return f"<div style='display:flex;gap:3px;flex-wrap:wrap'>{''.join(parts)}</div>"


st.sidebar.header("Cities")
selected: list = st.sidebar.multiselect(
    "Add or remove cities",
    options=list(CITIES),
    format_func=lambda c: c.name,
    key="cities",
)
st.sidebar.caption(f"{len(selected)} of {len(CITIES)} cities selected")

st.title("Borderless Meeting Planner")
st.caption("Find a window where every city is inside 09:00–17:00 local time.")

now = datetime.now(timezone.utc)
overlap = overlap_hours(now, selected)

col_cities, col_overlap = st.columns(2)
col_cities.metric("Cities", len(selected))
col_overlap.metric("Overlapping hours (next 7 days)", f"{overlap:.1f} h")

if selected and overlap == 0.0:
    st.warning(
        "No overlapping hours: no window in the next 7 days where all "
        "selected cities are within 09:00–17:00 local time."
    )

if selected:
    st.subheader("Local clocks")
    clock_cols = st.columns(min(len(selected), 4))
    for i, city in enumerate(selected):
        clock = local_clock(now, city)
        with clock_cols[i % len(clock_cols)]:
            st.markdown(f"**{clock.city}**")
            st.markdown(
                f"<div style='font-size:2.5rem;font-weight:700;"
                f"line-height:1.2'>{clock.time_str}</div>",
                unsafe_allow_html=True,
            )
            st.caption(clock.badge)

    st.subheader("24-hour local view")
    st.markdown(
        f"{_chip_html('working')} &nbsp; {_chip_html('overlap')} &nbsp; {_chip_html('outside')}",
        unsafe_allow_html=True,
    )
    for city in selected:
        local_now = now.astimezone(ZoneInfo(city.iana_tz))
        st.markdown(f"**{city.name}** — {local_now:%a} {local_now:%Y-%m-%d} local")
        st.markdown(
            _hour_cells_html(daily_grid(local_now.date(), city, selected)),
            unsafe_allow_html=True,
        )
else:
    st.info("Select at least one city in the sidebar to see local clocks and the 24-hour view.")
