# Wingfoil MCP — Design Spec

**Date:** 2026-03-28
**Status:** Approved

## Overview

A FastMCP server exposing two tools that help find the best consecutive 5-day windows for wingfoiling in France. Data is a static JSON fake database of 30 French spots, each with 365 days of wind conditions. No external API calls.

---

## Data Model

### `data/windspots.json`

Array of 30 spot objects. Each spot:

```json
{
  "id": "spot-001",
  "name": "La Torche",
  "region": "Bretagne",
  "lat": 47.84,
  "lon": -4.34,
  "conditions": [
    {
      "day_of_year": 1,
      "wind_speed_knots": 18.5,
      "wind_direction_deg": 270,
      "wave_height_m": 1.2
    }
  ]
}
```

`conditions` has exactly 365 entries (day_of_year 1–365).

### Scoring Formula (0–100 per day)

Each day is scored across three criteria:

| Criterion | Weight | Ideal range | Notes |
|---|---|---|---|
| Wind speed | 50 pts | 18–25 knots | Tapers off below 12 and above 35; 0 pts at 0 or ≥40 |
| Wind direction | 30 pts | Cross-shore (within ±45° of shore normal) | Offshore penalized; onshore acceptable |
| Wave height | 20 pts | 0.5–1.5 m | Flat (<0.3m) and big (>3m) penalized |

**5-day window score** = arithmetic mean of the 5 daily scores.

---

## Module Structure

```
wingfoil/
├── data/
│   └── windspots.json        # 30 spots × 365 days
├── tests/
│   ├── __init__.py
│   └── test_database.py      # unit tests for database.py logic
├── database.py               # load JSON, scoring, window search
├── server.py                 # FastMCP tools only
├── pyproject.toml
├── .pre-commit-config.yaml   # black, isort, mypy, pylint
├── Dockerfile
└── README.md
```

---

## `database.py` — Public API

```python
def score_day(day: dict) -> float:
    """Score a single day's conditions, returning 0.0–100.0."""

def best_window(spot: dict, month: int | None = None) -> dict:
    """
    Find the best consecutive 5-day window for a spot.
    If month is given, restrict search to windows where ALL 5 days fall within that calendar month.
    Returns: {spot_id, spot_name, region, start_day, end_day, score, days: [...]}
    """

def top_spots(n: int = 5, month: int | None = None) -> list[dict]:
    """
    Rank all 30 spots by their best 5-day window score.
    Returns top N spots descending by score.
    """
```

Internal helpers (not exported): `_load_db()`, `_days_in_month(month)`, `_score_wind_speed()`, `_score_wind_direction()`, `_score_wave_height()`.

---

## `server.py` — MCP Tools

```python
@mcp.tool()
def best_wingfoil_spots(n: int = 5) -> list[dict]:
    """Find the top N French wingfoil spots with their best 5-day wind window across the year."""

@mcp.tool()
def best_wingfoil_spots_by_month(month: int, n: int = 5) -> list[dict]:
    """Find top N French wingfoil spots for a given month (1–12), best consecutive 5 days."""
```

Port: **8004**. Transport: `streamable-http`.

---

## Unit Tests (`tests/test_database.py`)

| Test | What it verifies |
|---|---|
| `test_score_day_ideal_conditions` | Day with 20 kn, cross-shore, 1.0m wave scores ≥ 80 |
| `test_score_day_no_wind` | Day with 0 kn scores ≤ 10 |
| `test_score_day_huge_waves` | Day with 5m waves scores ≤ 40 |
| `test_best_window_returns_5_days` | Returned window always contains exactly 5 days |
| `test_best_window_month_filter` | All 5 days fall within the requested month |
| `test_best_window_higher_than_random` | Best window score ≥ any random 5-day average |
| `test_top_spots_length` | Returns exactly N results |
| `test_top_spots_ordered` | Results sorted descending by score |
| `test_top_spots_default_n` | Default N=5 returns 5 results |

---

## Tooling

### `pyproject.toml`

```toml
[project]
name = "mcp-wingfoil"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = ["fastmcp>=2.0"]

[dependency-groups]
dev = ["pytest>=8.0", "black>=24.0", "isort>=5.0", "mypy>=1.0", "pylint>=3.0", "pre-commit>=3.8"]

[tool.black]
line-length = 100

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
strict = true
python_version = "3.14"

[tool.pylint.messages_control]
max-line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### `.pre-commit-config.yaml`

Hooks run in order: `isort` → `black` → `mypy` → `pylint`.

---

## Docker

**`Dockerfile`** — base: `ghcr.io/astral-sh/uv:python3.14-bookworm-slim`. Installs `fastmcp`, copies `server.py`, `database.py`, `data/`. Exposes port 8004.

**`docker-compose.yml`** — add `wingfoil` service, port `8004:8004`, same pattern as existing services.

---

## Fake Data Generation

The `data/windspots.json` file is generated with realistic French coastal spots. Wind conditions follow seasonal patterns:
- Atlantic coast (Bretagne, Vendée): stronger winds Oct–Mar, moderate Apr–Sep
- Mediterranean (PACA, Languedoc): Mistral peaks Nov–Mar, Tramontane in Roussillon year-round
- Channel (Normandie): regular westerlies year-round
- Basque Country: westerly swells Sep–Apr

Each spot has a `shore_normal_deg` (used for direction scoring) that reflects actual coastline orientation.
