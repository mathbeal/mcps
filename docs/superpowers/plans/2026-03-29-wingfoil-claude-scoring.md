# Wingfoil — Claude-driven spot scoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hardcoded wingfoil scoring engine with two async MCP tools that expose raw spot data so Claude can reason and rank spots itself.

**Architecture:** `database.py` becomes a pure async data layer (load, aggregate, lookup). `server.py` exposes two FastMCP async tools: `list_spots` (paginated, monthly stats) and `get_spot` (full 365-day detail). All scoring logic is deleted.

**Tech Stack:** Python 3.14, FastMCP ≥ 2.0, asyncio, pytest, pytest-cov

---

## File map

| File | Action | Responsibility |
|---|---|---|
| `wingfoil/database.py` | Rewrite | Async load/cache, monthly aggregation, spot lookup by ID |
| `wingfoil/server.py` | Rewrite | Two async MCP tools: `list_spots`, `get_spot` |
| `wingfoil/tests/test_database.py` | Rewrite | Tests for all three database functions |
| `wingfoil/tests/test_server.py` | Rewrite | Tests for both MCP tools + tool registration |

---

## Task 1: Rewrite test_database.py (failing tests for new database API)

**Files:**
- Modify: `wingfoil/tests/test_database.py`

- [ ] **Step 1: Replace the entire file with tests for the new API**

