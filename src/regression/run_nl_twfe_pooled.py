"""Pooled district-clustered TWFE regression with Delta log NL as the outcome (linearmodels cross-check).

Replicates run_nl_ols_pooled.py (pyfixest primary) using linearmodels PanelOLS.
Specification:
    log(NL_it) - log(NL_{i,t-1}) = b0 + b1*Seasonal_Ratio_it
                                  + b2*NDVI_{i,t-1}
                                  + b3*NDBI_{i,t-1}
                                  + alpha_i + gamma_t + e_it

Two variants: Median (uses *_median series) and Mean (uses *_mean series).
SEs clustered at district (ST_CODE_DT_CODE uniquely identifies district).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(REPO_ROOT))
from src.utils import significance_label

DATA = REPO_ROOT / "data" / "processed" / "final_regression_dataset.xlsx"
OUT = REPO_ROOT / "outputs" / "tables" / "Regression_Results_Pooled_DistrictCluster.xlsx"


def run_one(df: pd.DataFrame, suffix: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    working = df.copy()
    working["dlog_NL"] = np.log(working[f"NL_{suffix}"]) - np.log(working[f"NL_{suffix}_t_minus_1"])

    X = pd.DataFrame(
        {
            "Seasonal_Ratio": working["Seasonal_Ratio"],
            f"NDVI_{suffix}_t_minus_1": working[f"NDVI_{suffix}_t_minus_1"],
            f"NDBI_{suffix}_t_minus_1": working[f"NDBI_{suffix}_t_minus_1"],
            "const": 1.0,
        },
        index=working.index,
    )

    panel = pd.concat(
        [working["dlog_NL"], X, working[["AC_UID", "YEAR", "DISTRICT_ID"]]],
        axis=1,
    ).replace([np.inf, -np.inf], np.nan).dropna(subset=["dlog_NL"])
    panel = panel.set_index(["AC_UID", "YEAR"])

    reg_cols = ["const", "Seasonal_Ratio", f"NDVI_{suffix}_t_minus_1", f"NDBI_{suffix}_t_minus_1"]
    dep = panel["dlog_NL"]
    regs = panel[reg_cols]
    clusters = panel["DISTRICT_ID"]

    mod = PanelOLS(dep, regs, entity_effects=True, time_effects=True, drop_absorbed=True)
    res = mod.fit(cov_type="clustered", clusters=clusters)

    name_map = {
        "const": "beta_0 (Constant)",
        "Seasonal_Ratio": "Seasonal_Ratio",
        f"NDVI_{suffix}_t_minus_1": f"NDVI_{suffix}_t_minus_1",
        f"NDBI_{suffix}_t_minus_1": f"NDBI_{suffix}_t_minus_1",
    }
    coef_rows = []
    for v in reg_cols:
        ci = res.conf_int().loc[v]
        coef_rows.append(
            {
                "Model": "Median" if suffix == "median" else "Mean",
                "Variable": name_map[v],
                "Coefficient": res.params[v],
                "Std_Error": res.std_errors[v],
                "t_stat": res.tstats[v],
                "p_value": res.pvalues[v],
                "CI_low_95": ci["lower"],
                "CI_high_95": ci["upper"],
                "Significance": significance_label(res.pvalues[v]),
            }
        )

    n_districts = clusters.nunique()
    label = "Median" if suffix == "median" else "Mean"
    stats_rows = [
        ("Model", label),
        (
            "Equation",
            f"log(NL_{suffix})_t - log(NL_{suffix})_(t-1) = b0 + b1*Seasonal_Ratio"
            f" + b2*NDVI_{suffix}_(t-1) + b3*NDBI_{suffix}_(t-1) + a_i + g_t + e_it",
        ),
        ("Estimator", "Two-way FE (linearmodels PanelOLS) — cross-check of pyfixest primary"),
        ("Entity FE", "AC (AC_UID) = alpha_i"),
        ("Time FE", "YEAR = gamma_t"),
        ("Std errors", f"Clustered by DISTRICT (n={n_districts} districts)"),
        ("Observations", int(res.nobs)),
        ("Entities (ACs)", int(res.entity_info.total)),
        ("Time periods", int(res.time_info.total)),
        ("R-sq (within)", float(res.rsquared_within)),
        ("R-sq (between)", float(res.rsquared_between)),
        ("R-sq (overall)", float(res.rsquared_overall)),
        ("F-statistic (robust)", float(res.f_statistic_robust.stat)),
        ("F p-value (robust)", float(res.f_statistic_robust.pval)),
    ]
    return pd.DataFrame(coef_rows), pd.DataFrame(stats_rows, columns=["Item", "Value"])


def main() -> None:
    df = pd.read_excel(DATA)
    df["DISTRICT_ID"] = df["ST_CODE"].astype(str) + "_" + df["DT_CODE"].astype(str)

    med_coef, med_stats = run_one(df, "median")
    mean_coef, mean_stats = run_one(df, "mean")

    notes = pd.DataFrame(
        {
            "Note": [
                "Outcome: Delta log NL = log(NL_t) - log(NL_{t-1}) (year-on-year growth in night-light radiance).",
                "Lagged regressors: NDVI_{t-1}, NDBI_{t-1}. Flood (Seasonal_Ratio) is contemporaneous.",
                "Two-way FE: AC (entity) + YEAR (time). Constant is explicit; entity/time effects absorbed by PanelOLS.",
                "SEs clustered by district (ST_CODE_DT_CODE). Significance: *** p<0.01, ** p<0.05, * p<0.10.",
                "Cross-check: same specification as run_nl_ols_pooled.py (pyfixest); coefficients should be close.",
            ]
        }
    )
    comparison = pd.DataFrame(
        {
            "Variable": med_coef["Variable"],
            "Median_Coef": med_coef["Coefficient"].round(4),
            "Median_Sig": med_coef["Significance"],
            "Mean_Coef": mean_coef["Coefficient"].round(4),
            "Mean_Sig": mean_coef["Significance"],
        }
    )

    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        notes.to_excel(xw, sheet_name="Notes", index=False)
        comparison.to_excel(xw, sheet_name="Comparison", index=False)
        med_coef.to_excel(xw, sheet_name="Median_Coef", index=False)
        med_stats.to_excel(xw, sheet_name="Median_Stats", index=False)
        mean_coef.to_excel(xw, sheet_name="Mean_Coef", index=False)
        mean_stats.to_excel(xw, sheet_name="Mean_Stats", index=False)

    print(f"Saved: {OUT}")
    print("\nMedian:")
    print(med_coef.to_string(index=False))
    print("\nMean:")
    print(mean_coef.to_string(index=False))


if __name__ == "__main__":
    main()
