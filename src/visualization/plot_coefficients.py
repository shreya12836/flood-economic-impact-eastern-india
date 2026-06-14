"""Coefficient plots for the flood regressor (Seasonal_Ratio).

Four figures, one per (outcome × estimator):
  1. Delta log NL  - TWFE
  2. Delta log NL  - OLS
  3. Delta NDBI    - TWFE
  4. Delta NDBI    - OLS

Each figure: 5 rows (Bihar, Jharkhand, Odisha, West Bengal, All states pooled),
Median and Mean model shown as two markers with 95% CIs (beta +/- 1.96*SE).
"""
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = REPO_ROOT / "outputs" / "tables"
OUTDIR = REPO_ROOT / "outputs" / "figures"
os.makedirs(OUTDIR, exist_ok=True)

CONFIG = [
    {
        "key": "NL_TWFE",
        "title": "Flood coefficient on Δlog NL — TWFE (AC + year FE, district-clustered SE)",
        "pooled": "Regression_Results_Pooled.xlsx",
        "bystate": "Regression_Results_By_State.xlsx",
        "xlabel": "β₁ (Seasonal_Ratio) on Δlog NL",
    },
    {
        "key": "NL_OLS",
        "title": "Flood coefficient on Δlog NL — Pooled OLS (district-clustered SE)",
        "pooled": "Regression_Results_NL_OLS_Pooled.xlsx",
        "bystate": "Regression_Results_NL_OLS_By_State.xlsx",
        "xlabel": "β₁ (Seasonal_Ratio) on Δlog NL",
    },
    {
        "key": "NDBI_TWFE",
        "title": "Flood coefficient on Δ NDBI — TWFE (AC + year FE, district-clustered SE)",
        "pooled": "Regression_Results_NDBI_Pooled_DistrictCluster.xlsx",
        "bystate": "Regression_Results_NDBI_By_State.xlsx",
        "xlabel": "β₁ (Seasonal_Ratio) on Δ NDBI",
    },
    {
        "key": "NDBI_OLS",
        "title": "Flood coefficient on Δ NDBI — Pooled OLS (district-clustered SE)",
        "pooled": "Regression_Results_NDBI_OLS_Pooled.xlsx",
        "bystate": "Regression_Results_NDBI_OLS_By_State.xlsx",
        "xlabel": "β₁ (Seasonal_Ratio) on Δ NDBI",
    },
]

STATE_LABELS = [
    ("BIHAR", "Bihar"),
    ("JHARKHAND", "Jharkhand"),
    ("ORISSA", "Odisha"),
    ("WB", "West Bengal"),
]

MODEL_STYLE = {
    "Median": {"color": "#1f77b4", "marker": "o"},
    "Mean":   {"color": "#d62728", "marker": "s"},
}


def get_pooled(path, model):
    """Return (beta, se) for Seasonal_Ratio from the pooled file."""
    coef = pd.read_excel(path, sheet_name=f"{model}_Coef")
    r = coef[coef["Variable"] == "Seasonal_Ratio"].iloc[0]
    return float(r["Coefficient"]), float(r["Std_Error"])


def get_bystate(path, model):
    """Return dict {STATE_KEY: (beta, se)} for Seasonal_Ratio."""
    sheet = f"{model}_All_States"
    df = pd.read_excel(path, sheet_name=sheet)
    r = df[df["Variable"] == "Seasonal_Ratio"].iloc[0]
    out = {}
    for key, _ in STATE_LABELS:
        out[key] = (float(r[f"{key}_Coef"]), float(r[f"{key}_SE"]))
    return out


def build_rows(cfg):
    """Returns list of dicts: row label, beta_med, se_med, beta_mean, se_mean."""
    pooled_path = os.path.join(BASE, cfg["pooled"])
    bystate_path = os.path.join(BASE, cfg["bystate"])

    bs_med = get_bystate(bystate_path, "Median")
    bs_mean = get_bystate(bystate_path, "Mean")
    p_med = get_pooled(pooled_path, "Median")
    p_mean = get_pooled(pooled_path, "Mean")

    rows = []
    for key, label in STATE_LABELS:
        rows.append({
            "label": label,
            "Median": bs_med[key],
            "Mean": bs_mean[key],
        })
    rows.append({
        "label": "All states (pooled)",
        "Median": p_med,
        "Mean": p_mean,
    })
    return rows


def plot_one(cfg):
    rows = build_rows(cfg)
    n = len(rows)
    fig, ax = plt.subplots(figsize=(8.5, 5.5))

    y_positions = list(range(n, 0, -1))  # top-to-bottom: Bihar at top
    offset = 0.18

    for i, row in enumerate(rows):
        y = y_positions[i]
        for k, model in enumerate(["Median", "Mean"]):
            beta, se = row[model]
            lo, hi = beta - 1.96 * se, beta + 1.96 * se
            yy = y + (offset if model == "Median" else -offset)
            style = MODEL_STYLE[model]
            ax.errorbar(
                beta, yy,
                xerr=[[beta - lo], [hi - beta]],
                fmt=style["marker"],
                color=style["color"],
                ecolor=style["color"],
                elinewidth=1.4,
                capsize=4,
                markersize=7,
                label=f"{model} model" if i == 0 else None,
            )

    ax.axvline(0, color="black", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_yticks(y_positions)
    ax.set_yticklabels([r["label"] for r in rows])
    ax.axhline(1.5, color="grey", linestyle=":", linewidth=0.8, alpha=0.6)
    ax.set_xlabel(cfg["xlabel"])
    ax.set_title(cfg["title"], fontsize=11, fontweight="bold")
    ax.grid(True, axis="x", alpha=0.3)
    ax.legend(loc="best", framealpha=0.9)
    fig.tight_layout()

    out = os.path.join(OUTDIR, f"coef_{cfg['key']}.png")
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"Saved: {out}")


def main():
    for cfg in CONFIG:
        plot_one(cfg)


if __name__ == "__main__":
    main()
