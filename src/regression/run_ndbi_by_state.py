"""By-state district-clustered TWFE regression with Delta NDBI as the outcome.

Same specification as run_ndbi_pooled.py, run separately on each of the 4 states.
Outputs Median_All_States and Mean_All_States summary sheets (one row per variable,
columns per state with Coef/SE/Sig), plus per-state coefficient sheets and a stats sheet.
"""
from pathlib import Path
import pandas as pd
from linearmodels.panel import PanelOLS

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data" / "processed" / "final_regression_dataset.xlsx"
OUT = REPO_ROOT / "outputs" / "tables" / "Regression_Results_NDBI_By_State.xlsx"

STATES = {
    "BIHAR": "Bihar",
    "JHARKHAND": "Jharkhand",
    "ORISSA": "Odisha",
    "WB": "WB",
}


def stars(p):
    if p < 0.01:
        return "p < 0.01"
    if p < 0.05:
        return "p < 0.05"
    if p < 0.10:
        return "p < 0.10"
    return "n.s."


def run_state(df_state, suffix):
    y = df_state[f"NDBI_{suffix}"] - df_state[f"NDBI_{suffix}_t_minus_1"]
    X = pd.DataFrame({
        "Seasonal_Ratio": df_state["Seasonal_Ratio"],
        f"NDVI_{suffix}_t_minus_1": df_state[f"NDVI_{suffix}_t_minus_1"],
        f"NL_{suffix}_t_minus_1": df_state[f"NL_{suffix}_t_minus_1"],
    }, index=df_state.index)
    X["const"] = 1.0

    panel = pd.concat([y.rename("delta_ndbi"), X, df_state[["AC_UID", "YEAR", "DISTRICT_ID"]]], axis=1).dropna()
    panel = panel.set_index(["AC_UID", "YEAR"])

    dep = panel["delta_ndbi"]
    regs = panel[["const", "Seasonal_Ratio", f"NDVI_{suffix}_t_minus_1", f"NL_{suffix}_t_minus_1"]]
    clusters = panel["DISTRICT_ID"]

    mod = PanelOLS(dep, regs, entity_effects=True, time_effects=True, drop_absorbed=True)
    res = mod.fit(cov_type="clustered", clusters=clusters)

    name_map = {
        "const": "beta_0 (Constant)",
        "Seasonal_Ratio": "Seasonal_Ratio",
        f"NDVI_{suffix}_t_minus_1": f"NDVI_{suffix}_t_minus_1",
        f"NL_{suffix}_t_minus_1": f"NL_{suffix}_t_minus_1",
    }
    rows = []
    for v in regs.columns:
        rows.append({
            "Variable": name_map[v],
            "Coefficient": res.params[v],
            "Std_Error": res.std_errors[v],
            "t_stat": res.tstats[v],
            "p_value": res.pvalues[v],
            "Significance": stars(res.pvalues[v]),
        })
    coef_df = pd.DataFrame(rows)

    n_districts = clusters.nunique()
    stats = {
        "Observations": int(res.nobs),
        "ACs (entities)": int(res.entity_info.total),
        "Districts (clusters)": n_districts,
        "Years": int(res.time_info.total),
        "R-sq (within)": float(res.rsquared_within),
    }
    return coef_df, stats


def main():
    df = pd.read_excel(DATA)
    df["DISTRICT_ID"] = df["ST_CODE"].astype(str) + "_" + df["DT_CODE"].astype(str)

    out_sheets = {}
    stats_records = []

    for suffix in ["median", "mean"]:
        # Per-state results
        per_state_coef = {}
        per_state_stats = {}
        for state_label, state_name in STATES.items():
            sub = df[df["STATE"] == state_name].copy()
            cdf, st = run_state(sub, suffix)
            per_state_coef[state_label] = cdf
            per_state_stats[state_label] = st

        # All-states summary sheet (one row per variable; columns per state)
        var_order = per_state_coef["BIHAR"]["Variable"].tolist()
        all_states = pd.DataFrame({"Variable": var_order})
        for state_label in STATES:
            cdf = per_state_coef[state_label].set_index("Variable")
            all_states[f"{state_label}_Coef"] = all_states["Variable"].map(cdf["Coefficient"])
            all_states[f"{state_label}_SE"] = all_states["Variable"].map(cdf["Std_Error"])
            all_states[f"{state_label}_Sig"] = all_states["Variable"].map(cdf["Significance"])

        # Append model-level rows (Obs / ACs / Districts / Years / R-sq)
        meta_rows = ["Observations", "ACs (entities)", "Districts (clusters)", "Years", "R-sq (within)"]
        for item in meta_rows:
            row = {"Variable": item}
            for state_label in STATES:
                row[f"{state_label}_Coef"] = per_state_stats[state_label][item]
                row[f"{state_label}_SE"] = None
                row[f"{state_label}_Sig"] = None
            all_states = pd.concat([all_states, pd.DataFrame([row])], ignore_index=True)

        sheet_name = "Median_All_States" if suffix == "median" else "Mean_All_States"
        out_sheets[sheet_name] = all_states

        # Per-state coefficient sheets and stats
        for state_label in STATES:
            sub_sheet = f"{state_label}_{'Median' if suffix == 'median' else 'Mean'}"
            out_sheets[sub_sheet] = per_state_coef[state_label]
            stats_records.append({
                "Model": "Median" if suffix == "median" else "Mean",
                "State": state_label,
                **per_state_stats[state_label],
            })

    # Build a per-state stats sheet keyed by state
    stats_by_state = {}
    for s in stats_records:
        key = s["State"]
        if key not in stats_by_state:
            stats_by_state[key] = []
        stats_by_state[key].append(s)
    for state_label, recs in stats_by_state.items():
        out_sheets[f"{state_label}_Stats"] = pd.DataFrame(recs)

    notes = pd.DataFrame({
        "Note": [
            "Outcome: Delta NDBI = NDBI_t - NDBI_{t-1} (level change).",
            "Lagged regressors: NDVI_{t-1}, NL_{t-1}. Seasonal_Ratio is contemporaneous.",
            "TWFE PanelOLS, AC + YEAR FE, SEs clustered by district (ST_CODE_DT_CODE).",
            "Estimated separately for each state. Significance: *** p<0.01, ** p<0.05, * p<0.10.",
        ]
    })

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
