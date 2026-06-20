"""By-state regression with NDBI_t as the outcome (TWFE-LDV via pyfixest).

Specification per state:
    NDBI_it = b1*Seasonal_Ratio_it
            + b2*NDVI_{i,t-1}
            + b3*NL_{i,t-1}
            + b4*NDBI_{i,t-1}
            + alpha_i + gamma_t + e_it
    SEs clustered at district (ST_CODE_DT_CODE).

Nickell bias caveat applies (T=5, ~20% downward bias on b4).
"""
from pathlib import Path
import numpy as np
import pandas as pd
from pyfixest.estimation import feols

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(REPO_ROOT))
from src.utils import significance_label

DATA = REPO_ROOT / "data" / "processed" / "final_regression_dataset.xlsx"
OUT = REPO_ROOT / "outputs" / "tables" / "Regression_Results_NDBI_OLS_By_State.xlsx"

STATES = {
    "BIHAR": "Bihar",
    "JHARKHAND": "Jharkhand",
    "ORISSA": "Odisha",
    "WB": "WB",
}


def run_state(df_state, suffix):
    needed = [
        f"NDBI_{suffix}", f"NDBI_{suffix}_t_minus_1",
        f"NDVI_{suffix}_t_minus_1", f"NL_{suffix}_t_minus_1",
        "Seasonal_Ratio", "AC_UID", "YEAR", "DISTRICT_ID",
    ]
    panel = df_state.dropna(subset=needed).copy()

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
            "Variable": r["Variable"],
            "Coefficient": r["Estimate"],
            "Std_Error": r["Std. Error"],
            "t_stat": r["t value"],
            "p_value": r["Pr(>|t|)"],
            "Significance": significance_label(r["Pr(>|t|)"]),
        })

    stats = {
        "Observations": int(fit._N),
        "ACs (entities)": int(panel["AC_UID"].nunique()),
        "Districts (clusters)": int(panel["DISTRICT_ID"].nunique()),
        "R-squared": float(fit._r2_within),
        "R-squared (overall)": float(fit._r2),
    }
    return pd.DataFrame(rows), stats


def main():
    df = pd.read_excel(DATA)
    df["DISTRICT_ID"] = df["ST_CODE"].astype(str) + "_" + df["DT_CODE"].astype(str)

    out_sheets = {}
    stats_records = []

    for suffix in ["median", "mean"]:
        per_state_coef = {}
        per_state_stats = {}
        for state_label, state_name in STATES.items():
            sub = df[df["STATE"] == state_name].copy()
            cdf, st = run_state(sub, suffix)
            per_state_coef[state_label] = cdf
            per_state_stats[state_label] = st

        var_order = per_state_coef["BIHAR"]["Variable"].tolist()
        all_states = pd.DataFrame({"Variable": var_order})
        for state_label in STATES:
            cdf = per_state_coef[state_label].set_index("Variable")
            all_states[f"{state_label}_Coef"] = all_states["Variable"].map(cdf["Coefficient"])
            all_states[f"{state_label}_SE"] = all_states["Variable"].map(cdf["Std_Error"])
            all_states[f"{state_label}_Sig"] = all_states["Variable"].map(cdf["Significance"])

        meta_rows = ["Observations", "ACs (entities)", "Districts (clusters)", "R-squared", "R-squared (overall)"]
        meta_df = pd.DataFrame({"Variable": meta_rows})
        for state_label in STATES:
            meta_df[f"{state_label}_Coef"] = [per_state_stats[state_label][m] for m in meta_rows]
            meta_df[f"{state_label}_SE"] = [None] * len(meta_rows)
            meta_df[f"{state_label}_Sig"] = [None] * len(meta_rows)
        all_states = pd.concat([all_states, meta_df], ignore_index=True)

        sheet_name = "Median_All_States" if suffix == "median" else "Mean_All_States"
        out_sheets[sheet_name] = all_states

        for state_label in STATES:
            sub_sheet = f"{state_label}_{'Median' if suffix == 'median' else 'Mean'}"
            out_sheets[sub_sheet] = per_state_coef[state_label]
            stats_records.append({
                "Model": "Median" if suffix == "median" else "Mean",
                "State": state_label,
                **per_state_stats[state_label],
            })

    stats_by_state = {}
    for s in stats_records:
        stats_by_state.setdefault(s["State"], []).append(s)
    for state_label, recs in stats_by_state.items():
        out_sheets[f"{state_label}_Stats"] = pd.DataFrame(recs)

    notes = pd.DataFrame({"Note": [
        "Outcome: NDBI_t (level).",
        "Estimator: TWFE-LDV via pyfixest, run separately by state. FEs: AC_UID + YEAR.",
        "Regressors: Seasonal_Ratio (contemp.), NDVI_{t-1}, NL_{t-1}, NDBI_{t-1} (lagged DV).",
        "SEs clustered by district (ST_CODE_DT_CODE). Significance: *** p<0.01, ** p<0.05, * p<0.10.",
        "Nickell bias caveat: lagged NDBI_{t-1} with AC FE biases its own coefficient downward",
        "  by ~1/T (T=5, so ~20%). Flood coefficient (Seasonal_Ratio) is far less affected.",
        "R-squared row = within-R^2 (post-FE-absorption). Overall R^2 reported separately.",
    ]})

    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        notes.to_excel(xw, sheet_name="Notes", index=False)
        for name, frame in out_sheets.items():
            frame.to_excel(xw, sheet_name=name, index=False)

    print(f"Saved: {OUT}")
    for sheet in ["Median_All_States", "Mean_All_States"]:
        print(f"\n--- {sheet} ---")
        print(out_sheets[sheet].to_string(index=False))


if __name__ == "__main__":
    main()
