"""Unit tests for server.py — GPS distance MCP tool."""

# pylint: disable=redefined-outer-name,protected-access

import asyncio
import math

import pytest

import server

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def paris() -> tuple[float, float]:
    """GPS coordinates of Paris, France."""
    return (48.8566, 2.3522)


@pytest.fixture()
def london() -> tuple[float, float]:
    """GPS coordinates of London, United Kingdom."""
    return (51.5074, -0.1278)


@pytest.fixture()
def same_point() -> tuple[float, float]:
    """A single GPS point used for zero-distance tests."""
    return (43.2965, 5.3698)  # Marseille


# ---------------------------------------------------------------------------
# _haversine_km (internal helper)
# ---------------------------------------------------------------------------


def test_haversine_paris_london(paris: tuple[float, float], london: tuple[float, float]) -> None:
    """Paris-London distance must be approximately 343 km."""
    km = server._haversine_km(*paris, *london)  # pylint: disable=protected-access
    assert 341.0 < km < 346.0


def test_haversine_same_point(same_point: tuple[float, float]) -> None:
    """Distance from a point to itself must be zero."""
    km = server._haversine_km(*same_point, *same_point)  # pylint: disable=protected-access
    assert km == pytest.approx(0.0, abs=1e-9)


def test_haversine_symmetry(paris: tuple[float, float], london: tuple[float, float]) -> None:
    """Haversine distance must be symmetric (A→B == B→A)."""
    d_ab = server._haversine_km(*paris, *london)  # pylint: disable=protected-access
    d_ba = server._haversine_km(*london, *paris)  # pylint: disable=protected-access
    assert d_ab == pytest.approx(d_ba)


def test_haversine_antipodal_points() -> None:
    """Distance between antipodal points must be approximately half Earth's circumference."""
    # (0, 0) and (0, 180) are antipodal along the equator
    km = server._haversine_km(0.0, 0.0, 0.0, 180.0)  # pylint: disable=protected-access
    half_circumference = math.pi * server._EARTH_RADIUS_KM
    assert km == pytest.approx(half_circumference, rel=1e-4)


def test_haversine_known_nautical_distance() -> None:
    """One degree of latitude must equal approximately 60 nautical miles (111.12 km)."""
    km = server._haversine_km(0.0, 0.0, 1.0, 0.0)  # pylint: disable=protected-access
    assert 110.5 < km < 111.7


# ---------------------------------------------------------------------------
# distance_between_points (MCP tool)
# ---------------------------------------------------------------------------


def test_distance_returns_dict(paris: tuple[float, float], london: tuple[float, float]) -> None:
    """distance_between_points must return a dict with 'km' and 'nm' keys."""
    result = server.distance_between_points(*paris, *london)
    assert isinstance(result, dict)
    assert "km" in result
    assert "nm" in result


def test_distance_km_value(paris: tuple[float, float], london: tuple[float, float]) -> None:
    """Paris-London distance in km must be within the expected range."""
    result = server.distance_between_points(*paris, *london)
    assert 341.0 < result["km"] < 346.0


def test_distance_nm_value(paris: tuple[float, float], london: tuple[float, float]) -> None:
    """Paris-London distance in nautical miles must be consistent with km value."""
    result = server.distance_between_points(*paris, *london)
    expected_nm = result["km"] / server._KM_PER_NAUTICAL_MILE  # pylint: disable=protected-access
    assert result["nm"] == pytest.approx(expected_nm, rel=1e-3)


def test_distance_rounding(paris: tuple[float, float], london: tuple[float, float]) -> None:
    """Both km and nm must be rounded to exactly 3 decimal places."""
    result = server.distance_between_points(*paris, *london)
    assert result["km"] == round(result["km"], 3)
    assert result["nm"] == round(result["nm"], 3)


def test_distance_zero_same_point(same_point: tuple[float, float]) -> None:
    """Distance from a point to itself must be 0.0 km and 0.0 nm."""
    result = server.distance_between_points(*same_point, *same_point)
    assert result["km"] == pytest.approx(0.0, abs=1e-9)
    assert result["nm"] == pytest.approx(0.0, abs=1e-9)


def test_distance_symmetry(paris: tuple[float, float], london: tuple[float, float]) -> None:
    """distance_between_points must be symmetric (A→B == B→A)."""
    d_ab = server.distance_between_points(*paris, *london)
    d_ba = server.distance_between_points(*london, *paris)
    assert d_ab["km"] == pytest.approx(d_ba["km"])
    assert d_ab["nm"] == pytest.approx(d_ba["nm"])


def test_distance_positive_values(paris: tuple[float, float], london: tuple[float, float]) -> None:
    """Distance values must be strictly positive for distinct points."""
    result = server.distance_between_points(*paris, *london)
    assert result["km"] > 0.0
    assert result["nm"] > 0.0


def test_distance_nm_less_than_km(paris: tuple[float, float], london: tuple[float, float]) -> None:
    """Nautical miles value must always be less than kilometres (1 nm > 1 km)."""
    result = server.distance_between_points(*paris, *london)
    assert result["nm"] < result["km"]


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def test_tool_registered() -> None:
    """distance_between_points must be registered as an MCP tool."""
    tool_names = [t.name for t in asyncio.run(server.mcp.list_tools())]
    assert "distance_between_points" in tool_names