```python
"""Tests for database.py — async load, monthly aggregation, spot lookup."""

from __future__ import annotations

import asyncio
import math
from typing import Any

import pytest

import database


# ---------------------------------------------------------------------------
# Helpers & fixtures
# ---------------------------------------------------------------------------


def _make_spot(
    spot_id: str = "test-001",
    name: str = "Test Spot",
    *,
    wind_speed: float = 15.0,
    wind_dir: float = 180.0,
    wave_height: float = 1.0,
) -> dict[str, Any]:
    """Build a minimal spot dict with 365 identical days."""
    return {
        "id": spot_id,
        "name": name,
        "region": "Test",
        "lat": 47.0,
        "lon": -3.0,
        "shore_normal_deg": 270.0,
        "conditions": [
            {
                "day_of_year": i + 1,
                "wind_speed_knots": wind_speed,
                "wind_direction_deg": wind_dir,
                "wave_height_m": wave_height,
            }
            for i in range(365)
        ],
    }


@pytest.fixture(autouse=True)
def reset_db_cache() -> None:
    """Reset the in-memory database cache before every test."""
    database._DB = None  # pylint: disable=protected-access


# ---------------------------------------------------------------------------
# load_db
# ---------------------------------------------------------------------------


def test_load_db_returns_30_spots() -> None:
    """load_db must load the real windspots.json with exactly 30 spots."""
    spots = asyncio.run(database.load_db())
    assert len(spots) == 30


def test_load_db_all_spots_have_365_days() -> None:
    """Every spot loaded from JSON must have exactly 365 daily conditions."""
    spots = asyncio.run(database.load_db())
    assert all(len(s["conditions"]) == 365 for s in spots)


def test_load_db_cache_hit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Second call to load_db must not read the file again (cache hit)."""
    call_count = 0

    original_read = database._read_json  # pylint: disable=protected-access

    def counting_read() -> list[dict[str, Any]]:
        nonlocal call_count
        call_count += 1
        return original_read()

    monkeypatch.setattr(database, "_read_json", counting_read)
    asyncio.run(database.load_db())
    asyncio.run(database.load_db())
    assert call_count == 1  # file read only once


def test_load_db_missing_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """load_db must raise FileNotFoundError when the database file is missing."""
    from pathlib import Path  # pylint: disable=import-outside-toplevel

    monkeypatch.setattr(database, "_DB_PATH", Path("/nonexistent/windspots.json"))
    with pytest.raises(FileNotFoundError):
        asyncio.run(database.load_db())


# ---------------------------------------------------------------------------
# aggregate_monthly
# ---------------------------------------------------------------------------


def test_aggregate_monthly_has_12_months() -> None:
    """aggregate_monthly must return exactly 12 month keys."""
    spot = _make_spot()
    stats = database.aggregate_monthly(spot)
    assert set(stats.keys()) == {str(m) for m in range(1, 13)}


def test_aggregate_monthly_uniform_spot() -> None:
    """All months must have the same avg wind speed when conditions are uniform."""
    spot = _make_spot(wind_speed=20.0)
    stats = database.aggregate_monthly(spot)
    for month_stats in stats.values():
        assert month_stats["wind_speed_avg"] == pytest.approx(20.0, abs=0.01)
        assert month_stats["wind_speed_min"] == pytest.approx(20.0, abs=0.01)
        assert month_stats["wind_speed_max"] == pytest.approx(20.0, abs=0.01)


def test_aggregate_monthly_wave_stats() -> None:
    """wave_height_avg and wave_height_max must be correct for uniform conditions."""
    spot = _make_spot(wave_height=1.5)
    stats = database.aggregate_monthly(spot)
    for month_stats in stats.values():
        assert month_stats["wave_height_avg"] == pytest.approx(1.5, abs=0.01)
        assert month_stats["wave_height_max"] == pytest.approx(1.5, abs=0.01)


def test_aggregate_monthly_circular_mean_wraps() -> None:
    """Circular mean of 359° and 1° must be ~0°, not 180°."""
    # Only the first 2 days (in January) have the edge-case directions
    conditions = [
        {"day_of_year": 1, "wind_speed_knots": 15.0, "wind_direction_deg": 359.0, "wave_height_m": 1.0},
        {"day_of_year": 2, "wind_speed_knots": 15.0, "wind_direction_deg": 1.0, "wave_height_m": 1.0},
        *[
            {"day_of_year": i, "wind_speed_knots": 15.0, "wind_direction_deg": 180.0, "wave_height_m": 1.0}
            for i in range(3, 366)
        ],
    ]
    spot = {
        "id": "wrap-test",
        "name": "Wrap Test",
        "region": "Test",
        "lat": 47.0,
        "lon": -3.0,
        "shore_normal_deg": 270.0,
        "conditions": conditions,
    }
    stats = database.aggregate_monthly(spot)
    jan_dir = stats["1"]["wind_dir_avg"]
    # Circular mean of 359° and 1° is ~0° — must NOT be near 180°
    assert jan_dir < 5.0 or jan_dir > 355.0


def test_aggregate_monthly_result_keys() -> None:
    """Each month entry must have all required keys."""
    spot = _make_spot()
    stats = database.aggregate_monthly(spot)
    required = {"wind_speed_avg", "wind_speed_min", "wind_speed_max", "wind_dir_avg",
                "wave_height_avg", "wave_height_max"}
    for month_stats in stats.values():
        assert required <= month_stats.keys()


# ---------------------------------------------------------------------------
# get_spot_by_id
# ---------------------------------------------------------------------------


def test_get_spot_by_id_returns_correct_spot(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_spot_by_id must return the spot whose id matches."""
    fake_db = [_make_spot("spot-001", "Alpha"), _make_spot("spot-002", "Beta")]
    monkeypatch.setattr(database, "_DB", fake_db)
    result = asyncio.run(database.get_spot_by_id("spot-002"))
    assert result["name"] == "Beta"


def test_get_spot_by_id_raises_key_error_for_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_spot_by_id must raise KeyError for an unknown spot_id."""
    monkeypatch.setattr(database, "_DB", [_make_spot("spot-001")])
    with pytest.raises(KeyError):
        asyncio.run(database.get_spot_by_id("nonexistent"))
```

- [ ] **Step 2: Run tests to confirm they all fail**

```bash
cd /home/mathieu/MCPs/wingfoil && python -m pytest tests/test_database.py -v 2>&1 | head -40
```

Expected: ImportError or multiple FAILED — `load_db`, `aggregate_monthly`, `get_spot_by_id` don't exist yet.

---

## Task 2: Rewrite database.py

**Files:**
- Modify: `wingfoil/database.py`

- [ ] **Step 1: Replace the entire file**

