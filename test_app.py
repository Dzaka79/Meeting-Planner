"""App-layer acceptance tests for app.py (SPEC.md §6)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from logic import get_city

APP_PATH = str(Path(__file__).parent / "app.py")


def _app() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception
    return at


def test_tc13_no_overlap_tokyo_london_shows_warning():
    at = _app()
    at.multiselect[0].set_value([get_city("Tokyo"), get_city("London")])
    at.run()
    assert not at.exception
    assert at.metric[1].value == "0.0 h"
    assert len(at.warning) == 1
    assert "No overlapping hours" in at.warning[0].value


def test_no_warning_when_overlap_exists_or_no_cities_selected():
    at = _app()
    assert len(at.warning) == 0  # empty selection (F6) must not warn
    at.multiselect[0].set_value([get_city("London"), get_city("Bali")])
    at.run()
    assert not at.exception
    assert len(at.warning) == 0  # London + Bali overlap, so no warning


def test_legend_chips_show_labels():
    at = _app()
    at.multiselect[0].set_value([get_city("London"), get_city("Bali")])
    at.run()
    assert not at.exception
    legend = next(
        m.value for m in at.markdown if isinstance(m.value, str) and "Working hours" in m.value
    )
    assert "Overlapping hours" in legend
    assert "Outside working hours" in legend
    assert "{label}" not in legend
