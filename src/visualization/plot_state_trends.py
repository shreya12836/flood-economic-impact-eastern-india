"""State-year trend plots for descriptive figures.

For each variable, two panels:
  - 'mean'   panel: state-year MEAN across ACs of the *_mean column
  - 'median' panel: state-year MEDIAN across ACs of the *_median column
For Seasonal_Ratio (single column): mean across ACs / median across ACs.
"""
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data" / "processed" / "final_regression_dataset.xlsx"
OUTDIR = REPO_ROOT / "outputs" / "figures"
os.makedirs(OUTDIR, exist_ok=True)

STATE_ORDER = ["Bihar", "Jharkhand", "Odisha", "WB"]
STATE_LABELS = {"Bihar": "Bihar", "Jharkhand": "Jharkhand", "Odisha": "Odisha", "WB": "West Bengal"}
STATE_COLORS = {
    "Bihar":     "#1f77b4",
    "Jharkhand": "#d62728",
    "Odisha":    "#2ca02c",
    "WB":        "#ff7f0e",
}

VARIABLES = [
    {"key": "NL",            "label": "Night Lights (NL)"},
    {"key": "NDBI",          "label": "NDBI"},
    {"key": "NDVI",          "label": "NDVI"},
    {"key": "Seasonal_Ratio","label": "Seasonal Flood Ratio"},
]


def get_series(df, var_key, agg):
    """Return DataFrame indexed by YEAR, columns = states, values = aggregate."""
    if var_key == "Seasonal_Ratio":
        col = "Seasonal_Ratio"
        op = "mean" if agg == "mean" else "median"
    else:
        col = f"{var_key}_{'mean' if agg == 'mean' else 'median'}"
        op = "mean" if agg == "mean" else "median"

    g = df.groupby(["STATE", "YEAR"])[col].agg(op).reset_index()
    pivot = g.pivot(index="YEAR", columns="STATE", values=col)
    return pivot[[s for s in STATE_ORDER if s in pivot.columns]]


def plot_panel(ax, pivot, title, ylabel):
    for state in pivot.columns:
        ax.plot(
            pivot.index, pivot[state],
            marker="o", linewidth=2, markersize=5,
            color=STATE_COLORS[state], label=STATE_LABELS[state],
        )
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(sorted(pivot.index.unique()))


def main():
    df = pd.read_excel(DATA)

    # individual PNGs
    for v in VARIABLES:
        for agg in ["mean", "median"]:
            pivot = get_series(df, v["key"], agg)
            fig, ax = plt.subplots(figsize=(7, 4.5))
            plot_panel(ax, pivot, f"{v['label']} — state-year {agg}", f"{agg.capitalize()} of {v['label']}")
            ax.legend(title="State", loc="best", framealpha=0.9)
            fig.tight_layout()
            out = os.path.join(OUTDIR, f"trend_{v['key']}_{agg}.png")
            fig.savefig(out, dpi=200)
            plt.close(fig)
            print(f"Saved: {out}")

    # combined 4x2 grid
    fig, axes = plt.subplots(4, 2, figsize=(13, 16))
    for i, v in enumerate(VARIABLES):
        for j, agg in enumerate(["mean", "median"]):
            pivot = get_series(df, v["key"], agg)
            plot_panel(axes[i, j], pivot, f"{v['label']} — {agg}", f"{agg.capitalize()}")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, title="State",
               bbox_to_anchor=(0.5, -0.01), frameon=True)
    fig.suptitle("State-year trends, 2014–2019 (AC-level aggregation)", fontsize=14, fontweight="bold", y=1.00)
    fig.tight_layout(rect=[0, 0.02, 1, 0.99])
    out = os.path.join(OUTDIR, "trend_grid_all_variables.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