```python
"""Wingfoil spot database — async loading, monthly aggregation, and spot lookup."""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import math
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DB_PATH = Path(__file__).parent / "data" / "windspots.json"
_DB: list[dict[str, Any]] | None = None


def _read_json() -> list[dict[str, Any]]:
    """Read and parse the windspots JSON file from disk.

    >>> isinstance(_read_json(), list)
    True
    """
    logger.debug("Reading spot database from %s", _DB_PATH)
    return json.loads(_DB_PATH.read_text(encoding="utf-8"))


async def load_db() -> list[dict[str, Any]]:
    """Load and cache the spot database, reading from disk only on first call."""
    global _DB  # noqa: PLW0603  # pylint: disable=global-statement
    if _DB is None:
        # Offload blocking file I/O to a thread so the event loop is not blocked
        _DB = await asyncio.to_thread(_read_json)
        logger.info("Loaded %d spots from database", len(_DB))
    return _DB


def _days_in_month(month: int) -> list[int]:
    """Return day_of_year values (1–365) for the given month in a non-leap year.

    Uses year 2001 (non-leap) for a consistent 365-day mapping.

    >>> _days_in_month(1)[0], _days_in_month(1)[-1], len(_days_in_month(1))
    (1, 31, 31)
    """
    if not 1 <= month <= 12:
        raise ValueError(f"month must be 1–12, got {month}")
    year = 2001  # non-leap year for consistent mapping
    start = datetime.date(year, month, 1)
    end = (
        datetime.date(year, 12, 31)
        if month == 12
        else datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    )
    result: list[int] = []
    current = start
    while current <= end:
        result.append(current.timetuple().tm_yday)
        current += datetime.timedelta(days=1)
    return result


def aggregate_monthly(spot: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Compute per-month aggregated stats for a spot.

    Returns a dict keyed by month number (string "1"–"12"), each with:
    wind_speed_avg, wind_speed_min, wind_speed_max, wind_dir_avg (circular),
    wave_height_avg, wave_height_max.
    """
    conditions: list[dict[str, Any]] = spot["conditions"]
    result: dict[str, dict[str, float]] = {}

    for month in range(1, 13):
        month_day_set = set(_days_in_month(month))
        # Filter conditions to only those whose day falls in this month
        mc = [c for c in conditions if c["day_of_year"] in month_day_set]
        if not mc:
            logger.warning("No conditions found for month %d in spot %s", month, spot.get("id"))
            continue

        speeds = [float(c["wind_speed_knots"]) for c in mc]
        waves = [float(c["wave_height_m"]) for c in mc]
        # Circular mean: convert to unit vectors, average, then back to degrees
        dirs_rad = [math.radians(float(c["wind_direction_deg"])) for c in mc]
        n = len(mc)
        sin_mean = sum(math.sin(r) for r in dirs_rad) / n
        cos_mean = sum(math.cos(r) for r in dirs_rad) / n
        dir_avg = math.degrees(math.atan2(sin_mean, cos_mean)) % 360.0

        result[str(month)] = {
            "wind_speed_avg": round(sum(speeds) / n, 2),
            "wind_speed_min": round(min(speeds), 2),
            "wind_speed_max": round(max(speeds), 2),
            "wind_dir_avg": round(dir_avg, 2),
            "wave_height_avg": round(sum(waves) / n, 2),
            "wave_height_max": round(max(waves), 2),
        }

    logger.debug("Aggregated monthly stats for spot %s", spot.get("id"))
    return result


async def get_spot_by_id(spot_id: str) -> dict[str, Any]:
    """Return the spot with the given id, or raise KeyError if not found."""
    spots = await load_db()
    for spot in spots:
        if spot["id"] == spot_id:
            logger.debug("Found spot %s", spot_id)
            return spot
    logger.warning("Spot not found: %s", spot_id)
    raise KeyError(spot_id)
```

- [ ] **Step 2: Run database tests**

```bash
cd /home/mathieu/MCPs/wingfoil && python -m pytest tests/test_database.py -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
cd /home/mathieu/MCPs/wingfoil && git add database.py tests/test_database.py
git commit -m "refactor(wingfoil): replace scoring engine with async data layer"
```

---

## Task 3: Rewrite test_server.py (failing tests for new tool API)

**Files:**
- Modify: `wingfoil/tests/test_server.py`

- [ ] **Step 1: Replace the entire file with tests for the new tools**

