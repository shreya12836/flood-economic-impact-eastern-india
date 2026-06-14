"""Pooled regression with NDBI_t as the outcome (TWFE-LDV via pyfixest).

Specification:
    NDBI_it = b1*Seasonal_Ratio_it
            + b2*NDVI_{i,t-1}
            + b3*NL_{i,t-1}
            + b4*NDBI_{i,t-1}
            + alpha_i + gamma_t + e_it
    alpha_i = AC fixed effects, gamma_t = year fixed effects.
    SEs clustered at district (ST_CODE_DT_CODE).

Note: lagged dependent variable (NDBI_{t-1}) on RHS together with AC FE
introduces Nickell bias on b4 of order 1/T (T=5 here, so ~20% downward).
b1 (flood) is far less affected.

Estimator: pyfixest.feols (formula API; FE absorbed, no intercept reported).
"""
from pathlib import Path
import numpy as np
import pandas as pd
from pyfixest.estimation import feols

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data" / "processed" / "final_regression_dataset.xlsx"
OUT = REPO_ROOT / "outputs" / "tables" / "Regression_Results_NDBI_OLS_Pooled.xlsx"


def stars(p):
    if p < 0.01:
        return "p < 0.01"
    if p < 0.05:
        return "p < 0.05"
    if p < 0.10:
        return "p < 0.10"
    return "n.s."


def run_one(df, suffix):
    needed = [
        f"NDBI_{suffix}", f"NDBI_{suffix}_t_minus_1",
        f"NDVI_{suffix}_t_minus_1", f"NL_{suffix}_t_minus_1",
        "Seasonal_Ratio", "AC_UID", "YEAR", "DISTRICT_ID",
    ]
    panel = df.dropna(subset=needed).copy()

    fml = (
        f"NDBI_{suffix} ~ Seasonal_Ratio "
        f"+ NDVI_{suffix}_t_minus_1 "
        f"+ NL_{suffix}_t_minus_1 "
        f"+ NDBI_{suffix}_t_minus_1 "
        f"| AC_UID + YEAR"
    )
    fit = feols(fml, data=panel, vcov={"CRV1": "DISTRICT_ID"})
    tidy = fit.tidy().reset_index().rename(columns={"Coefficient": "Variable"})

    rows = []
    for _, r in tidy.iterrows():
        rows.append({
            "Model": "Median" if suffix == "median" else "Mean",
            "Variable": r["Variable"],
            "Coefficient": r["Estimate"],
            "Std_Error": r["Std. Error"],
            "t_stat": r["t value"],
            "p_value": r["Pr(>|t|)"],
            "CI_low_95": r["2.5%"],
            "CI_high_95": r["97.5%"],
            "Significance": stars(r["Pr(>|t|)"]),
        })

    n_clusters = panel["DISTRICT_ID"].nunique()
    n_acs = panel["AC_UID"].nunique()
    stats = [
        ("Model", "Median" if suffix == "median" else "Mean"),
        ("Equation", f"NDBI_{suffix}_it = b1*Seasonal_Ratio + b2*NDVI_{suffix}_(t-1) + b3*NL_{suffix}_(t-1) + b4*NDBI_{suffix}_(t-1) + alpha_i + gamma_t + e_it"),
        ("Estimator", "TWFE-LDV via pyfixest (AC + YEAR fixed effects, lagged DV on RHS)"),
        ("Std errors", f"Clustered by DISTRICT (n={n_clusters} districts)"),
        ("Observations", int(fit._N)),
        ("ACs (entities)", int(n_acs)),
        ("R-squared", float(fit._r2_within)),
        ("R-squared (within)", float(fit._r2_within)),
        ("R-squared (overall)", float(fit._r2)),
    ]
    return pd.DataFrame(rows), pd.DataFrame(stats, columns=["Item", "Value"])


def main():
    df = pd.read_excel(DATA)
    df["DISTRICT_ID"] = df["ST_CODE"].astype(str) + "_" + df["DT_CODE"].astype(str)

    med_coef, med_stats = run_one(df, "median")
    mean_coef, mean_stats = run_one(df, "mean")

    notes = pd.DataFrame({"Note": [
        "Outcome: NDBI_t (level).",
        "Estimator: TWFE-LDV via pyfixest. Fixed effects: AC_UID and YEAR (absorbed; no intercept).",
        "Regressors: Seasonal_Ratio (contemp.), NDVI_{t-1}, NL_{t-1}, NDBI_{t-1} (lagged DV).",
        "SEs clustered by district (ST_CODE_DT_CODE). Significance: *** p<0.01, ** p<0.05, * p<0.10.",
        "Nickell bias caveat: lagged NDBI_{t-1} together with AC FE biases its own coefficient",
        "  downward by ~1/T (T=5, so ~20%). Flood coefficient (Seasonal_Ratio) is far less affected.",
        "R-squared in this file refers to within-R^2 (after FE absorption); overall R^2 separate.",
    ]})
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
