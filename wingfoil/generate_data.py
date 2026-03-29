#!/usr/bin/env python3
"""Generate data/windspots.json — run once to produce the fake database."""

from __future__ import annotations

import json
import logging
import math
import random
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Each spot defines:
#   shore_normal_deg: compass direction perpendicular to coast, pointing seaward
#   wind_base_kn: annual average wind speed in knots
#   wind_amp_kn: seasonal amplitude (winter = base + amp/2, summer = base - amp/2)
#   wave_base_m: annual average wave height in metres
#   wave_amp_m: seasonal amplitude
#   prevailing_wind_deg: dominant wind direction used for generating daily values

SPOTS: list[dict[str, Any]] = [
    # --- Bretagne ---
    {
        "id": "spot-001",
        "name": "La Torche",
        "region": "Bretagne",
        "lat": 47.84,
        "lon": -4.34,
        "shore_normal_deg": 260.0,
        "wind_base_kn": 18.0,
        "wind_amp_kn": 10.0,
        "wave_base_m": 1.0,
        "wave_amp_m": 0.8,
        "prevailing_wind_deg": 255.0,
    },
    {
        "id": "spot-002",
        "name": "Gâvres",
        "region": "Bretagne",
        "lat": 47.69,
        "lon": -3.31,
        "shore_normal_deg": 220.0,
        "wind_base_kn": 15.0,
        "wind_amp_kn": 8.0,
        "wave_base_m": 0.8,
        "wave_amp_m": 0.6,
        "prevailing_wind_deg": 250.0,
    },
    {
        "id": "spot-003",
        "name": "Carnac",
        "region": "Bretagne",
        "lat": 47.57,
        "lon": -3.08,
        "shore_normal_deg": 180.0,
        "wind_base_kn": 14.0,
        "wind_amp_kn": 7.0,
        "wave_base_m": 0.7,
        "wave_amp_m": 0.5,
        "prevailing_wind_deg": 240.0,
    },
    {
        "id": "spot-004",
        "name": "Saint-Lunaire",
        "region": "Bretagne",
        "lat": 48.64,
        "lon": -2.11,
        "shore_normal_deg": 315.0,
        "wind_base_kn": 16.0,
        "wind_amp_kn": 9.0,
        "wave_base_m": 0.9,
        "wave_amp_m": 0.7,
        "prevailing_wind_deg": 250.0,
    },
    {
        "id": "spot-005",
        "name": "Brest Iroise",
        "region": "Bretagne",
        "lat": 48.39,
        "lon": -4.52,
        "shore_normal_deg": 270.0,
        "wind_base_kn": 17.0,
        "wind_amp_kn": 10.0,
        "wave_base_m": 1.1,
        "wave_amp_m": 0.9,
        "prevailing_wind_deg": 260.0,
    },
    {
        "id": "spot-006",
        "name": "Roches-Douvres",
        "region": "Côtes-d'Armor",
        "lat": 49.09,
        "lon": -2.81,
        "shore_normal_deg": 315.0,
        "wind_base_kn": 19.0,
        "wind_amp_kn": 10.0,
        "wave_base_m": 1.2,
        "wave_amp_m": 1.0,
        "prevailing_wind_deg": 255.0,
    },
    # --- Loire-Atlantique / Vendée ---
    {
        "id": "spot-007",
        "name": "La Baule",
        "region": "Loire-Atlantique",
        "lat": 47.28,
        "lon": -2.40,
        "shore_normal_deg": 200.0,
        "wind_base_kn": 13.0,
        "wind_amp_kn": 7.0,
        "wave_base_m": 0.6,
        "wave_amp_m": 0.5,
        "prevailing_wind_deg": 245.0,
    },
    {
        "id": "spot-008",
        "name": "Saint-Gilles-Croix-de-Vie",
        "region": "Vendée",
        "lat": 46.69,
        "lon": -1.93,
        "shore_normal_deg": 270.0,
        "wind_base_kn": 14.0,
        "wind_amp_kn": 8.0,
        "wave_base_m": 0.8,
        "wave_amp_m": 0.6,
        "prevailing_wind_deg": 255.0,
    },
    {
        "id": "spot-009",
        "name": "Les Sables-d'Olonne",
        "region": "Vendée",
        "lat": 46.50,
        "lon": -1.79,
        "shore_normal_deg": 270.0,
        "wind_base_kn": 15.0,
        "wind_amp_kn": 8.0,
        "wave_base_m": 0.9,
        "wave_amp_m": 0.7,
        "prevailing_wind_deg": 255.0,
    },
    {
        "id": "spot-010",
        "name": "La Tranche-sur-Mer",
        "region": "Vendée",
        "lat": 46.34,
        "lon": -1.44,
        "shore_normal_deg": 270.0,
        "wind_base_kn": 14.0,
        "wind_amp_kn": 7.0,
        "wave_base_m": 0.8,
        "wave_amp_m": 0.6,
        "prevailing_wind_deg": 255.0,
    },
    # --- Charente / Gironde ---
    {
        "id": "spot-011",
        "name": "Île de Ré",
        "region": "Charente-Maritime",
        "lat": 46.19,
        "lon": -1.32,
        "shore_normal_deg": 270.0,
        "wind_base_kn": 14.0,
        "wind_amp_kn": 7.0,
        "wave_base_m": 0.7,
        "wave_amp_m": 0.5,
        "prevailing_wind_deg": 255.0,
    },
    {
        "id": "spot-012",
        "name": "Royan",
        "region": "Charente-Maritime",
        "lat": 45.63,
        "lon": -1.02,
        "shore_normal_deg": 270.0,
        "wind_base_kn": 13.0,
        "wind_amp_kn": 7.0,
        "wave_base_m": 0.7,
        "wave_amp_m": 0.5,
        "prevailing_wind_deg": 250.0,
    },
    {
        "id": "spot-013",
        "name": "Lacanau",
        "region": "Gironde",
        "lat": 45.00,
        "lon": -1.20,
        "shore_normal_deg": 270.0,
        "wind_base_kn": 15.0,
        "wind_amp_kn": 8.0,
        "wave_base_m": 1.0,
        "wave_amp_m": 0.8,
        "prevailing_wind_deg": 255.0,
    },
    # --- Landes / Pays Basque ---
    {
        "id": "spot-014",
        "name": "Hossegor",
        "region": "Landes",
        "lat": 43.79,
        "lon": -1.45,
        "shore_normal_deg": 270.0,
        "wind_base_kn": 14.0,
        "wind_amp_kn": 7.0,
        "wave_base_m": 1.2,
        "wave_amp_m": 1.0,
        "prevailing_wind_deg": 255.0,
    },
    {
        "id": "spot-015",
        "name": "Hendaye",
        "region": "Pyrénées-Atlantiques",
        "lat": 43.37,
        "lon": -1.78,
        "shore_normal_deg": 225.0,
        "wind_base_kn": 12.0,
        "wind_amp_kn": 6.0,
        "wave_base_m": 0.8,
        "wave_amp_m": 0.6,
        "prevailing_wind_deg": 245.0,
    },
    # --- Méditerranée : Roussillon / Languedoc ---
    {
        "id": "spot-016",
        "name": "Leucate",
        "region": "Aude",
        "lat": 42.91,
        "lon": 3.03,
        "shore_normal_deg": 90.0,
        "wind_base_kn": 14.0,
        "wind_amp_kn": 12.0,
        "wave_base_m": 0.6,
        "wave_amp_m": 0.5,
        "prevailing_wind_deg": 330.0,
    },
    {
        "id": "spot-017",
        "name": "Port-Barcarès",
        "region": "Pyrénées-Orientales",
        "lat": 42.79,
        "lon": 3.04,
        "shore_normal_deg": 135.0,
        "wind_base_kn": 13.0,
        "wind_amp_kn": 11.0,
        "wave_base_m": 0.5,
        "wave_amp_m": 0.4,
        "prevailing_wind_deg": 330.0,
    },
    {
        "id": "spot-018",
        "name": "Canet-en-Roussillon",
        "region": "Pyrénées-Orientales",
        "lat": 42.70,
        "lon": 3.02,
        "shore_normal_deg": 135.0,
        "wind_base_kn": 12.0,
        "wind_amp_kn": 10.0,
        "wave_base_m": 0.5,
        "wave_amp_m": 0.5,
        "prevailing_wind_deg": 330.0,
    },
    {
        "id": "spot-019",
        "name": "Saint-Cyprien",
        "region": "Pyrénées-Orientales",
        "lat": 42.63,
        "lon": 3.04,
        "shore_normal_deg": 135.0,
        "wind_base_kn": 13.0,
        "wind_amp_kn": 10.0,
        "wave_base_m": 0.5,
        "wave_amp_m": 0.5,
        "prevailing_wind_deg": 330.0,
    },
    {
        "id": "spot-020",
        "name": "Gruissan",
        "region": "Aude",
        "lat": 43.11,
        "lon": 3.09,
        "shore_normal_deg": 135.0,
        "wind_base_kn": 13.0,
        "wind_amp_kn": 11.0,
        "wave_base_m": 0.5,
        "wave_amp_m": 0.5,
        "prevailing_wind_deg": 325.0,
    },
    {
        "id": "spot-021",
        "name": "Marseillan-Plage",
        "region": "Hérault",
        "lat": 43.32,
        "lon": 3.55,
        "shore_normal_deg": 180.0,
        "wind_base_kn": 12.0,
        "wind_amp_kn": 9.0,
        "wave_base_m": 0.5,
        "wave_amp_m": 0.4,
        "prevailing_wind_deg": 315.0,
    },
    {
        "id": "spot-022",
        "name": "Palavas-les-Flots",
        "region": "Hérault",
        "lat": 43.53,
        "lon": 3.93,
        "shore_normal_deg": 180.0,
        "wind_base_kn": 12.0,
        "wind_amp_kn": 9.0,
        "wave_base_m": 0.4,
        "wave_amp_m": 0.4,
        "prevailing_wind_deg": 315.0,
    },
    {
        "id": "spot-023",
        "name": "Port-Camargue",
        "region": "Gard",
        "lat": 43.52,
        "lon": 4.13,
        "shore_normal_deg": 180.0,
        "wind_base_kn": 13.0,
        "wind_amp_kn": 10.0,
        "wave_base_m": 0.5,
        "wave_amp_m": 0.5,
        "prevailing_wind_deg": 315.0,
    },
    {
        "id": "spot-024",
        "name": "Saintes-Maries-de-la-Mer",
        "region": "Bouches-du-Rhône",
        "lat": 43.45,
        "lon": 4.43,
        "shore_normal_deg": 180.0,
        "wind_base_kn": 15.0,
        "wind_amp_kn": 12.0,
        "wave_base_m": 0.6,
        "wave_amp_m": 0.6,
        "prevailing_wind_deg": 315.0,
    },
    {
        "id": "spot-025",
        "name": "La Ciotat",
        "region": "Bouches-du-Rhône",
        "lat": 43.18,
        "lon": 5.60,
        "shore_normal_deg": 135.0,
        "wind_base_kn": 11.0,
        "wind_amp_kn": 8.0,
        "wave_base_m": 0.5,
        "wave_amp_m": 0.4,
        "prevailing_wind_deg": 310.0,
    },
    # --- Manche / Nord ---
    {
        "id": "spot-026",
        "name": "Wissant",
        "region": "Pas-de-Calais",
        "lat": 50.88,
        "lon": 1.67,
        "shore_normal_deg": 315.0,
        "wind_base_kn": 16.0,
        "wind_amp_kn": 8.0,
        "wave_base_m": 0.8,
        "wave_amp_m": 0.7,
        "prevailing_wind_deg": 240.0,
    },
    {
        "id": "spot-027",
        "name": "Le Touquet",
        "region": "Pas-de-Calais",
        "lat": 50.52,
        "lon": 1.58,
        "shore_normal_deg": 270.0,
        "wind_base_kn": 15.0,
        "wind_amp_kn": 7.0,
        "wave_base_m": 0.7,
        "wave_amp_m": 0.6,
        "prevailing_wind_deg": 245.0,
    },
    {
        "id": "spot-028",
        "name": "Courseulles-sur-Mer",
        "region": "Calvados",
        "lat": 49.33,
        "lon": -0.46,
        "shore_normal_deg": 0.0,
        "wind_base_kn": 14.0,
        "wind_amp_kn": 7.0,
        "wave_base_m": 0.7,
        "wave_amp_m": 0.5,
        "prevailing_wind_deg": 240.0,
    },
    {
        "id": "spot-029",
        "name": "Mesquer",
        "region": "Loire-Atlantique",
        "lat": 47.40,
        "lon": -2.47,
        "shore_normal_deg": 270.0,
        "wind_base_kn": 13.0,
        "wind_amp_kn": 7.0,
        "wave_base_m": 0.6,
        "wave_amp_m": 0.5,
        "prevailing_wind_deg": 250.0,
    },
    {
        "id": "spot-030",
        "name": "Capbreton",
        "region": "Landes",
        "lat": 43.64,
        "lon": -1.44,
        "shore_normal_deg": 270.0,
        "wind_base_kn": 13.0,
        "wind_amp_kn": 7.0,
        "wave_base_m": 1.0,
        "wave_amp_m": 0.8,
        "prevailing_wind_deg": 255.0,
    },
]