```python
"""Tests for server.py — list_spots and get_spot MCP tools."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

import database
import server


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_spot(spot_id: str, name: str) -> dict[str, Any]:
    """Build a minimal spot with 365 uniform days."""
    return {
        "id": spot_id,
        "name": name,
        "region": "Test",
        "lat": 47.0,
        "lon": -3.0,
        "shore_normal_deg": 270.0,
        "conditions": [
            {
                "day_of_year": i + 1,
                "wind_speed_knots": 15.0,
                "wind_direction_deg": 180.0,
                "wave_height_m": 1.0,
            }
            for i in range(365)
        ],
    }


@pytest.fixture()
def fake_db(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Inject 12 fake spots into the database cache."""
    spots = [_make_spot(f"spot-{i:03d}", f"Spot {i}") for i in range(12)]
    monkeypatch.setattr(database, "_DB", spots)
    return spots


@pytest.fixture(autouse=True)
def reset_db_cache() -> None:
    """Reset cache before every test to avoid cross-test contamination."""
    database._DB = None  # pylint: disable=protected-access


# ---------------------------------------------------------------------------
# list_spots — pagination
# ---------------------------------------------------------------------------


def test_list_spots_total_matches_db(fake_db: list[dict[str, Any]]) -> None:
    """total field must equal the number of spots in the database."""
    result = asyncio.run(server.list_spots(page=1, page_size=5))
    assert result["total"] == 12


def test_list_spots_first_page_count(fake_db: list[dict[str, Any]]) -> None:
    """First page with page_size=5 must return exactly 5 spots."""
    result = asyncio.run(server.list_spots(page=1, page_size=5))
    assert len(result["spots"]) == 5


def test_list_spots_last_page_partial(fake_db: list[dict[str, Any]]) -> None:
    """Last page of 12 spots with page_size=5 must return the remaining 2 spots."""
    result = asyncio.run(server.list_spots(page=3, page_size=5))
    assert len(result["spots"]) == 2


def test_list_spots_out_of_range_page(fake_db: list[dict[str, Any]]) -> None:
    """A page beyond the last must return an empty spots list."""
    result = asyncio.run(server.list_spots(page=99, page_size=5))
    assert result["spots"] == []
    assert result["total"] == 12


def test_list_spots_page_metadata(fake_db: list[dict[str, Any]]) -> None:
    """Response must include page and page_size reflecting the request."""
    result = asyncio.run(server.list_spots(page=2, page_size=3))
    assert result["page"] == 2
    assert result["page_size"] == 3


# ---------------------------------------------------------------------------
# list_spots — spot shape
# ---------------------------------------------------------------------------


def test_list_spots_spot_has_monthly_stats(fake_db: list[dict[str, Any]]) -> None:
    """Each spot in the response must contain monthly_stats with 12 months."""
    result = asyncio.run(server.list_spots(page=1, page_size=1))
    spot = result["spots"][0]
    assert "monthly_stats" in spot
    assert len(spot["monthly_stats"]) == 12


def test_list_spots_spot_has_required_keys(fake_db: list[dict[str, Any]]) -> None:
    """Each spot must include id, name, region, lat, lon, shore_normal_deg, monthly_stats."""
    required = {"id", "name", "region", "lat", "lon", "shore_normal_deg", "monthly_stats"}
    result = asyncio.run(server.list_spots(page=1, page_size=5))
    for spot in result["spots"]:
        assert required <= spot.keys()


def test_list_spots_no_raw_conditions(fake_db: list[dict[str, Any]]) -> None:
    """list_spots must NOT include the raw 365-day conditions array."""
    result = asyncio.run(server.list_spots(page=1, page_size=5))
    for spot in result["spots"]:
        assert "conditions" not in spot


# ---------------------------------------------------------------------------
# get_spot
# ---------------------------------------------------------------------------


def test_get_spot_returns_full_conditions(fake_db: list[dict[str, Any]]) -> None:
    """get_spot must return the spot with its 365-day conditions array."""
    result = asyncio.run(server.get_spot("spot-000"))
    assert result["id"] == "spot-000"
    assert len(result["conditions"]) == 365


def test_get_spot_has_metadata(fake_db: list[dict[str, Any]]) -> None:
    """get_spot must include id, name, region, lat, lon, shore_normal_deg."""
    required = {"id", "name", "region", "lat", "lon", "shore_normal_deg", "conditions"}
    result = asyncio.run(server.get_spot("spot-001"))
    assert required <= result.keys()


def test_get_spot_unknown_id_returns_error(fake_db: list[dict[str, Any]]) -> None:
    """get_spot with an unknown id must return a dict with an 'error' key."""
    result = asyncio.run(server.get_spot("does-not-exist"))
    assert "error" in result


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def test_tools_registered() -> None:
    """Both MCP tools must be registered on the server instance."""
    tool_names = [t.name for t in asyncio.run(server.mcp.list_tools())]
    assert "list_spots" in tool_names
    assert "get_spot" in tool_names
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /home/mathieu/MCPs/wingfoil && python -m pytest tests/test_server.py -v 2>&1 | head -40
```

