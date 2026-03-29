"""Shared pytest fixtures for wingfoil tests."""

from __future__ import annotations

import pytest

import database


@pytest.fixture(autouse=True)
def reset_db_cache() -> None:
    """Reset the in-memory database cache before every test."""
    database._DB = None  # pylint: disable=protected-access
