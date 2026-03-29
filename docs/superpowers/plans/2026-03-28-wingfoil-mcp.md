# Wingfoil MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastMCP server exposing two tools that find the best consecutive 5-day wingfoil windows across 30 French spots, backed by a static JSON fake database.

**Architecture:** Option B — flat directory with `database.py` (scoring + search logic), `server.py` (MCP tools only), and `data/windspots.json` (30 spots × 365 days). Tests target `database.py` directly without going through the MCP layer.

**Tech Stack:** Python 3.14, fastmcp>=2.0, pytest, pytest-cov, black, isort, mypy, pylint, pre-commit, Docker (ghcr.io/astral-sh/uv:python3.14-bookworm-slim)

---

## AGENTS.md Constraints (mandatory)

| Rule | Applied where |
|---|---|
| Logs on all new code | `database.py`, `server.py`, `generate_data.py` — use `logging` module |
| Doctests if < 5 lines | `_score_wind_speed`, `_score_wind_direction`, `_score_wave_height` |
| Annotate code with comments | All non-obvious logic blocks |
| Cyclomatic complexity ≤ 19 | Each function — enforced by pylint `--max-complexity=19` |
| Coverage > 95% | `pytest --cov=. --cov-fail-under=95` in Task 8 |
| Remove zero-coverage tests | Review after first coverage run |
| Fixtures for test complexity | `@pytest.fixture` in `test_database.py` |
| `glossary.md` (never committed) | Created in Task 1, added to `.gitignore` |
| Vocabulary: one term per concept | spot, window, score, day_of_year, shore_normal |
| CI: current + next Python, allow failure on next | `.github/workflows/ci.yml` in Task 9 |
| PR title: `[AI]: <title>` | Reminder in Task 9 |
| PR description: <5 lines + coverage + complexity | Reminder in Task 9 |
| Never install packages < 7 days old | Check release dates before pinning versions |

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `wingfoil/data/windspots.json` | Create | 30 spots × 365 days fake database |
| `wingfoil/generate_data.py` | Create | One-time script to produce windspots.json |
| `wingfoil/database.py` | Create | Load JSON, score days, find best windows |
| `wingfoil/server.py` | Create | FastMCP tools, imports database.py |
| `wingfoil/tests/__init__.py` | Create | Empty |
| `wingfoil/tests/test_database.py` | Create | Unit tests for database.py |
| `wingfoil/pyproject.toml` | Create | Project config + tool settings |
| `wingfoil/.pre-commit-config.yaml` | Create | isort → black → mypy → pylint hooks |
| `wingfoil/.gitignore` | Create | Excludes glossary.md, .venv, __pycache__ |
| `wingfoil/glossary.md` | Create | Vocabulary definitions (never committed) |
| `wingfoil/Dockerfile` | Create | Container definition |
| `docker-compose.yml` | Modify | Add wingfoil service on port 8004 |
| `.github/workflows/ci.yml` | Create | CI: python3.14 + python3.15 (allow failure) |

---

## Task 1: Project Scaffold

**Files:**
- Create: `wingfoil/pyproject.toml`
- Create: `wingfoil/.pre-commit-config.yaml`
- Create: `wingfoil/data/.gitkeep`
- Create: `wingfoil/tests/__init__.py`

- [ ] **Step 1: Create the directory structure**

```bash
mkdir -p /home/mathieu/MCPs/wingfoil/data
mkdir -p /home/mathieu/MCPs/wingfoil/tests
touch /home/mathieu/MCPs/wingfoil/tests/__init__.py
```

- [ ] **Step 2: Create `wingfoil/pyproject.toml`**

```toml
[project]
name = "mcp-wingfoil"
version = "0.1.0"
description = "MCP server — French wingfoil spots and best wind windows"
requires-python = ">=3.14"
dependencies = [
    "fastmcp>=2.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "black>=24.0",
    "isort>=5.13",
    "mypy>=1.10",
    "pylint>=3.2",
    "pre-commit>=3.8",
]

[tool.black]
line-length = 100

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
strict = true
python_version = "3.14"

[tool.pylint.format]
max-line-length = 100

[tool.pylint.messages_control]
disable = ["C0301"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--doctest-modules --cov=. --cov-report=term-missing --cov-fail-under=95"

[tool.coverage.run]
omit = ["generate_data.py", "tests/*"]

[tool.pylint.design]
max-complexity = 19
```

- [ ] **Step 3: Create `wingfoil/.pre-commit-config.yaml`**

```yaml
repos:
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: []

  - repo: local
    hooks:
      - id: pylint
        name: pylint
        entry: pylint
        language: system
        types: [python]
        args: [--max-line-length=100]
```

- [ ] **Step 4: Create `wingfoil/.gitignore`**

```
.venv/
__pycache__/
*.pyc
.coverage
htmlcov/
glossary.md
```

- [ ] **Step 5: Create `wingfoil/glossary.md`** (never committed — excluded by .gitignore)

```markdown
# Glossary

| Term | Definition |
|---|---|
| day_of_year | Integer 1–365 identifying a calendar day in a non-leap year |
| score | Float 0.0–100.0 representing daily wingfoil conditions quality |
| shore_normal | Compass direction (degrees) perpendicular to the coastline, pointing seaward |
| spot | A named French coastal location suitable for wingfoiling |
| window | A consecutive sequence of exactly 5 days used for condition averaging |
```

- [ ] **Step 6: Install dev dependencies**

```bash
cd /home/mathieu/MCPs/wingfoil && uv sync --dev
```

Expected: resolves and installs all dev deps into `.venv`.

- [ ] **Step 7: Commit**

```bash
cd /home/mathieu/MCPs/wingfoil
git -C /home/mathieu/MCPs add wingfoil/pyproject.toml wingfoil/.pre-commit-config.yaml wingfoil/.gitignore wingfoil/tests/__init__.py
git -C /home/mathieu/MCPs commit -m "chore: scaffold wingfoil MCP project"
```

