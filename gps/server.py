"""MCP server — GPS distance calculations using the Haversine formula."""

import logging
import math
import os

from fastmcp import FastMCP  # pylint: disable=import-error

# Configure root logger so library log calls are visible in server output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8101"))

mcp = FastMCP("gps")

# Earth's mean radius in kilometres (IUGG value)
_EARTH_RADIUS_KM = 6371.0088

# 1 nautical mile = 1.852 km (exact, per BIPM)
_KM_PER_NAUTICAL_MILE = 1.852


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in kilometres between two GPS points.

    Uses the Haversine formula, accurate to within ~0.5 % for any pair of
    points on Earth.

    >>> round(_haversine_km(48.8566, 2.3522, 51.5074, -0.1278), 1)
    343.6
    """
    # Convert decimal degrees to radians
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(a))


@mcp.tool()
def distance_between_points(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> dict[str, float]:
    """Calculate the great-circle distance between two GPS coordinates.

    Uses the Haversine formula. Results are returned in both kilometres and
    nautical miles, which is useful for marine, sailing, and wingfoil contexts.

    Args:
        lat1: Latitude of the first point in decimal degrees (−90 to 90).
        lon1: Longitude of the first point in decimal degrees (−180 to 180).
        lat2: Latitude of the second point in decimal degrees (−90 to 90).
        lon2: Longitude of the second point in decimal degrees (−180 to 180).

    Returns:
        A dict with keys ``km`` (kilometres) and ``nm`` (nautical miles),
        both rounded to three decimal places.
    """
    logger.info(
        "Tool called: distance_between_points(lat1=%f, lon1=%f, lat2=%f, lon2=%f)",
        lat1,
        lon1,
        lat2,
        lon2,
    )

    km = _haversine_km(lat1, lon1, lat2, lon2)
    nm = km / _KM_PER_NAUTICAL_MILE

    result = {"km": round(km, 3), "nm": round(nm, 3)}
    logger.info("Distance result: %s", result)
    return result


if __name__ == "__main__":  # pragma: no cover
    logger.info("Starting gps MCP server on %s:%d", HOST, PORT)
    mcp.run(transport="streamable-http", host=HOST, port=PORT)
