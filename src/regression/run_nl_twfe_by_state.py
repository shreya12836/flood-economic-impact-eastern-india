"""By-state district-clustered TWFE regression with Delta log NL as the outcome (linearmodels cross-check).

Replicates run_nl_ols_by_state.py (pyfixest primary) using linearmodels PanelOLS,
run separately on each of the 4 states.
Specification per state:
    log(NL_it) - log(NL_{i,t-1}) = b0 + b1*Seasonal_Ratio_it
                                  + b2*NDVI_{i,t-1}
                                  + b3*NDBI_{i,t-1}
                                  + alpha_i + gamma_t + e_it

Outputs Median_All_States and Mean_All_States summary sheets (one row per variable,
columns per state with Coef/SE/Sig), plus per-state coefficient sheets and a stats sheet.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data" / "processed" / "final_regression_dataset.xlsx"
OUT = REPO_ROOT / "outputs" / "tables" / "Regression_Results_By_State.xlsx"

STATES = {
    "BIHAR": "Bihar",
    "JHARKHAND": "Jharkhand",
    "ORISSA": "Odisha",
    "WB": "WB",
}


def stars(p: float) -> str:
    if p < 0.01:
        return "p < 0.01"
    if p < 0.05:
        return "p < 0.05"
    if p < 0.10:
        return "p < 0.10"
    return "n.s."


def run_state(df_state: pd.DataFrame, suffix: str) -> tuple[pd.DataFrame, dict]:
    working = df_state.copy()
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
    rows = []
    for v in reg_cols:
        rows.append(
            {
                "Variable": name_map[v],
                "Coefficient": res.params[v],
                "Std_Error": res.std_errors[v],
                "t_stat": res.tstats[v],
                "p_value": res.pvalues[v],
                "Significance": stars(res.pvalues[v]),
            }
        )

    stats = {
        "Observations": int(res.nobs),
        "ACs (entities)": int(res.entity_info.total),
        "Districts (clusters)": int(clusters.nunique()),
        "Years": int(res.time_info.total),
        "R-sq (within)": float(res.rsquared_within),
    }
    return pd.DataFrame(rows), stats


def main() -> None:
    df = pd.read_excel(DATA)
    df["DISTRICT_ID"] = df["ST_CODE"].astype(str) + "_" + df["DT_CODE"].astype(str)

    out_sheets: dict[str, pd.DataFrame] = {}
    stats_records: list[dict] = []

    for suffix in ["median", "mean"]:
        per_state_coef: dict[str, pd.DataFrame] = {}
        per_state_stats: dict[str, dict] = {}
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

        meta_rows = ["Observations", "ACs (entities)", "Districts (clusters)", "Years", "R-sq (within)"]
        for item in meta_rows:
            row: dict = {"Variable": item}
            for state_label in STATES:
                row[f"{state_label}_Coef"] = per_state_stats[state_label][item]
                row[f"{state_label}_SE"] = None
                row[f"{state_label}_Sig"] = None
            all_states = pd.concat([all_states, pd.DataFrame([row])], ignore_index=True)

        sheet_name = "Median_All_States" if suffix == "median" else "Mean_All_States"
        out_sheets[sheet_name] = all_states

        for state_label in STATES:
            sub_sheet = f"{state_label}_{'Median' if suffix == 'median' else 'Mean'}"
            out_sheets[sub_sheet] = per_state_coef[state_label]
            stats_records.append(
                {"Model": "Median" if suffix == "median" else "Mean", "State": state_label, **per_state_stats[state_label]}
            )

    stats_by_state: dict[str, list] = {}
    for s in stats_records:
        stats_by_state.setdefault(s["State"], []).append(s)
    for state_label, recs in stats_by_state.items():
        out_sheets[f"{state_label}_Stats"] = pd.DataFrame(recs)

    notes = pd.DataFrame(
        {
            "Note": [
                "Outcome: Delta log NL = log(NL_t) - log(NL_{t-1}) (year-on-year growth in night-light radiance).",
                "Lagged regressors: NDVI_{t-1}, NDBI_{t-1}. Seasonal_Ratio is contemporaneous.",
                "TWFE PanelOLS (linearmodels), AC + YEAR FE, SEs clustered by district (ST_CODE_DT_CODE).",
                "Estimated separately for each state. Significance: *** p<0.01, ** p<0.05, * p<0.10.",
                "Cross-check: same specification as run_nl_ols_by_state.py (pyfixest); coefficients should be close.",
            ]
        }
    )

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
