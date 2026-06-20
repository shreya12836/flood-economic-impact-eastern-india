"""Pooled district-clustered TWFE regression with NDBI_t (level) as the outcome (linearmodels cross-check).

Replicates run_ndbi_ols_pooled.py (pyfixest primary) using linearmodels PanelOLS.
Specification (per dissertation Eq 2):
    NDBI_it = b0 + b1*Seasonal_Ratio_it
            + b2*NDVI_{i,t-1}
            + b3*NL_{i,t-1}
            + b4*NDBI_{i,t-1}   <- lagged dependent variable
            + alpha_i + gamma_t + e_it

Note: lagged DV (NDBI_{t-1}) with entity FE introduces Nickell bias ~1/T ≈ 20% on b4.
The flood coefficient (b1) is far less affected.

Two variants: Median (uses *_median series) and Mean (uses *_mean series).
SEs clustered at district (state+district code uniquely identifies district).
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
OUT = REPO_ROOT / "outputs" / "tables" / "Regression_Results_NDBI_Pooled_DistrictCluster.xlsx"


def run_one(df, suffix):
    y = df[f"NDBI_{suffix}"]
    X = pd.DataFrame({
        "Seasonal_Ratio": df["Seasonal_Ratio"],
        f"NDVI_{suffix}_t_minus_1": df[f"NDVI_{suffix}_t_minus_1"],
        f"NL_{suffix}_t_minus_1": df[f"NL_{suffix}_t_minus_1"],
        f"NDBI_{suffix}_t_minus_1": df[f"NDBI_{suffix}_t_minus_1"],
    }, index=df.index)
    X["const"] = 1.0

    panel = pd.concat([y.rename("ndbi_level"), X, df[["AC_UID", "YEAR", "DISTRICT_ID"]]], axis=1).dropna()
    panel = panel.set_index(["AC_UID", "YEAR"])

    dep = panel["ndbi_level"]
    regs = panel[["const", "Seasonal_Ratio", f"NDVI_{suffix}_t_minus_1", f"NL_{suffix}_t_minus_1", f"NDBI_{suffix}_t_minus_1"]]
    clusters = panel["DISTRICT_ID"]

    mod = PanelOLS(dep, regs, entity_effects=True, time_effects=True, drop_absorbed=True)
    res = mod.fit(cov_type="clustered", clusters=clusters)

    coef_rows = []
    name_map = {
        "const": "beta_0 (Constant)",
        "Seasonal_Ratio": "Seasonal_Ratio",
        f"NDVI_{suffix}_t_minus_1": f"NDVI_{suffix}_t_minus_1",
        f"NL_{suffix}_t_minus_1": f"NL_{suffix}_t_minus_1",
        f"NDBI_{suffix}_t_minus_1": f"NDBI_{suffix}_t_minus_1",
    }
    for v in regs.columns:
        b = res.params[v]
        se = res.std_errors[v]
        t = res.tstats[v]
        p = res.pvalues[v]
        ci = res.conf_int().loc[v]
        coef_rows.append({
            "Model": "Median" if suffix == "median" else "Mean",
            "Variable": name_map[v],
            "Coefficient": b,
            "Std_Error": se,
            "t_stat": t,
            "p_value": p,
            "CI_low_95": ci["lower"],
            "CI_high_95": ci["upper"],
            "Significance": significance_label(p),
        })

    n_districts = clusters.nunique()
    stats_rows = [
        ("Model", "Median" if suffix == "median" else "Mean"),
        ("Equation", f"NDBI_{suffix}_it = b0 + b1*Seasonal_Ratio + b2*NDVI_{suffix}_(t-1) + b3*NL_{suffix}_(t-1) + b4*NDBI_{suffix}_(t-1) + a_i + g_t + e_it"),
        ("Estimator", "Two-way FE (linearmodels PanelOLS) — cross-check of pyfixest primary (LDV spec)"),
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


def main():
    df = pd.read_excel(DATA)
    df["DISTRICT_ID"] = df["ST_CODE"].astype(str) + "_" + df["DT_CODE"].astype(str)

    med_coef, med_stats = run_one(df, "median")
    mean_coef, mean_stats = run_one(df, "mean")

    notes = pd.DataFrame({
        "Note": [
            "Outcome: NDBI_t (level; NDBI is bounded in [-1,1]).",
            "Regressors: Seasonal_Ratio (contemp.), NDVI_{t-1}, NL_{t-1}, NDBI_{t-1} (lagged DV).",
            "Two-way FE: AC (entity) + YEAR (time). Constant is explicit; FE absorbed by PanelOLS.",
            "SEs clustered by district (ST_CODE_DT_CODE). Significance: *** p<0.01, ** p<0.05, * p<0.10.",
            "Nickell bias: lagged NDBI_{t-1} with entity FE biases its coefficient ~1/T ≈ 20%; flood coef far less affected.",
            "Cross-check: same specification as run_ndbi_ols_pooled.py (pyfixest); coefficients should be close.",
        ]
    })
    comparison = pd.DataFrame({
        "Variable": med_coef["Variable"],
        "Median_Coef": med_coef["Coefficient"].round(4),
        "Median_Sig": med_coef["Significance"],
        "Mean_Coef": mean_coef["Coefficient"].round(4),
        "Mean_Sig": mean_coef["Significance"],
    })

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
