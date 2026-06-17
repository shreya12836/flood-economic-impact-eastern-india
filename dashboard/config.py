from __future__ import annotations

from utils.icons import (
    BUILDING, CALENDAR, CHART_BAR, CODE, COG, CUBE,
    DATABASE, GLOBE, MAP, PIN, SIGNAL, TREND_DOWN, WRENCH,
)

PROJECT_TITLE = "Flood Impact on Economic Activity — Eastern India"
PROJECT_DESCRIPTION = (
    "Panel econometric analysis of how seasonal flood exposure affects economic activity "
    "and built-up development across Assembly Constituencies in Eastern India using "
    "satellite-derived indicators."
)

# ── Icon configuration ────────────────────────────────────────────────────────
# All values are Bootstrap Icons class names (strings like "bar-chart-line").
# Rendering is handled by theme._bi() — changing names here never touches HTML.

HERO_TAGS: list[dict] = [
    {"icon": SIGNAL,    "label": "Satellite Data"},
    {"icon": CHART_BAR, "label": "Panel Econometrics"},
]

HERO_DYNAMIC_TAG_ICONS: dict[str, str] = {
    "constituencies": BUILDING,
    "year_range":     CALENDAR,
}

KPI_ICONS: list[str] = [BUILDING, MAP, CALENDAR, CUBE]

META_ICONS: dict[str, str] = {
    "Methods":  COG,
    "Data":     DATABASE,
    "Coverage": GLOBE,
    "Tools":    CODE,
}

FINDING_FALLBACK_ICON: str = PIN

# ── Key Findings ─────────────────────────────────────────────────────────────
# Each dict defines one finding card on the Overview page.
# Add / remove entries here; page layout code never changes.
# outcome + estimator must match keys in data_loader._POOLED_FILES.
FINDINGS_SPECS: list[dict] = [
    {
        "outcome": "NL",
        "estimator": "OLS",
        "variant": "Median",
        "variable": "Seasonal_Ratio",
        "variable_label": "Seasonal Ratio (flood coverage)",
        "outcome_label": "Night-light growth (Δlog NL)",
    },
    {
        "outcome": "NDBI",
        "estimator": "OLS",
        "variant": "Median",
        "variable": "Seasonal_Ratio",
        "variable_label": "Seasonal Ratio (flood coverage)",
        "outcome_label": "Built-up index change (NDBI)",
    },
]

# ── State-level headline findings (Overview page Key Findings section) ────────
# These are the primary results: state regressions where effects are significant.
# Pooled regressions show no significant effect — the aggregate null masks heterogeneity.
KEY_FINDINGS: list[dict] = [
    {
        "icon": TREND_DOWN,
        "label": "West Bengal — Night-lights",
        "outcome": "NL",
        "estimator": "OLS",
        "state_key": "WB",
        "variable": "Seasonal_Ratio",
        "interpretation": (
            "Higher flood exposure is associated with a statistically significant reduction "
            "in night-lights growth. A one-unit increase in seasonal flood water fraction "
            "is associated with a 32–39 percent reduction in economic activity growth."
        ),
    },
    {
        "icon": WRENCH,
        "label": "Bihar — Built-up Index (NDBI)",
        "outcome": "NDBI",
        "estimator": "OLS",
        "state_key": "BIHAR",
        "variable": "Seasonal_Ratio",
        "interpretation": (
            "Flood exposure predicts a significant decline in built-up index growth. "
            "Flood-affected constituencies see slower infrastructure accumulation."
        ),
    },
]

POOLED_NOTE: str = (
    "No statistically significant effect is detected in pooled regressions. "
    "The aggregate null masks heterogeneous state-level effects, consistent with "
    "variation in flood frequency, infrastructure quality, and institutional capacity "
    "across states."
)

# ── Study Area map ────────────────────────────────────────────────────────────
# Approximate (lon, lat) centroid per state key as it appears in panel["STATE"].
# No shapefiles exist in this project; these are the authoritative centroid source.
# Unknown state keys fall back to India's geographic centre (82, 22).
STATE_CENTROIDS: dict[str, tuple[float, float]] = {
    "Bihar":       (85.3, 25.1),
    "Jharkhand":   (85.9, 23.6),
    "Odisha":      (84.5, 20.9),
    "West Bengal": (88.3, 22.6),
    "WB":          (88.3, 22.6),
}

# ── Project metadata ──────────────────────────────────────────────────────────
# Additional method notes appended to the auto-derived estimator list on the Overview page.
METHODS_EXTRA: list[str] = ["District-level clustering"]

TOOLS: list[str] = [
    "Python", "pyfixest", "linearmodels", "Google Earth Engine", "QGIS", "Streamlit",
]
DATA_SOURCES: list[str] = [
    "VIIRS/DMSP Nighttime Lights (NL)",
    "Landsat-8 SR — NDVI, NDBI",
    "JRC Global Surface Water (Seasonal Ratio)",
    "Election Commission of India (AC boundaries)",
]

# ── GeoJSON layer registry ────────────────────────────────────────────────────
# Extensible: add district / constituency layers here in future.
GEO_LAYERS: dict[str, str] = {
    "state": "data/eastern_india_states.geojson",
    # "district":     "data/eastern_india_districts.geojson",  # future
    # "constituency": "data/eastern_india_acs.geojson",        # future
}
STATE_GEO_NAME_FIELD: str = "name"  # GeoJSON feature property key for state name

# Maps panel STATE column values → GeoJSON name property values (handles aliases)
STATE_NAME_MAP: dict[str, str] = {
    "Bihar":       "Bihar",
    "Jharkhand":   "Jharkhand",
    "Odisha":      "Odisha",
    "West Bengal": "West Bengal",
    "WB":          "West Bengal",
}

# ── Debug mode ────────────────────────────────────────────────────────────────
# Set True to show a diagnostics expander on the Overview page.
# Shows: data file paths, loaded file names, row counts, active specs, timestamps.
DEBUG_MODE: bool = False
