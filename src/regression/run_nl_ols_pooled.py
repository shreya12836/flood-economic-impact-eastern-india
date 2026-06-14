"""Pooled regression with Delta log NL as the outcome (TWFE via pyfixest).

Specification:
    log NL_it - log NL_{i,t-1} = b1*Seasonal_Ratio_it
                                + b2*NDVI_{i,t-1} + b3*NDBI_{i,t-1}
                                + alpha_i + gamma_t + e_it
    alpha_i = AC fixed effects, gamma_t = year fixed effects.
    SEs clustered at district (ST_CODE_DT_CODE).

Estimator: pyfixest.feols (formula API; FE absorbed, no intercept reported).
"""
from pathlib import Path
import numpy as np
import pandas as pd
from pyfixest.estimation import feols

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data" / "processed" / "final_regression_dataset.xlsx"
OUT = REPO_ROOT / "outputs" / "tables" / "Regression_Results_NL_OLS_Pooled.xlsx"


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
        f"NL_{suffix}", f"NL_{suffix}_t_minus_1",
        f"NDVI_{suffix}_t_minus_1", f"NDBI_{suffix}_t_minus_1",
        "Seasonal_Ratio", "AC_UID", "YEAR", "DISTRICT_ID",
    ]
    panel = df.dropna(subset=needed).copy()
    panel["dlog_NL"] = np.log(panel[f"NL_{suffix}"]) - np.log(panel[f"NL_{suffix}_t_minus_1"])
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(subset=["dlog_NL"])

    fml = (
        f"dlog_NL ~ Seasonal_Ratio "
        f"+ NDVI_{suffix}_t_minus_1 "
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
        ("Equation", f"log(NL_{suffix})_t - log(NL_{suffix})_(t-1) = b1*Seasonal_Ratio + b2*NDVI_{suffix}_(t-1) + b3*NDBI_{suffix}_(t-1) + alpha_i + gamma_t + e_it"),
        ("Estimator", "TWFE via pyfixest (AC + YEAR fixed effects)"),
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
        "Outcome: Delta log NL = log(NL_t) - log(NL_{t-1}).",
        "Estimator: TWFE via pyfixest. Fixed effects: AC_UID and YEAR (absorbed; no intercept).",
        "Lagged regressors: NDVI_{t-1}, NDBI_{t-1}. Seasonal_Ratio contemporaneous.",
        "SEs clustered by district (ST_CODE_DT_CODE). Significance: *** p<0.01, ** p<0.05, * p<0.10.",
        "R-squared in this file refers to within-R^2 (after FE absorption); overall R^2 reported separately.",
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
