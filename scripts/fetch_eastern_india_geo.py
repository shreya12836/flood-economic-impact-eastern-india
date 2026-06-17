"""
One-time setup script.
Downloads Natural Earth admin-1 state boundaries, filters to the 4 study states,
simplifies geometry, and saves to dashboard/data/eastern_india_states.geojson.

Run from the repo root:
    python scripts/fetch_eastern_india_geo.py
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd

_STUDY_STATES = {"Bihar", "Jharkhand", "Odisha", "West Bengal"}
_GEO_URL = (
    "https://naciscdn.org/naturalearth/10m/cultural/"
    "ne_10m_admin_1_states_provinces.zip"
)
_OUT = (
    Path(__file__).resolve().parent.parent
    / "dashboard"
    / "data"
    / "eastern_india_states.geojson"
)


def main() -> None:
    print("Downloading Natural Earth admin-1 boundaries...")
    world = gpd.read_file(_GEO_URL)
    india = world[world["admin"] == "India"].copy()
    study = india[india["name"].isin(_STUDY_STATES)].copy()

    if len(study) != len(_STUDY_STATES):
        found = set(study["name"])
        missing = _STUDY_STATES - found
        raise RuntimeError(f"States not matched in source data: {missing}")

    study = study[["name", "geometry"]].copy()
    study["geometry"] = study["geometry"].simplify(0.01, preserve_topology=True)
    study = study.to_crs("EPSG:4326")

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    study.to_file(_OUT, driver="GeoJSON")
    print(f"Saved {len(study)} features to {_OUT}")


if __name__ == "__main__":
    main()
