"""Tests for server.py — list_spots and get_spot MCP tools."""

# pylint: disable=duplicate-code,redefined-outer-name,unused-argument

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
    """get_spot must include id, name, region, lat, lon, shore_normal_deg, conditions."""
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
