# AGENTS.md

## Project state

Spec-first: `SPEC.md` defines features, data structures, and acceptance criteria.
- `logic.py` — pure domain logic (no Streamlit imports).
- `app.py` — Streamlit UI (entrypoint; uses only `logic.py` for domain work).
- `test_logic.py` — acceptance tests TC1–TC10.
- `test_app.py` — app-layer tests via `streamlit.testing.v1.AppTest` (TC13; TC11–TC12 not written yet).

## Environment

- Python 3.14 venv at `.venv/` (created with system Python 3.14).
- Activate (Windows): `.venv\Scripts\activate` (PowerShell) or `.\.venv\Scripts\Activate.ps1`.
- Key packages already installed: `streamlit`, `uvicorn`, `starlette`, `pandas`, `numpy`, `altair`, `pytest`, `requests`, `tzdata` (required for `zoneinfo` on Windows).
- No lint/typecheck scripts defined yet; run tools via `.venv\Scripts\python.exe` or activate first.

## Commands

- App: `.venv\Scripts\streamlit.exe run app.py` (from repo root).
- Tests: `.venv\Scripts\python.exe -m pytest -q` (from repo root; no config file, defaults apply).

## Conventions

- Domain rules live in `logic.py` exactly as written in `SPEC.md`; change both together, keep `test_logic.py` green.
- Instants passed to `logic.py` must be timezone-aware; tests freeze `NOW = 2026-10-13T15:22:21Z` for reference values.
