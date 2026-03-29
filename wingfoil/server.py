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
PORT = int(os.getenv("PORT", "8102"))

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
