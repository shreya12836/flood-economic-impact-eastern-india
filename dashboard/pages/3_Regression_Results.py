import pandas as pd
import streamlit as st

from utils.charts import forest_plot
from utils.data_loader import load_forest_data

st.set_page_config(page_title="Regression Results", layout="wide")
st.header("Regression Results — Flood Exposure Coefficient")

_SPEC_OPTIONS = {
    "NL (night lights) — OLS, pyfixest [primary]":              ("NL",   "OLS"),
    "NDBI (built-up index) — OLS, pyfixest, LDV [primary]":    ("NDBI", "OLS"),
    "NL (night lights) — TWFE, linearmodels [cross-check]":     ("NL",   "TWFE"),
    "NDBI (built-up index) — TWFE, linearmodels [cross-check]": ("NDBI", "TWFE"),
}

_SIG_STARS = {
    "p < 0.01": "***",
    "p < 0.05": "**",
    "p < 0.10": "*",
    "n.s.": "",
}

with st.sidebar:
    st.subheader("Specification")
    spec_label = st.selectbox("Outcome & estimator", list(_SPEC_OPTIONS.keys()))
    variant = st.radio("Variable variant", ["Median", "Mean"])

outcome, estimator = _SPEC_OPTIONS[spec_label]

try:
    rows = load_forest_data(outcome, estimator, variant)
except Exception as e:
    st.error(f"Could not load results: {e}")
    st.stop()

title = f"Seasonal_Ratio coefficient ({spec_label}, {variant} model)"
fig = forest_plot(rows, title)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Error bars show 95% confidence intervals. "
    "Pooled uses exact CI from the regression table; state-level uses ±1.96 × SE. "
    "SEs clustered by district."
)

st.divider()
st.subheader("Coefficient table")

tbl_rows = []
for r in rows:
    stars = _SIG_STARS.get(str(r["sig"]).strip(), "")
    tbl_rows.append(
        {
            "Specification": r["label"],
            "β (Seasonal_Ratio)": round(r["coef"], 4),
            "95% CI low": round(r["ci_low"], 4),
            "95% CI high": round(r["ci_high"], 4),
            "Significance": f"{r['sig']} {stars}".strip(),
        }
    )

st.dataframe(pd.DataFrame(tbl_rows), use_container_width=True, hide_index=True)

with st.expander("Specification notes"):
    if outcome == "NL" and estimator == "OLS":
        st.markdown(
            """
            **Dependent variable:** Δlog(NL) — year-on-year growth in night-light radiance.
            **Estimator:** pyfixest.feols — AC + year fixed effects (primary estimator per dissertation).
            **Standard errors:** Clustered by district (108 clusters pooled; 19–37 by state).
            """
        )
    elif outcome == "NDBI" and estimator == "OLS":
        st.markdown(
            """
            **Dependent variable:** NDBI_t (level), with lagged NDBI on RHS (LDV specification).
            **Estimator:** pyfixest.feols — AC + year fixed effects (primary estimator per dissertation).
            **Nickell bias caveat:** With T ≈ 5, the lagged-DV coefficient has ~20% downward bias.
            The flood coefficient (β₁) is far less affected.
            **Standard errors:** Clustered by district (108 clusters pooled; 19–37 by state).
            """
        )
    elif outcome == "NL" and estimator == "TWFE":
        st.markdown(
            """
            **Dependent variable:** Δlog(NL) — year-on-year growth in night-light radiance.
            **Estimator:** linearmodels PanelOLS — two-way FE (cross-check of pyfixest primary).
            **Standard errors:** Clustered by district.
            """
        )
    else:
        st.markdown(
            """
            **Dependent variable:** NDBI_t (level), with lagged NDBI on RHS (LDV specification).
            **Estimator:** linearmodels PanelOLS — two-way FE (cross-check of pyfixest primary).
            **Nickell bias caveat:** With T ≈ 5, the lagged-DV coefficient has ~20% downward bias.
            The flood coefficient (β₁) is far less affected.
            **Standard errors:** Clustered by district.
            """
        )
