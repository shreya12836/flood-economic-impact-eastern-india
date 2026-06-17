from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data" / "processed" / "final_regression_dataset.xlsx"
TABLES = REPO_ROOT / "outputs" / "tables"

_POOLED_FILES = {
    ("NL",   "OLS"):  "Regression_Results_NL_OLS_Pooled.xlsx",
    ("NDBI", "OLS"):  "Regression_Results_NDBI_OLS_Pooled.xlsx",
    ("NL",   "TWFE"): "Regression_Results_Pooled_DistrictCluster.xlsx",
    ("NDBI", "TWFE"): "Regression_Results_NDBI_Pooled_DistrictCluster.xlsx",
}

_BYSTATE_FILES = {
    ("NL",   "OLS"):  "Regression_Results_NL_OLS_By_State.xlsx",
    ("NDBI", "OLS"):  "Regression_Results_NDBI_OLS_By_State.xlsx",
    ("NL",   "TWFE"): "Regression_Results_By_State.xlsx",
    ("NDBI", "TWFE"): "Regression_Results_NDBI_By_State.xlsx",
}

# Canonical display names for known state keys; unknown keys fall back to .title()
_DISPLAY_NAMES: dict[str, str] = {
    "BIHAR": "Bihar",
    "JHARKHAND": "Jharkhand",
    "ORISSA": "Odisha",   # historical census code; renamed from Orissa in 2011
    "WB": "West Bengal",
}

STARS = {"p < 0.01": "***", "p < 0.05": "**", "p < 0.10": "*", "n.s.": ""}


def _check_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"Results file not found: {path.name}. Run the regression pipeline first."
        )


def _read_sheet(path: Path, sheet: str, **kwargs) -> pd.DataFrame:
    try:
        return pd.read_excel(path, sheet_name=sheet, **kwargs)
    except Exception as exc:
        msg = str(exc).lower()
        if "worksheet" in msg or "not found" in msg:
            raise KeyError(
                f"Sheet '{sheet}' not found in {path.name}. Re-run the regression pipeline."
            ) from exc
        raise


@st.cache_data
def load_state_geojson(layer: str = "state") -> dict:
    from config import GEO_LAYERS
    rel_path = GEO_LAYERS[layer]
    geo_path = Path(__file__).resolve().parent.parent / rel_path
    if not geo_path.exists():
        raise FileNotFoundError(
            f"GeoJSON not found at {geo_path}. "
            "Run scripts/fetch_eastern_india_geo.py first."
        )
    with geo_path.open() as f:
        return json.load(f)


@st.cache_data
def load_panel() -> pd.DataFrame:
    return pd.read_excel(DATA, sheet_name="Panel")


@st.cache_data
def discover_states(outcome: str, estimator: str, variant: str) -> list[tuple[str, str]]:
    """Return [(state_key, display_name), ...] auto-discovered from All_States column headers.

    Adding a new state to the regression output (a new KEY_Coef column) surfaces it here
    without any code change.
    """
    bystate_file = TABLES / _BYSTATE_FILES[(outcome, estimator)]
    _check_file(bystate_file)
    df = _read_sheet(bystate_file, f"{variant}_All_States", nrows=0)
    keys = [c.removesuffix("_Coef") for c in df.columns if c.endswith("_Coef")]
    return [(k, _DISPLAY_NAMES.get(k, k.title())) for k in keys]


@st.cache_data
def load_pooled_table(outcome: str, estimator: str, variant: str) -> pd.DataFrame:
    """Full coefficient table for the pooled regression."""
    f = TABLES / _POOLED_FILES[(outcome, estimator)]
    _check_file(f)
    return _read_sheet(f, f"{variant}_Coef")


@st.cache_data
def load_state_table(outcome: str, estimator: str, variant: str, state_key: str) -> pd.DataFrame:
    """Full coefficient table for a single state."""
    f = TABLES / _BYSTATE_FILES[(outcome, estimator)]
    _check_file(f)
    return _read_sheet(f, f"{state_key}_{variant}")


