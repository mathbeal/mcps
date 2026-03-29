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
        _DB = await asyncio.to_thread(_read_json)  # pylint: disable=no-member
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
        month_conds = [c for c in conditions if c["day_of_year"] in month_day_set]
        if not month_conds:
            logger.warning("No conditions found for month %d in spot %s", month, spot.get("id"))
            continue

        speeds = [float(c["wind_speed_knots"]) for c in month_conds]
        waves = [float(c["wave_height_m"]) for c in month_conds]
        # Circular mean: convert to unit vectors, average, then back to degrees
        dirs_rad = [math.radians(float(c["wind_direction_deg"])) for c in month_conds]
        count = len(month_conds)
        sin_mean = sum(math.sin(r) for r in dirs_rad) / count
        cos_mean = sum(math.cos(r) for r in dirs_rad) / count
        dir_avg = math.degrees(math.atan2(sin_mean, cos_mean)) % 360.0

        result[str(month)] = {
            "wind_speed_avg": round(sum(speeds) / count, 2),
            "wind_speed_min": round(min(speeds), 2),
            "wind_speed_max": round(max(speeds), 2),
            "wind_dir_avg": round(dir_avg, 2),
            "wave_height_avg": round(sum(waves) / count, 2),
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