def _generate_conditions(spot: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate 365 days of synthetic wind conditions with seasonal patterns.

    Wind peaks in mid-January (day 15), troughs in mid-July (day 196).
    Uses a cosine seasonal curve plus Gaussian noise for realism.
    """
    # Unique seed per spot using signed lat/lon — avoids collisions between
    # spots with similar absolute coordinate sums (e.g. Atlantic vs Mediterranean)
    random.seed(int(spot["lat"] * 100) * 1000 + int(spot["lon"] * 100))

    base_kn: float = spot["wind_base_kn"]
    amp_kn: float = spot["wind_amp_kn"]
    base_wave: float = spot["wave_base_m"]
    amp_wave: float = spot["wave_amp_m"]
    prevailing: float = spot["prevailing_wind_deg"]

    conditions: list[dict[str, Any]] = []
    for day in range(1, 366):
        # Seasonal factor: +1 at mid-January (day 15), -1 at mid-July (day 196)
        seasonal = math.cos(2 * math.pi * (day - 15) / 365)

        wind_speed = base_kn + amp_kn * 0.5 * seasonal + random.gauss(0, 2.5)
        wind_speed = round(max(0.0, wind_speed), 1)

        # Wind direction varies around prevailing direction with realistic spread
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
    """Generate windspots.json from the SPOTS definition list."""
    # DEBUG level shows per-spot progress; INFO shows summary only
    logging.basicConfig(level=logging.INFO)
    logger.info("Generating conditions for %d spots", len(SPOTS))
    output: list[dict[str, Any]] = []

    for spot_params in SPOTS:
        spot_out: dict[str, Any] = {
            "id": spot_params["id"],
            "name": spot_params["name"],
            "region": spot_params["region"],
            "lat": spot_params["lat"],
            "lon": spot_params["lon"],
            "shore_normal_deg": spot_params["shore_normal_deg"],
            "conditions": _generate_conditions(spot_params),
        }
        output.append(spot_out)
        logger.debug("Generated %s (%s)", spot_params["name"], spot_params["region"])

    out_path = Path(__file__).parent / "data" / "windspots.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Written %d spots to %s", len(output), out_path)


if __name__ == "__main__":
    main()