@st.cache_data
def load_comparison_table(
    outcome: str, estimator: str, variant: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Wide comparison table: Variable x Pooled + all states.

    Returns (coef_df, stats_df). Each cell in coef_df is formatted as '0.1234***'.
    stats_df holds model-level rows (Observations, R-sq, etc.) in the same wide layout.

    Meta rows are detected dynamically: rows where the first state SE column is null.
    This handles OLS files ('R-squared', 'R-squared (overall)') and TWFE files
    ('Years', 'R-sq (within)') without a hardcoded list.
    """
    def fmt_coef(coef: float, sig: object) -> str:
        stars = STARS.get(str(sig).strip(), "")
        return f"{coef:.4f}{stars}"

    def fmt_meta(val: object) -> str:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "-"
        if isinstance(val, float) and val == int(val):
            return str(int(val))
        if isinstance(val, float):
            return f"{val:.4f}"
        return str(val)

    pooled_df = load_pooled_table(outcome, estimator, variant)
    bystate_file = TABLES / _BYSTATE_FILES[(outcome, estimator)]
    _check_file(bystate_file)
    all_df = _read_sheet(bystate_file, f"{variant}_All_States")
    states = discover_states(outcome, estimator, variant)

    # Detect meta rows dynamically: rows where the first state SE column is null/NaN
    first_se_col = f"{states[0][0]}_SE"
    is_meta = all_df[first_se_col].isna()

    pooled_idx = pooled_df.set_index("Variable")
    coef_df_raw = all_df[~is_meta].copy()
    meta_df_raw = all_df[is_meta].copy()
    coef_idx = coef_df_raw.set_index("Variable")

    coef_rows: list[dict] = []
    for var in coef_df_raw["Variable"]:
        row: dict = {"Variable": var}
        if var in pooled_idx.index:
            pr = pooled_idx.loc[var]
            row["Pooled"] = fmt_coef(pr["Coefficient"], pr["Significance"])
        else:
            row["Pooled"] = "-"
        for key, disp in states:
            if var in coef_idx.index:
                row[disp] = fmt_coef(
                    coef_idx.loc[var, f"{key}_Coef"],
                    coef_idx.loc[var, f"{key}_Sig"],
                )
            else:
                row[disp] = "-"
        coef_rows.append(row)

    meta_rows: list[dict] = []
    meta_idx = meta_df_raw.set_index("Variable")
    for var in meta_df_raw["Variable"]:
        row = {"Variable": var, "Pooled": "-"}
        for key, disp in states:
            row[disp] = fmt_meta(meta_idx.loc[var, f"{key}_Coef"])
        meta_rows.append(row)

    return pd.DataFrame(coef_rows), pd.DataFrame(meta_rows)


@st.cache_data
def load_spec_meta(outcome: str, estimator: str, variant: str) -> dict[str, str]:
    """Pull key spec metadata from the pooled Stats sheet."""
    f = TABLES / _POOLED_FILES[(outcome, estimator)]
    if not f.exists():
        return {}
    df = pd.read_excel(f, sheet_name=f"{variant}_Stats", index_col=0, header=0)
    df.columns = ["Value"]
    def _get(key: str) -> str:
        return str(df.loc[key, "Value"]) if key in df.index else "—"
    return {
        "estimator": _get("Estimator"),
        "se": _get("Std errors"),
        "n_obs": _get("Observations"),
        "r2": _get("R-squared"),
    }


@st.cache_data
def load_robustness_summary(outcome: str, variable: str) -> dict:
    """Check sign consistency of variable across all estimator × variant combinations.

    Compares OLS Median (primary) against OLS Mean and all TWFE variants for the same
    outcome. Returns a plain-language note suitable for the Overview findings card.
    """
    coefs: dict[str, float] = {}
    for (out, est), fname in _POOLED_FILES.items():
        if out != outcome:
            continue
        f = TABLES / fname
        if not f.exists():
            continue
        for variant in ("Median", "Mean"):
            try:
                coef_df = _read_sheet(f, f"{variant}_Coef")
                row = coef_df[coef_df["Variable"] == variable]
                if not row.empty:
                    coefs[f"{est} {variant}"] = float(row.iloc[0]["Coefficient"])
            except Exception:
                pass

    if not coefs:
        return {"note": None}

    signs = {1 if v > 0 else -1 for v in coefs.values()}
    consistent = len(signs) == 1
    n = len(coefs)
    direction = "negative" if list(coefs.values())[0] < 0 else "positive"

    if consistent:
        note = (
            f"Direction ({direction}) consistent across all {n} specification checks "
            f"(Median/Mean, OLS/TWFE)."
        )
    else:
        note = (
            "Direction varies across specifications — "
            "see Regression Results page for full comparison."
        )
    return {"note": note, "consistent": consistent, "n_checked": n}


def discover_outcomes() -> list[str]:
    """Return sorted unique outcome names from _POOLED_FILES — no I/O."""
    return sorted({outcome for outcome, _ in _POOLED_FILES})


@st.cache_data
def load_state_finding(
    outcome: str, estimator: str, state_key: str, variable: str
) -> dict[str, dict] | None:
    """Load Median and Mean coefficients for one state and variable.

    Returns {"Median": {"coef", "sig", "stars"}, "Mean": {...}} or None if missing.
    """
    fname = _BYSTATE_FILES.get((outcome, estimator))
    if not fname:
        return None
    f = TABLES / fname
    if not f.exists():
        return None
    results: dict[str, dict] = {}
    for variant in ("Median", "Mean"):
        try:
            df = _read_sheet(f, f"{state_key}_{variant}")
            row = df[df["Variable"] == variable]
            if not row.empty:
                r = row.iloc[0]
                results[variant] = {
                    "coef":  float(r["Coefficient"]),
                    "sig":   str(r["Significance"]),
                    "stars": STARS.get(str(r["Significance"]).strip(), ""),
                }
        except Exception:
            pass
    return results if results else None


@st.cache_data
def load_overview_findings(
    outcome: str, estimator: str, variant: str, variable: str
) -> dict | None:
    """Load coefficient + model stats for one spec/variable. Returns None on any failure."""
    fname = _POOLED_FILES.get((outcome, estimator), "")
    if not fname:
        return None
    f = TABLES / fname
    if not f.exists():
        return None
    try:
        coef_df = _read_sheet(f, f"{variant}_Coef")
        row = coef_df[coef_df["Variable"] == variable]
        if row.empty:
            return None
        r = row.iloc[0]
        meta = load_spec_meta(outcome, estimator, variant)
        return {
            "coef":            float(r["Coefficient"]),
            "se":              float(r["Std_Error"]),
            "sig":             str(r["Significance"]),
            "stars":           STARS.get(str(r["Significance"]).strip(), ""),
            "ci_low":          float(r["CI_low_95"]),
            "ci_high":         float(r["CI_high_95"]),
            "n_obs":           meta.get("n_obs", "—"),
            "r2":              meta.get("r2", "—"),
            "estimator_label": meta.get("estimator", "—"),
            "se_label":        meta.get("se", "—"),
            "source_file":     fname,
        }
    except Exception:
        return None


@st.cache_data
def load_forest_data(outcome: str, estimator: str, variant: str) -> list[dict]:
    """Return list of rows for the forest plot: pooled + 4 states."""
    pooled_file = TABLES / _POOLED_FILES[(outcome, estimator)]
    bystate_file = TABLES / _BYSTATE_FILES[(outcome, estimator)]
    _check_file(pooled_file)
    _check_file(bystate_file)

    pooled_df = _read_sheet(pooled_file, f"{variant}_Coef")
    pooled_row = pooled_df[pooled_df["Variable"] == "Seasonal_Ratio"].iloc[0]

    rows = [
        {
            "label": "All states (pooled)",
            "coef": pooled_row["Coefficient"],
            "ci_low": pooled_row["CI_low_95"],
            "ci_high": pooled_row["CI_high_95"],
            "sig": pooled_row["Significance"],
            "is_pooled": True,
        }
    ]

    by_df = _read_sheet(bystate_file, f"{variant}_All_States")
    sr_row = by_df[by_df["Variable"] == "Seasonal_Ratio"].iloc[0]

    state_keys = [c.removesuffix("_Coef") for c in by_df.columns if c.endswith("_Coef")]
    for col_key in state_keys:
        label = _DISPLAY_NAMES.get(col_key, col_key.title())
        coef = sr_row[f"{col_key}_Coef"]
        se = sr_row[f"{col_key}_SE"]
        sig = sr_row[f"{col_key}_Sig"]
        rows.append(
            {
                "label": label,
                "coef": coef,
                "ci_low": coef - 1.96 * se,
                "ci_high": coef + 1.96 * se,
                "sig": sig,
                "is_pooled": False,
            }
        )

    return rows
