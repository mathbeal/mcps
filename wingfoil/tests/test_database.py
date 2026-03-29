"""Tests for database.py — async load, monthly aggregation, and spot lookup."""

# pylint: disable=duplicate-code

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

import database

# ---------------------------------------------------------------------------
# Helpers & fixtures
# ---------------------------------------------------------------------------


# Local helper — builds a minimal spot dict with configurable wind/wave parameters
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

    _rj = database._read_json  # pylint: disable=protected-access
    original_read: Callable[[], list[dict[str, Any]]] = _rj

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
        {
            "day_of_year": 1,
            "wind_speed_knots": 15.0,
            "wind_direction_deg": 359.0,
            "wave_height_m": 1.0,
        },
        {
            "day_of_year": 2,
            "wind_speed_knots": 15.0,
            "wind_direction_deg": 1.0,
            "wave_height_m": 1.0,
        },
        *[
            {
                "day_of_year": i,
                "wind_speed_knots": 15.0,
                "wind_direction_deg": 180.0,
                "wave_height_m": 1.0,
            }
            for i in range(32, 366)  # start from Feb (day 32) so January only has days 1 & 2
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
    required = {
        "wind_speed_avg",
        "wind_speed_min",
        "wind_speed_max",
        "wind_dir_avg",
        "wave_height_avg",
        "wave_height_max",
    }
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


# ---------------------------------------------------------------------------
# _days_in_month (error path)
# ---------------------------------------------------------------------------


def test_days_in_month_invalid_month_zero() -> None:
    """_days_in_month with month=0 must raise ValueError."""
    with pytest.raises(ValueError, match="month must be 1"):
        database._days_in_month(0)  # pylint: disable=protected-access


def test_days_in_month_invalid_month_13() -> None:
    """_days_in_month with month=13 must raise ValueError."""
    with pytest.raises(ValueError, match="month must be 1"):
        database._days_in_month(13)  # pylint: disable=protected-access


# ---------------------------------------------------------------------------
# aggregate_monthly (empty month branch)
# ---------------------------------------------------------------------------


def test_aggregate_monthly_skips_month_with_no_conditions() -> None:
    """aggregate_monthly must skip a month that has no matching conditions."""
    # Build a spot with only February conditions (days 32–59) — January has no entries
    feb_start = 32  # first day of February in a non-leap year
    feb_end = 59  # last day of February in a non-leap year
    conditions = [
        {
            "day_of_year": i,
            "wind_speed_knots": 15.0,
            "wind_direction_deg": 180.0,
            "wave_height_m": 1.0,
        }
        for i in range(feb_start, feb_end + 1)
    ]
    spot = {
        "id": "sparse-test",
        "name": "Sparse",
        "region": "Test",
        "lat": 47.0,
        "lon": -3.0,
        "shore_normal_deg": 270.0,
        "conditions": conditions,
    }
    stats = database.aggregate_monthly(spot)
    # January (month "1") must be absent because no conditions for those days
    assert "1" not in stats
    # February (month "2") must be present
    assert "2" in stats