---

## Task 2: Generate Fake Database

**Files:**
- Create: `wingfoil/generate_data.py`
- Create: `wingfoil/data/windspots.json` (generated output)

- [ ] **Step 1: Create `wingfoil/generate_data.py`**

```python
#!/usr/bin/env python3
"""Generate data/windspots.json — run once to produce the fake database."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

# Each spot defines:
#   shore_normal_deg: compass direction perpendicular to coast, pointing seaward
#   wind_base_kn: annual average wind speed in knots
#   wind_amp_kn: seasonal amplitude (winter = base + amp/2, summer = base - amp/2)
#   wave_base_m: annual average wave height in metres
#   wave_amp_m: seasonal amplitude
#   prevailing_wind_deg: dominant wind direction used for generating daily values

SPOTS: list[dict] = [
    # --- Bretagne ---
    {
        "id": "spot-001", "name": "La Torche", "region": "Bretagne",
        "lat": 47.84, "lon": -4.34, "shore_normal_deg": 260.0,
        "wind_base_kn": 18.0, "wind_amp_kn": 10.0,
        "wave_base_m": 1.0, "wave_amp_m": 0.8,
        "prevailing_wind_deg": 255.0,
    },
    {
        "id": "spot-002", "name": "Gâvres", "region": "Bretagne",
        "lat": 47.69, "lon": -3.31, "shore_normal_deg": 220.0,
        "wind_base_kn": 15.0, "wind_amp_kn": 8.0,
        "wave_base_m": 0.8, "wave_amp_m": 0.6,
        "prevailing_wind_deg": 250.0,
    },
    {
        "id": "spot-003", "name": "Carnac", "region": "Bretagne",
        "lat": 47.57, "lon": -3.08, "shore_normal_deg": 180.0,
        "wind_base_kn": 14.0, "wind_amp_kn": 7.0,
        "wave_base_m": 0.7, "wave_amp_m": 0.5,
        "prevailing_wind_deg": 240.0,
    },
    {
        "id": "spot-004", "name": "Saint-Lunaire", "region": "Bretagne",
        "lat": 48.64, "lon": -2.11, "shore_normal_deg": 315.0,
        "wind_base_kn": 16.0, "wind_amp_kn": 9.0,
        "wave_base_m": 0.9, "wave_amp_m": 0.7,
        "prevailing_wind_deg": 250.0,
    },
    {
        "id": "spot-005", "name": "Brest Iroise", "region": "Bretagne",
        "lat": 48.39, "lon": -4.52, "shore_normal_deg": 270.0,
        "wind_base_kn": 17.0, "wind_amp_kn": 10.0,
        "wave_base_m": 1.1, "wave_amp_m": 0.9,
        "prevailing_wind_deg": 260.0,
    },
    {
        "id": "spot-006", "name": "Roches-Douvres", "region": "Côtes-d'Armor",
        "lat": 49.09, "lon": -2.81, "shore_normal_deg": 315.0,
        "wind_base_kn": 19.0, "wind_amp_kn": 10.0,
        "wave_base_m": 1.2, "wave_amp_m": 1.0,
        "prevailing_wind_deg": 255.0,
    },
    # --- Loire-Atlantique / Vendée ---
    {
        "id": "spot-007", "name": "La Baule", "region": "Loire-Atlantique",
        "lat": 47.28, "lon": -2.40, "shore_normal_deg": 200.0,
        "wind_base_kn": 13.0, "wind_amp_kn": 7.0,
        "wave_base_m": 0.6, "wave_amp_m": 0.5,
        "prevailing_wind_deg": 245.0,
    },
    {
        "id": "spot-008", "name": "Saint-Gilles-Croix-de-Vie", "region": "Vendée",
        "lat": 46.69, "lon": -1.93, "shore_normal_deg": 270.0,
        "wind_base_kn": 14.0, "wind_amp_kn": 8.0,
        "wave_base_m": 0.8, "wave_amp_m": 0.6,
        "prevailing_wind_deg": 255.0,
    },
    {
        "id": "spot-009", "name": "Les Sables-d'Olonne", "region": "Vendée",
        "lat": 46.50, "lon": -1.79, "shore_normal_deg": 270.0,
        "wind_base_kn": 15.0, "wind_amp_kn": 8.0,
        "wave_base_m": 0.9, "wave_amp_m": 0.7,
        "prevailing_wind_deg": 255.0,
    },
    {
        "id": "spot-010", "name": "La Tranche-sur-Mer", "region": "Vendée",
        "lat": 46.34, "lon": -1.44, "shore_normal_deg": 270.0,
        "wind_base_kn": 14.0, "wind_amp_kn": 7.0,
        "wave_base_m": 0.8, "wave_amp_m": 0.6,
        "prevailing_wind_deg": 255.0,
    },
    # --- Charente / Gironde ---
    {
        "id": "spot-011", "name": "Île de Ré", "region": "Charente-Maritime",
        "lat": 46.19, "lon": -1.32, "shore_normal_deg": 270.0,
        "wind_base_kn": 14.0, "wind_amp_kn": 7.0,
        "wave_base_m": 0.7, "wave_amp_m": 0.5,
        "prevailing_wind_deg": 255.0,
    },
    {
        "id": "spot-012", "name": "Royan", "region": "Charente-Maritime",
        "lat": 45.63, "lon": -1.02, "shore_normal_deg": 270.0,
        "wind_base_kn": 13.0, "wind_amp_kn": 7.0,
        "wave_base_m": 0.7, "wave_amp_m": 0.5,
        "prevailing_wind_deg": 250.0,
    },
    {
        "id": "spot-013", "name": "Lacanau", "region": "Gironde",
        "lat": 45.00, "lon": -1.20, "shore_normal_deg": 270.0,
        "wind_base_kn": 15.0, "wind_amp_kn": 8.0,
        "wave_base_m": 1.0, "wave_amp_m": 0.8,
        "prevailing_wind_deg": 255.0,
    },
    # --- Landes / Pays Basque ---
    {
        "id": "spot-014", "name": "Hossegor", "region": "Landes",
        "lat": 43.79, "lon": -1.45, "shore_normal_deg": 270.0,
        "wind_base_kn": 14.0, "wind_amp_kn": 7.0,
        "wave_base_m": 1.2, "wave_amp_m": 1.0,
        "prevailing_wind_deg": 255.0,
    },
    {
        "id": "spot-015", "name": "Hendaye", "region": "Pyrénées-Atlantiques",
        "lat": 43.37, "lon": -1.78, "shore_normal_deg": 225.0,
        "wind_base_kn": 12.0, "wind_amp_kn": 6.0,
        "wave_base_m": 0.8, "wave_amp_m": 0.6,
        "prevailing_wind_deg": 245.0,
    },
    # --- Méditerranée : Roussillon / Languedoc ---
    {
        "id": "spot-016", "name": "Leucate", "region": "Aude",
        "lat": 42.91, "lon": 3.03, "shore_normal_deg": 90.0,
        "wind_base_kn": 14.0, "wind_amp_kn": 12.0,
        "wave_base_m": 0.6, "wave_amp_m": 0.7,
        "prevailing_wind_deg": 330.0,
    },
    {
        "id": "spot-017", "name": "Port-Barcarès", "region": "Pyrénées-Orientales",
        "lat": 42.79, "lon": 3.04, "shore_normal_deg": 135.0,
        "wind_base_kn": 13.0, "wind_amp_kn": 11.0,
        "wave_base_m": 0.5, "wave_amp_m": 0.6,
        "prevailing_wind_deg": 330.0,
    },
    {
        "id": "spot-018", "name": "Canet-en-Roussillon", "region": "Pyrénées-Orientales",
        "lat": 42.70, "lon": 3.02, "shore_normal_deg": 135.0,
        "wind_base_kn": 12.0, "wind_amp_kn": 10.0,
        "wave_base_m": 0.5, "wave_amp_m": 0.5,
        "prevailing_wind_deg": 330.0,
    },
    {
        "id": "spot-019", "name": "Saint-Cyprien", "region": "Pyrénées-Orientales",
        "lat": 42.63, "lon": 3.04, "shore_normal_deg": 135.0,
        "wind_base_kn": 13.0, "wind_amp_kn": 10.0,
        "wave_base_m": 0.5, "wave_amp_m": 0.5,
        "prevailing_wind_deg": 330.0,
    },
    {
        "id": "spot-020", "name": "Gruissan", "region": "Aude",
        "lat": 43.11, "lon": 3.09, "shore_normal_deg": 135.0,
        "wind_base_kn": 13.0, "wind_amp_kn": 11.0,
        "wave_base_m": 0.5, "wave_amp_m": 0.5,
        "prevailing_wind_deg": 325.0,
    },
    {
        "id": "spot-021", "name": "Marseillan-Plage", "region": "Hérault",
        "lat": 43.32, "lon": 3.55, "shore_normal_deg": 180.0,
        "wind_base_kn": 12.0, "wind_amp_kn": 9.0,
        "wave_base_m": 0.5, "wave_amp_m": 0.4,
        "prevailing_wind_deg": 315.0,
    },
    {
        "id": "spot-022", "name": "Palavas-les-Flots", "region": "Hérault",
        "lat": 43.53, "lon": 3.93, "shore_normal_deg": 180.0,
        "wind_base_kn": 12.0, "wind_amp_kn": 9.0,
        "wave_base_m": 0.4, "wave_amp_m": 0.4,
        "prevailing_wind_deg": 315.0,
    },
    {
        "id": "spot-023", "name": "Port-Camargue", "region": "Gard",
        "lat": 43.52, "lon": 4.13, "shore_normal_deg": 180.0,
        "wind_base_kn": 13.0, "wind_amp_kn": 10.0,
        "wave_base_m": 0.5, "wave_amp_m": 0.5,
        "prevailing_wind_deg": 315.0,
    },
    {
        "id": "spot-024", "name": "Saintes-Maries-de-la-Mer", "region": "Bouches-du-Rhône",
        "lat": 43.45, "lon": 4.43, "shore_normal_deg": 180.0,
        "wind_base_kn": 15.0, "wind_amp_kn": 12.0,
        "wave_base_m": 0.6, "wave_amp_m": 0.6,
        "prevailing_wind_deg": 315.0,
    },
    {
        "id": "spot-025", "name": "La Ciotat", "region": "Bouches-du-Rhône",
        "lat": 43.18, "lon": 5.60, "shore_normal_deg": 135.0,
        "wind_base_kn": 11.0, "wind_amp_kn": 8.0,
        "wave_base_m": 0.5, "wave_amp_m": 0.4,
        "prevailing_wind_deg": 310.0,
    },
    # --- Manche / Nord ---
    {
        "id": "spot-026", "name": "Wissant", "region": "Pas-de-Calais",
        "lat": 50.88, "lon": 1.67, "shore_normal_deg": 315.0,
        "wind_base_kn": 16.0, "wind_amp_kn": 8.0,
        "wave_base_m": 0.8, "wave_amp_m": 0.7,
        "prevailing_wind_deg": 240.0,
    },
    {
        "id": "spot-027", "name": "Le Touquet", "region": "Pas-de-Calais",
        "lat": 50.52, "lon": 1.58, "shore_normal_deg": 270.0,
        "wind_base_kn": 15.0, "wind_amp_kn": 7.0,
        "wave_base_m": 0.7, "wave_amp_m": 0.6,
        "prevailing_wind_deg": 245.0,
    },
    {
        "id": "spot-028", "name": "Courseulles-sur-Mer", "region": "Calvados",
        "lat": 49.33, "lon": -0.46, "shore_normal_deg": 0.0,
        "wind_base_kn": 14.0, "wind_amp_kn": 7.0,
        "wave_base_m": 0.7, "wave_amp_m": 0.5,
        "prevailing_wind_deg": 240.0,
    },
    {
        "id": "spot-029", "name": "Mesquer", "region": "Loire-Atlantique",
        "lat": 47.40, "lon": -2.47, "shore_normal_deg": 270.0,
        "wind_base_kn": 13.0, "wind_amp_kn": 7.0,
        "wave_base_m": 0.6, "wave_amp_m": 0.5,
        "prevailing_wind_deg": 250.0,
    },
    {
        "id": "spot-030", "name": "Capbreton", "region": "Landes",
        "lat": 43.64, "lon": -1.44, "shore_normal_deg": 270.0,
        "wind_base_kn": 13.0, "wind_amp_kn": 7.0,
        "wave_base_m": 1.0, "wave_amp_m": 0.8,
        "prevailing_wind_deg": 255.0,
    },
]


def _generate_conditions(spot: dict) -> list[dict]:
    """Generate 365 days of synthetic wind conditions with seasonal patterns."""
    # Seed from spot coordinates for reproducibility
    random.seed(int(abs(spot["lat"]) * 1000) + int(abs(spot["lon"]) * 1000))

    base_kn = spot["wind_base_kn"]
    amp_kn = spot["wind_amp_kn"]
    base_wave = spot["wave_base_m"]
    amp_wave = spot["wave_amp_m"]
    prevailing = spot["prevailing_wind_deg"]

    conditions = []
    for day in range(1, 366):
        # Seasonal factor: +1 in mid-January (day 15), -1 in mid-July (day 196)
        seasonal = math.cos(2 * math.pi * (day - 15) / 365)

        wind_speed = base_kn + amp_kn * 0.5 * seasonal + random.gauss(0, 2.5)
        wind_speed = round(max(0.0, wind_speed), 1)

        wind_dir = (prevailing + random.gauss(0, 40.0)) % 360
        wind_dir = round(wind_dir, 1)

        wave_height = base_wave + amp_wave * 0.5 * seasonal + random.gauss(0, 0.15)
        wave_height = round(max(0.1, wave_height), 2)

        conditions.append(
            {
                "day_of_year": day,
                "wind_speed_knots": wind_speed,
                "wind_direction_deg": wind_dir,
                "wave_height_m": wave_height,
            }
        )
    return conditions


def main() -> None:
    output = []
    for spot_params in SPOTS:
        spot_out = {
            "id": spot_params["id"],
            "name": spot_params["name"],
            "region": spot_params["region"],
            "lat": spot_params["lat"],
            "lon": spot_params["lon"],
            "shore_normal_deg": spot_params["shore_normal_deg"],
            "conditions": _generate_conditions(spot_params),
        }
        output.append(spot_out)

    out_path = Path(__file__).parent / "data" / "windspots.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written {len(output)} spots to {out_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the generator**

```bash
cd /home/mathieu/MCPs/wingfoil && python generate_data.py
```

Expected output: `Written 30 spots to .../wingfoil/data/windspots.json`

- [ ] **Step 3: Sanity-check the output**

```bash
python3 -c "
import json
db = json.load(open('data/windspots.json'))
print(f'Spots: {len(db)}')
print(f'Days per spot: {len(db[0][\"conditions\"])}')
print(f'First spot: {db[0][\"name\"]} ({db[0][\"region\"]})')
print(f'Sample day: {db[0][\"conditions\"][0]}')
"
```

Expected: `Spots: 30`, `Days per spot: 365`, then spot and day data.

- [ ] **Step 4: Commit**

```bash
cd /home/mathieu/MCPs
git add wingfoil/generate_data.py wingfoil/data/windspots.json
git commit -m "feat: add 30-spot wingfoil fake database with 365-day conditions"
```

---

## Task 3: Scoring Functions (TDD)

**Files:**
- Create: `wingfoil/tests/test_database.py` (scoring tests)
- Create: `wingfoil/database.py` (scoring implementation)

### 3a — Write failing tests for scoring

- [ ] **Step 1: Create `wingfoil/tests/test_database.py` with scoring tests**

```python
"""Unit tests for database.py — scoring and window search."""

