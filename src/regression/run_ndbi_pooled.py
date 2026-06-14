"""Pooled district-clustered TWFE regression with Delta NDBI as the outcome.

Specification (per dissertation):
    NDBI_it - NDBI_{i,t-1} = b0 + b1*Seasonal_Ratio_it
                            + b2*NDVI_{i,t-1}
                            + b3*NL_{i,t-1}
                            + alpha_i + gamma_t + e_it

Two variants: Median (uses *_median series) and Mean (uses *_mean series).
SEs clustered at district (state+district code uniquely identifies district).
"""
from pathlib import Path
import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data" / "processed" / "final_regression_dataset.xlsx"
OUT = REPO_ROOT / "outputs" / "tables" / "Regression_Results_NDBI_Pooled_DistrictCluster.xlsx"


def stars(p):
    if p < 0.01:
        return "p < 0.01"
    if p < 0.05:
        return "p < 0.05"
    if p < 0.10:
        return "p < 0.10"
    return "n.s."


def run_one(df, suffix):
    y = df[f"NDBI_{suffix}"] - df[f"NDBI_{suffix}_t_minus_1"]
    X = pd.DataFrame({
        "Seasonal_Ratio": df["Seasonal_Ratio"],
        f"NDVI_{suffix}_t_minus_1": df[f"NDVI_{suffix}_t_minus_1"],
        f"NL_{suffix}_t_minus_1": df[f"NL_{suffix}_t_minus_1"],
    }, index=df.index)
    X["const"] = 1.0

    panel = pd.concat([y.rename("delta_ndbi"), X, df[["AC_UID", "YEAR", "DISTRICT_ID"]]], axis=1).dropna()
    panel = panel.set_index(["AC_UID", "YEAR"])

    dep = panel["delta_ndbi"]
    regs = panel[["const", "Seasonal_Ratio", f"NDVI_{suffix}_t_minus_1", f"NL_{suffix}_t_minus_1"]]
    clusters = panel["DISTRICT_ID"]

    mod = PanelOLS(dep, regs, entity_effects=True, time_effects=True, drop_absorbed=True)
    res = mod.fit(cov_type="clustered", clusters=clusters)

    coef_rows = []
    name_map = {
        "const": "beta_0 (Constant)",
        "Seasonal_Ratio": "Seasonal_Ratio",
        f"NDVI_{suffix}_t_minus_1": f"NDVI_{suffix}_t_minus_1",
        f"NL_{suffix}_t_minus_1": f"NL_{suffix}_t_minus_1",
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
            "Significance": stars(p),
        })

    n_districts = panel.reset_index()["DISTRICT_ID"].nunique() if "DISTRICT_ID" in panel.reset_index().columns else clusters.nunique()
    stats_rows = [
        ("Model", "Median" if suffix == "median" else "Mean"),
        ("Equation", f"NDBI_{suffix}_t - NDBI_{suffix}_(t-1) = b0 + b1*Seasonal_Ratio + b2*NDVI_{suffix}_(t-1) + b3*NL_{suffix}_(t-1) + a_i + g_t + e_it"),
        ("Estimator", "Two-way FE (PanelOLS) with explicit constant"),
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
            "Outcome: Delta NDBI = NDBI_t - NDBI_{t-1} (level change; NDBI is bounded in [-1,1]).",
            "Lagged regressors: NDVI_{t-1}, NL_{t-1}. Flood (Seasonal_Ratio) is contemporaneous.",
            "Two-way fixed effects: AC (entity) + YEAR (time). Constant absorbed by FE; reported beta_0 is the implied intercept.",
            "SEs clustered by district (ST_CODE_DT_CODE). Significance: *** p<0.01, ** p<0.05, * p<0.10.",
            "Sample: 2016-2019 (need t-1 covariates).",
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
