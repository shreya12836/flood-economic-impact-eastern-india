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

_STATES = [
    ("BIHAR", "Bihar"),
    ("JHARKHAND", "Jharkhand"),
    ("ORISSA", "Odisha"),
    ("WB", "West Bengal"),
]


@st.cache_data
def load_panel() -> pd.DataFrame:
    return pd.read_excel(DATA, sheet_name="Panel")


@st.cache_data
def load_forest_data(outcome: str, estimator: str, variant: str) -> list[dict]:
    """Return list of rows for the forest plot: pooled + 4 states."""
    pooled_file = TABLES / _POOLED_FILES[(outcome, estimator)]
    bystate_file = TABLES / _BYSTATE_FILES[(outcome, estimator)]

    coef_sheet = f"{variant}_Coef"
    all_states_sheet = f"{variant}_All_States"

    pooled_df = pd.read_excel(pooled_file, sheet_name=coef_sheet)
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

    by_df = pd.read_excel(bystate_file, sheet_name=all_states_sheet)
    sr_row = by_df[by_df["Variable"] == "Seasonal_Ratio"].iloc[0]

    for col_key, label in _STATES:
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