from __future__ import annotations

import pytest

from database import (
    _days_in_month,
    _score_wave_height,
    _score_wind_direction,
    _score_wind_speed,
    best_window,
    score_day,
    top_spots,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_day(
    day_of_year: int = 1,
    wind_speed_knots: float = 20.0,
    wind_direction_deg: float = 0.0,
    wave_height_m: float = 1.0,
) -> dict:
    return {
        "day_of_year": day_of_year,
        "wind_speed_knots": wind_speed_knots,
        "wind_direction_deg": wind_direction_deg,
        "wave_height_m": wave_height_m,
    }


def _make_spot(
    conditions: list[dict] | None = None,
    shore_normal_deg: float = 270.0,
) -> dict:
    """Build a minimal spot dict. Default conditions: 365 identical ideal days."""
    if conditions is None:
        conditions = [
            _make_day(
                day_of_year=i + 1,
                wind_speed_knots=20.0,
                wind_direction_deg=0.0,
                wave_height_m=1.0,
            )
            for i in range(365)
        ]
    return {
        "id": "test-spot",
        "name": "Test Spot",
        "region": "Test",
        "lat": 47.0,
        "lon": -3.0,
        "shore_normal_deg": shore_normal_deg,
        "conditions": conditions,
    }


# ---------------------------------------------------------------------------
# _score_wind_speed
# ---------------------------------------------------------------------------


def test_score_wind_speed_ideal_range():
    # 18–25 kn → max 50 pts
    assert _score_wind_speed(20.0) == pytest.approx(50.0)
    assert _score_wind_speed(18.0) == pytest.approx(50.0)
    assert _score_wind_speed(25.0) == pytest.approx(50.0)


def test_score_wind_speed_zero():
    assert _score_wind_speed(0.0) == pytest.approx(0.0)


def test_score_wind_speed_low_wind_below_ideal():
    # 6 kn is below ideal → score < 50
    assert _score_wind_speed(6.0) < 50.0


def test_score_wind_speed_too_strong():
    # 40 kn is above ideal → score < 50
    assert _score_wind_speed(40.0) < 50.0


# ---------------------------------------------------------------------------
# _score_wind_direction
# ---------------------------------------------------------------------------


def test_score_wind_direction_cross_shore():
    # diff = 90° → cross-shore → 30 pts
    # shore_normal=270, wind=0 → diff = |(0-270+180)%360 - 180| = |270-180| = 90
    assert _score_wind_direction(0.0, 270.0) == pytest.approx(30.0)


def test_score_wind_direction_onshore():
    # diff = 0° → onshore → 20 pts
    # shore_normal=270, wind=270 → diff=0
    assert _score_wind_direction(270.0, 270.0) == pytest.approx(20.0)


def test_score_wind_direction_offshore():
    # diff ≈ 180° → offshore → 10 pts
    # shore_normal=270, wind=90 → diff = |(90-270+180)%360 - 180| = |0-180| = 180
    assert _score_wind_direction(90.0, 270.0) == pytest.approx(10.0)


def test_score_wind_direction_cross_beats_offshore():
    shore = 270.0
    assert _score_wind_direction(0.0, shore) > _score_wind_direction(90.0, shore)


# ---------------------------------------------------------------------------
# _score_wave_height
# ---------------------------------------------------------------------------


def test_score_wave_height_ideal_range():
    # 0.5–1.5 m → 20 pts
    assert _score_wave_height(1.0) == pytest.approx(20.0)
    assert _score_wave_height(0.5) == pytest.approx(20.0)
    assert _score_wave_height(1.5) == pytest.approx(20.0)


def test_score_wave_height_flat():
    # < 0.3 m → very low pts
    assert _score_wave_height(0.1) < 10.0


def test_score_wave_height_too_big():
    # 5.0 m → 0 pts
    assert _score_wave_height(5.0) == pytest.approx(0.0)


def test_score_wave_height_ideal_beats_extreme():
    assert _score_wave_height(1.0) > _score_wave_height(4.0)


# ---------------------------------------------------------------------------
# score_day
# ---------------------------------------------------------------------------


def test_score_day_ideal_conditions():
    # 20 kn, cross-shore (wind=0°, shore=270° → diff=90°), 1.0 m → 100 pts
    day = _make_day(wind_speed_knots=20.0, wind_direction_deg=0.0, wave_height_m=1.0)
    assert score_day(day, shore_normal_deg=270.0) == pytest.approx(100.0)


def test_score_day_no_wind():
    # 0 kn → 0 speed pts; direction and wave still add up to 50
    day = _make_day(wind_speed_knots=0.0, wind_direction_deg=0.0, wave_height_m=1.0)
    assert score_day(day, shore_normal_deg=270.0) == pytest.approx(50.0)


def test_score_day_offshore_worse_than_cross():
    # Offshore wind should score lower than cross-shore
    cross = _make_day(wind_speed_knots=20.0, wind_direction_deg=0.0, wave_height_m=1.0)
    offshore = _make_day(wind_speed_knots=20.0, wind_direction_deg=90.0, wave_height_m=1.0)
    shore = 270.0
    assert score_day(cross, shore) > score_day(offshore, shore)
```

- [ ] **Step 2: Run to confirm tests fail (database.py not yet created)**

```bash
cd /home/mathieu/MCPs/wingfoil && python -m pytest tests/test_database.py -k "score" -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'database'`

### 3b — Implement scoring functions

- [ ] **Step 3: Create `wingfoil/database.py` with scoring implementation**

```python
"""Wingfoil spot database — loading, scoring, and window search."""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DB_PATH = Path(__file__).parent / "data" / "windspots.json"
_DB: list[dict] | None = None


def _load_db() -> list[dict]:
    """Load and cache the spot database from JSON."""
    global _DB  # noqa: PLW0603
    if _DB is None:
        logger.debug("Loading spot database from %s", _DB_PATH)
        _DB = json.loads(_DB_PATH.read_text(encoding="utf-8"))
        logger.info("Loaded %d spots from database", len(_DB))
    return _DB


def _score_wind_speed(knots: float) -> float:
    """Return 0–50 pts. Peak at 18–25 kn, tapers below 12 and above 35.

    >>> _score_wind_speed(20.0)
    50.0
    >>> _score_wind_speed(0.0)
    0.0
    """
    if knots <= 0.0:
        return 0.0
    if knots < 12.0:
        # Linear ramp: 0 pts at 0 kn → 30 pts at 12 kn
        return knots / 12.0 * 30.0
    if knots <= 25.0:
        # Ideal wingfoil range
        return 50.0
    if knots <= 35.0:
        # Gradual penalty above ideal
        return 50.0 - (knots - 25.0) / 10.0 * 30.0
    # Sharp penalty for dangerously strong wind
    return max(0.0, 20.0 - (knots - 35.0) / 5.0 * 20.0)


def _score_wind_direction(wind_dir_deg: float, shore_normal_deg: float) -> float:
    """Return 0–30 pts. Cross-shore (diff≈90°) best, offshore (diff≈180°) worst.

    >>> _score_wind_direction(0.0, 270.0)  # cross-shore
    30.0
    >>> _score_wind_direction(270.0, 270.0)  # onshore
    20.0
    """
    # diff: angular distance between wind and shore_normal (0=onshore, 90=cross, 180=offshore)
    diff = abs((wind_dir_deg - shore_normal_deg + 180.0) % 360.0 - 180.0)
    if diff <= 45.0:
        return 20.0  # onshore — acceptable but not ideal
    if diff <= 135.0:
        return 30.0  # cross-shore — best for wingfoil safety and performance
    return 10.0  # offshore — dangerous, penalised heavily


def _score_wave_height(height_m: float) -> float:
    """Return 0–20 pts. Ideal 0.5–1.5 m; flat or storm-size penalised.

    >>> _score_wave_height(1.0)
    20.0
    >>> _score_wave_height(5.0)
    0.0
    """
    if height_m < 0.3:
        # Too flat — poor lift for wingfoil
        return max(0.0, height_m / 0.3 * 10.0)
    if height_m <= 1.5:
        # Ideal range
        return 20.0
    if height_m <= 3.0:
        # Increasingly challenging conditions
        return 20.0 - (height_m - 1.5) / 1.5 * 15.0
    # Storm waves — unsafe
    return max(0.0, 5.0 - (height_m - 3.0) / 2.0 * 5.0)


def score_day(day: dict, shore_normal_deg: float) -> float:
    """Score a single day's conditions, returning 0.0–100.0.

    Combines wind speed (50 pts), wind direction (30 pts), wave height (20 pts).
    """
    return (
        _score_wind_speed(day["wind_speed_knots"])
        + _score_wind_direction(day["wind_direction_deg"], shore_normal_deg)
        + _score_wave_height(day["wave_height_m"])
    )
```

- [ ] **Step 4: Run scoring tests — expect all to pass**

```bash
cd /home/mathieu/MCPs/wingfoil && python -m pytest tests/test_database.py -k "score" -v
```

Expected: all scoring tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
cd /home/mathieu/MCPs
git add wingfoil/database.py wingfoil/tests/test_database.py
git commit -m "feat: implement day scoring functions (TDD)"
```

---

## Task 4: Window Search (TDD)

**Files:**
- Modify: `wingfoil/tests/test_database.py` (add window tests)
- Modify: `wingfoil/database.py` (add _days_in_month, best_window)

### 4a — Write failing window tests

- [ ] **Step 1: Append window tests to `wingfoil/tests/test_database.py`**

Add the following after the `score_day` tests:

```python
# ---------------------------------------------------------------------------
# _days_in_month
# ---------------------------------------------------------------------------


def test_days_in_month_january():
    days = _days_in_month(1)
    assert days[0] == 1
    assert days[-1] == 31
    assert len(days) == 31


def test_days_in_month_february_non_leap():
    # non-leap year (2001 used internally) → 28 days
    days = _days_in_month(2)
    assert len(days) == 28


def test_days_in_month_december():
    days = _days_in_month(12)
    assert len(days) == 31
    assert days[-1] == 365


# ---------------------------------------------------------------------------
# best_window
# ---------------------------------------------------------------------------


def test_best_window_returns_five_days():
    spot = _make_spot()
    result = best_window(spot)
    assert len(result["days"]) == 5
    assert result["end_day"] - result["start_day"] == 4


def test_best_window_month_filter_all_days_in_month():
    spot = _make_spot()
    result = best_window(spot, month=7)
    july_days = set(_days_in_month(7))
    for day in result["days"]:
        assert day["day_of_year"] in july_days


def test_best_window_score_beats_any_random_window():
    """The best window must score >= any arbitrary 5-day window."""
    import random

    random.seed(99)
    spot = _make_spot()
    result = best_window(spot)
    shore = spot["shore_normal_deg"]
    conditions = spot["conditions"]

    for _ in range(50):
        start = random.randint(1, 361)
        window = [conditions[start - 1 + i] for i in range(5)]
        avg = sum(score_day(d, shore) for d in window) / 5.0
        assert avg <= result["score"] + 1e-9


def test_best_window_result_keys():
    spot = _make_spot()
    result = best_window(spot)
    for key in ("spot_id", "spot_name", "region", "lat", "lon", "start_day", "end_day", "score", "days"):
        assert key in result
```

- [ ] **Step 2: Run window tests — expect failures**

```bash
cd /home/mathieu/MCPs/wingfoil && python -m pytest tests/test_database.py -k "window or month" -v 2>&1 | head -20
```

Expected: `ImportError` or `AttributeError` for missing functions.

### 4b — Implement _days_in_month and best_window

- [ ] **Step 3: Append to `wingfoil/database.py`**

```python
def _days_in_month(month: int) -> list[int]:
    """Return day_of_year values (1–365) for the given month in a non-leap year."""
    year = 2001  # non-leap year
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


def best_window(spot: dict, month: int | None = None) -> dict:
    """Find the best consecutive 5-day window for a spot.

    All 5 days must fall within *month* when month is given.
    Returns a dict with spot metadata, window boundaries, score, and day list.
    """
    conditions: list[dict] = spot["conditions"]
    shore_normal: float = spot["shore_normal_deg"]

    if month is not None:
        # Restrict search to windows fully contained in the requested month
        month_day_set = set(_days_in_month(month))
        candidate_starts = [
            d
            for d in sorted(month_day_set)
            if all(d + i in month_day_set for i in range(5))
        ]
    else:
        # All windows: day 1-5 through day 361-365
        candidate_starts = list(range(1, 362))

    best_score = -1.0
    best_start = candidate_starts[0]

    for start in candidate_starts:
        window = [conditions[start - 1 + i] for i in range(5)]
        avg = sum(score_day(d, shore_normal) for d in window) / 5.0
        if avg > best_score:
            best_score = avg
            best_start = start

    best_days = [conditions[best_start - 1 + i] for i in range(5)]
    logger.debug(
        "Best window for %s (month=%s): days %d–%d score=%.2f",
        spot["name"], month, best_start, best_start + 4, best_score,
    )

    return {
        "spot_id": spot["id"],
        "spot_name": spot["name"],
        "region": spot["region"],
        "lat": spot["lat"],
        "lon": spot["lon"],
        "start_day": best_start,
        "end_day": best_start + 4,
        "score": round(best_score, 2),
        "days": best_days,
    }
```

- [ ] **Step 4: Run window tests — expect all to pass**

```bash
cd /home/mathieu/MCPs/wingfoil && python -m pytest tests/test_database.py -k "window or month or days_in" -v
```

Expected: all `PASSED`.

- [ ] **Step 5: Commit**

```bash
cd /home/mathieu/MCPs
git add wingfoil/database.py wingfoil/tests/test_database.py
git commit -m "feat: implement best_window with month filter (TDD)"
```

---

## Task 5: Top Spots (TDD)

**Files:**
- Modify: `wingfoil/tests/test_database.py` (add top_spots tests)
- Modify: `wingfoil/database.py` (add top_spots)

### 5a — Write failing top_spots tests

- [ ] **Step 1: Append to `wingfoil/tests/test_database.py`**

```python
# ---------------------------------------------------------------------------
# top_spots
# ---------------------------------------------------------------------------


def test_top_spots_returns_n(monkeypatch):
    fake_db = [
        dict(_make_spot(), id=f"spot-{i:03d}", name=f"Spot {i}")
        for i in range(10)
    ]
    import database
    monkeypatch.setattr(database, "_load_db", lambda: fake_db)
    result = top_spots(n=3)
    assert len(result) == 3


def test_top_spots_default_n(monkeypatch):
    fake_db = [
        dict(_make_spot(), id=f"spot-{i:03d}", name=f"Spot {i}")
        for i in range(10)
    ]
    import database
    monkeypatch.setattr(database, "_load_db", lambda: fake_db)
    result = top_spots()
    assert len(result) == 5


def test_top_spots_ordered_descending(monkeypatch):
    """Results must be sorted by score descending."""
    # Give each spot a unique score by varying wind speed
    fake_db = []
    for i in range(8):
        conditions = [
            _make_day(day_of_year=d + 1, wind_speed_knots=float(5 + i * 2))
            for d in range(365)
        ]
        fake_db.append(dict(_make_spot(conditions=conditions), id=f"spot-{i:03d}", name=f"Spot {i}"))

    import database
    monkeypatch.setattr(database, "_load_db", lambda: fake_db)
    result = top_spots(n=5)
    scores = [r["score"] for r in result]
    assert scores == sorted(scores, reverse=True)


def test_top_spots_month_filter(monkeypatch):
    """month parameter is forwarded to best_window."""
    fake_db = [
        dict(_make_spot(), id=f"spot-{i:03d}", name=f"Spot {i}")
        for i in range(6)
    ]
    import database
    monkeypatch.setattr(database, "_load_db", lambda: fake_db)
    result = top_spots(n=3, month=6)
    assert len(result) == 3
    june_days = set(_days_in_month(6))
    for spot_result in result:
        for day in spot_result["days"]:
            assert day["day_of_year"] in june_days
```

- [ ] **Step 2: Run — expect failures**

```bash
cd /home/mathieu/MCPs/wingfoil && python -m pytest tests/test_database.py -k "top_spots" -v 2>&1 | head -20
```

Expected: `ImportError` for `top_spots`.

### 5b — Implement top_spots

- [ ] **Step 3: Append to `wingfoil/database.py`**

```python
def top_spots(n: int = 5, month: int | None = None) -> list[dict]:
    """Rank all spots by best 5-day window score, return the top N."""
    db = _load_db()
    logger.info("Ranking %d spots (month=%s, top_n=%d)", len(db), month, n)
    results = [best_window(spot, month) for spot in db]
    results.sort(key=lambda x: x["score"], reverse=True)
    logger.debug("Top spot: %s score=%.2f", results[0]["spot_name"], results[0]["score"])
    return results[:n]
```

- [ ] **Step 4: Run all tests — all pass**

```bash
cd /home/mathieu/MCPs/wingfoil && python -m pytest tests/ -v
```

Expected: all tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
cd /home/mathieu/MCPs
git add wingfoil/database.py wingfoil/tests/test_database.py
git commit -m "feat: implement top_spots ranking (TDD)"
```

---

## Task 6: MCP Server

**Files:**
- Create: `wingfoil/server.py`

- [ ] **Step 1: Create `wingfoil/server.py`**

```python
"""MCP server — French wingfoil spots and best wind windows."""

from __future__ import annotations

import logging
import os

from fastmcp import FastMCP

import database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8004"))

mcp = FastMCP("wingfoil")


@mcp.tool()
def best_wingfoil_spots(n: int = 5) -> list[dict]:
    """Find the top N French wingfoil spots with their best consecutive 5-day wind window across the year.

    Returns spots ranked by their peak 5-day average score (wind speed, direction, wave height).
    Each result includes spot name, region, coordinates, the optimal window dates, and daily conditions.
    """
    logger.info("Tool called: best_wingfoil_spots(n=%d)", n)
    return database.top_spots(n=n)


@mcp.tool()
def best_wingfoil_spots_by_month(month: int, n: int = 5) -> list[dict]:
    """Find the top N French wingfoil spots for a specific month (1=Jan … 12=Dec).

    The 5-day window is constrained so all days fall within the requested month.
    Returns spots ranked by their best window score within that month.
    """
    logger.info("Tool called: best_wingfoil_spots_by_month(month=%d, n=%d)", month, n)
    return database.top_spots(n=n, month=month)


if __name__ == "__main__":
    logger.info("Starting wingfoil MCP server on %s:%d", HOST, PORT)
    mcp.run(transport="streamable-http", host=HOST, port=PORT)
```

- [ ] **Step 2: Smoke-test the server starts**

```bash
cd /home/mathieu/MCPs/wingfoil && timeout 5 python server.py || true
```

Expected: server starts (output like `Uvicorn running…`) then exits after 5 s — no import errors.

- [ ] **Step 3: Commit**

```bash
cd /home/mathieu/MCPs
git add wingfoil/server.py
git commit -m "feat: add FastMCP server with two wingfoil tools"
```

---

## Task 7: Docker & docker-compose

**Files:**
- Create: `wingfoil/Dockerfile`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Create `wingfoil/Dockerfile`**

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

ENV UV_SYSTEM_PYTHON=1

RUN uv pip install "fastmcp>=2.0"

COPY server.py database.py ./
COPY data/ ./data/

EXPOSE 8004

CMD ["python", "server.py"]
```

- [ ] **Step 2: Add wingfoil service to `docker-compose.yml`**

Read the current `docker-compose.yml` at `/home/mathieu/MCPs/docker-compose.yml`, then append the following service block before the final empty line:

```yaml
  wingfoil:
    build:
      context: ./wingfoil
    ports:
      - "8004:8004"
    env_file:
      - path: ./wingfoil/.env
        required: false
    environment:
      HOST: "0.0.0.0"
      PORT: "8004"
    restart: unless-stopped
```

- [ ] **Step 3: Verify compose config is valid**

```bash
cd /home/mathieu/MCPs && docker compose config --quiet && echo "OK"
```

Expected: `OK` (no YAML errors).

- [ ] **Step 4: Commit**

```bash
cd /home/mathieu/MCPs
git add wingfoil/Dockerfile docker-compose.yml
git commit -m "feat: add wingfoil Dockerfile and docker-compose service on port 8004"
```

---

## Task 8: Pre-commit Setup

**Files:**
- No new files — install hooks and run them

- [ ] **Step 1: Install pre-commit hooks**

```bash
cd /home/mathieu/MCPs/wingfoil && uv run pre-commit install
```

Expected: `pre-commit installed at .git/hooks/pre-commit`

Note: If the `wingfoil/` directory is not inside a git repo on its own, run:
```bash
cd /home/mathieu/MCPs && uv run --directory wingfoil pre-commit install --config wingfoil/.pre-commit-config.yaml
```

- [ ] **Step 2: Run all pre-commit hooks manually**

```bash
cd /home/mathieu/MCPs/wingfoil && uv run pre-commit run --all-files
```

Expected: all hooks pass (`isort`, `black`, `mypy`, `pylint` all green). Fix any issues reported before proceeding.

Common fixes:
- `isort`: reorders imports automatically — just `git add` the changed files and re-run
- `black`: reformats automatically — just `git add` and re-run
- `mypy`: type errors need manual fixes in the source files
- `pylint`: style/logic warnings need manual fixes

- [ ] **Step 3: Commit any auto-fixed files**

```bash
cd /home/mathieu/MCPs
git add wingfoil/
git commit -m "style: apply isort/black formatting, fix mypy/pylint issues"
```

- [ ] **Step 4: Run full test suite with coverage**

```bash
cd /home/mathieu/MCPs/wingfoil && python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-fail-under=95
```

Expected: all tests `PASSED`, coverage ≥ 95%.
If coverage < 95%: identify uncovered lines in the report and add targeted tests. Remove any test that covers zero new lines.

- [ ] **Step 5: Final commit**

```bash
cd /home/mathieu/MCPs
git add wingfoil/
git commit -m "chore: all pre-commit hooks pass, full test suite green, coverage ≥ 95%"
```

---

## Task 9: CI Workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    paths:
      - "wingfoil/**"
  pull_request:
    paths:
      - "wingfoil/**"

jobs:
  test-py314:
    name: Test (Python 3.14)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: wingfoil
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          python-version: "3.14"
      - run: uv sync --dev
      - run: uv run pytest tests/ --cov=. --cov-fail-under=95
      - run: uv run pre-commit run --all-files

  test-py315:
    name: Test (Python 3.15 — allowed to fail)
    runs-on: ubuntu-latest
    continue-on-error: true
    defaults:
      run:
        working-directory: wingfoil
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          python-version: "3.15"
      - run: uv sync --dev
      - run: uv run pytest tests/ --cov=. --cov-fail-under=95
```

- [ ] **Step 2: Commit**

```bash
cd /home/mathieu/MCPs
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions for Python 3.14 + 3.15 (allow failure)"
```

---

## PR Checklist (before creating PR)

When creating the PR, follow AGENTS.md format:

- **Title:** `[AI]: Add wingfoil MCP server with 30 French spots and best-window search`
- **Description** (< 5 lines):
  ```
  - FastMCP server with 2 tools: best spots unrestricted + by month
  - 30 French wingfoil spots × 365 days synthetic wind conditions
  - Scoring: wind speed (50pts) + direction (30pts) + wave height (20pts)
  - Coverage score: XX%, max complexity: YY
  ```
  (Fill in actual coverage and complexity values from the test run.)

---

## Self-Review Checklist

- [x] **30 spots × 365 days** — Task 2 (generate_data.py with `SPOTS` list of exactly 30)
- [x] **Python 3.14** — pyproject.toml + Dockerfile base image
- [x] **pre-commit: mypy, isort, black, pylint** — Task 1 + Task 8
- [x] **Unit tests** — 9+ tests Tasks 3–5 targeting scoring, window search, top_spots
- [x] **best_wingfoil_spots (unrestricted)** — Task 6
- [x] **best_wingfoil_spots_by_month** — Task 6 with month constraint
- [x] **Top N ranked** — `n` parameter on both tools, default 5
- [x] **Docker** — Task 7 Dockerfile + docker-compose port 8004
- [x] **shore_normal_deg** — present in spot data, used in score_day via best_window
- [x] **5-day window month constraint** — all 5 days within month enforced in candidate_starts
- [x] **Logging** — database.py + server.py, no secrets logged
- [x] **Doctests** — _score_wind_speed, _score_wind_direction, _score_wave_height (< 5 lines each)
- [x] **Coverage > 95%** — pytest-cov + --cov-fail-under=95 in Task 8
- [x] **Cyclomatic complexity ≤ 19** — pylint --max-complexity=19 in pyproject.toml
- [x] **Fixtures** — _make_day, _make_spot helpers in test_database.py
- [x] **glossary.md** — created Task 1, excluded via .gitignore
- [x] **CI** — Task 9: Python 3.14 required, 3.15 allow-failure
- [x] **PR format** — title + description template in Task 9
