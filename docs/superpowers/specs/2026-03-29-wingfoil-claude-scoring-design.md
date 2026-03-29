# Wingfoil — Claude-driven spot scoring

**Date:** 2026-03-29
**Status:** Approved

## Context

The wingfoil MCP server currently embeds hardcoded scoring formulas (`_score_wind_speed`, `_score_wind_direction`, `_score_wave_height`) that pre-rank spots before Claude ever sees them. Claude only receives a sorted list, with no ability to apply its own reasoning about what makes a good wingfoil session.

The goal is to remove all server-side scoring and expose raw meteorological data so Claude can determine the best spots itself.

## Architecture

The server shifts from a "scoring → ranking" model to a "raw data → Claude reasons" model.

```
database.py              server.py              Claude
────────────────         ──────────────         ───────────────────────
load_db() async          list_spots()    →      browses pages
aggregate_monthly()      get_spot()      →      zooms on candidates
get_spot_by_id()                                reasons + ranks
```

### database.py

Retains only three responsibilities:

- `load_db() async` — loads JSON file with in-memory cache
- `aggregate_monthly(spot)` — computes per-month avg/min/max for wind speed, circular mean for wind direction, avg/max for wave height
- `get_spot_by_id(spot_id)` — direct lookup by ID, raises `KeyError` if unknown

All scoring code is deleted: `_score_wind_speed`, `_score_wind_direction`, `_score_wave_height`, `score_day`, `best_window`, `top_spots`.

### server.py

Two async FastMCP tools:

- `list_spots(page: int = 1, page_size: int = 5)` — paginated list with monthly aggregates
- `get_spot(spot_id: str)` — full 365-day conditions + metadata

## Data structures

### list_spots response

```json
{
  "total": 30,
  "page": 1,
  "page_size": 5,
  "spots": [
    {
      "id": "spot-001",
      "name": "La Torche",
      "region": "Bretagne",
      "lat": 47.84,
      "lon": -4.34,
      "shore_normal_deg": 260.0,
      "monthly_stats": {
        "1": {
          "wind_speed_avg": 21.3,
          "wind_speed_min": 12.1,
          "wind_speed_max": 31.4,
          "wind_dir_avg": 245.0,
          "wave_height_avg": 1.4,
          "wave_height_max": 2.8
        }
      }
    }
  ]
}
```

Wind direction average uses circular mean to avoid artefacts at the 0°/360° boundary.

### get_spot response

```json
{
  "id": "spot-001",
  "name": "La Torche",
  "region": "Bretagne",
  "lat": 47.84,
  "lon": -4.34,
  "shore_normal_deg": 260.0,
  "conditions": [
    {"day_of_year": 1, "wind_speed_knots": 19.6, "wind_direction_deg": 200.8, "wave_height_m": 1.33}
  ]
}
```

## Error handling

- `get_spot` with unknown ID returns a structured error response (not a server crash)
- `list_spots` with out-of-range page returns empty `spots` list with correct `total`

## Testing

Target coverage: 95% (repo standard).

### test_database.py

- `load_db()` loads and caches correctly
- `aggregate_monthly()` computes correct avg/min/max on known data
- Circular mean handles the 359°/1° edge case correctly
- `get_spot_by_id()` returns the correct spot, raises `KeyError` for unknown IDs

### test_server.py

- `list_spots()`: correct pagination (page 1, page 2, last partial page)
- `list_spots()`: `total` = 30, each spot has `monthly_stats` with 12 months
- `get_spot()`: returns 365 days + complete metadata
- `get_spot()`: returns clear error for unknown `spot_id`