Expected: ImportError or FAILED — `list_spots`, `get_spot` don't exist yet.

---

## Task 4: Rewrite server.py

**Files:**
- Modify: `wingfoil/server.py`

- [ ] **Step 1: Replace the entire file**

```python
"""MCP server — French wingfoil spots, raw data for Claude to reason about."""

from __future__ import annotations

import logging
import os
from typing import Any

from fastmcp import FastMCP  # pylint: disable=import-error

import database

# Root logger so library log calls appear in server output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8103"))

mcp = FastMCP("wingfoil")


@mcp.tool()
async def list_spots(
    page: int = 1,
    page_size: int = 5,
) -> dict[str, Any]:
    """List French wingfoil spots with monthly aggregated stats, paginated.

    Each spot includes id, name, region, coordinates, shore_normal_deg, and
    monthly_stats: per-month avg/min/max wind speed, circular-mean wind direction,
    avg/max wave height.

    Use this tool to browse all spots and identify candidates worth inspecting in detail.
    Iterate through pages until you have seen enough spots to reason about.
    """
    logger.info("Tool called: list_spots(page=%d, page_size=%d)", page, page_size)
    spots = await database.load_db()
    total = len(spots)
    # Slice the correct page (0-indexed offset)
    start = (page - 1) * page_size
    page_spots = spots[start : start + page_size]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "spots": [
            {
                "id": s["id"],
                "name": s["name"],
                "region": s["region"],
                "lat": s["lat"],
                "lon": s["lon"],
                "shore_normal_deg": s["shore_normal_deg"],
                # Aggregated stats: compact summary, no raw daily data
                "monthly_stats": database.aggregate_monthly(s),
            }
            for s in page_spots
        ],
    }


@mcp.tool()
async def get_spot(spot_id: str) -> dict[str, Any]:
    """Get full 365-day conditions for a specific wingfoil spot.

    Returns id, name, region, coordinates, shore_normal_deg, and a conditions
    array of 365 entries (day_of_year, wind_speed_knots, wind_direction_deg,
    wave_height_m).

    Use this to inspect detailed daily conditions for candidates identified via list_spots.
    Returns {"error": "<message>"} if spot_id is unknown.
    """
    logger.info("Tool called: get_spot(spot_id=%r)", spot_id)
    try:
        return await database.get_spot_by_id(spot_id)
    except KeyError:
        logger.warning("get_spot called with unknown spot_id=%r", spot_id)
        return {"error": f"Unknown spot_id: {spot_id!r}"}


if __name__ == "__main__":  # pragma: no cover
    logger.info("Starting wingfoil MCP server on %s:%d", HOST, PORT)
    mcp.run(transport="streamable-http", host=HOST, port=PORT)
```

- [ ] **Step 2: Run all wingfoil tests**

```bash
cd /home/mathieu/MCPs/wingfoil && python -m pytest tests/ -v
```

Expected: all tests PASS, coverage ≥ 95%.

- [ ] **Step 3: Run pre-commit hooks**

```bash
cd /home/mathieu/MCPs/wingfoil && pre-commit run --files database.py server.py tests/test_database.py tests/test_server.py
```

Expected: all hooks pass (black, isort, mypy, pylint, xenon, pytest).

- [ ] **Step 4: Commit**

```bash
cd /home/mathieu/MCPs/wingfoil && git add server.py tests/test_server.py
git commit -m "feat(wingfoil): expose raw spot data via async list_spots and get_spot tools"
```
