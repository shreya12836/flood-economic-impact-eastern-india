import pandas as pd
import streamlit as st

from utils.charts import forest_plot
from utils.data_loader import (
    STARS,
    discover_states,
    load_comparison_table,
    load_forest_data,
    load_pooled_table,
    load_spec_meta,
    load_state_table,
)

st.set_page_config(page_title="Regression Results", layout="wide")
st.header("Regression Results - Flood Exposure Coefficient")

_SPEC_OPTIONS = {
    "NL (night lights) - OLS, pyfixest [primary]":              ("NL",   "OLS"),
    "NDBI (built-up index) - OLS, pyfixest, LDV [primary]":    ("NDBI", "OLS"),
    "NL (night lights) - TWFE, linearmodels [cross-check]":     ("NL",   "TWFE"),
    "NDBI (built-up index) - TWFE, linearmodels [cross-check]": ("NDBI", "TWFE"),
}


def _format_coef_table(df: pd.DataFrame) -> pd.DataFrame:
    out = df[["Variable", "Coefficient", "Std_Error", "t_stat", "p_value", "Significance"]].copy()
    out["Significance"] = out["Significance"].map(
        lambda s: f"{s} {STARS.get(str(s).strip(), '')}".strip()
    )
    for col in ["Coefficient", "Std_Error", "t_stat"]:
        out[col] = out[col].round(4)
    out["p_value"] = out["p_value"].round(4)
    return out


with st.sidebar:
    st.subheader("Specification")
    spec_label = st.selectbox("Outcome & estimator", list(_SPEC_OPTIONS.keys()))
    variant = st.radio("Variable variant", ["Median", "Mean"])

outcome, estimator = _SPEC_OPTIONS[spec_label]

meta = load_spec_meta(outcome, estimator, variant)
if meta:
    with st.sidebar:
        st.caption(
            f"**Estimator:** {meta['estimator']}  \n"
            f"**SE:** {meta['se']}  \n"
            f"**N (pooled):** {meta['n_obs']}  \n"
            f"**R²:** {meta['r2']}"
        )

# Discover available states from the Excel files - no hardcoding needed
states = discover_states(outcome, estimator, variant)
state_display_names = [d for _, d in states]

with st.sidebar:
    st.subheader("Sample")
    state_option = st.selectbox(
        "View",
        ["All States (pooled)"] + state_display_names + ["Compare All States"],
    )

try:
    forest_rows = load_forest_data(outcome, estimator, variant)
except FileNotFoundError as e:
    st.error(f"Missing results file — {e}")
    st.stop()
except KeyError as e:
    st.error(f"Missing sheet in results file — {e}")
    st.stop()
except Exception as e:
    st.error(f"Could not load forest plot data: {e}")
    st.stop()

tab_forest, tab_detail = st.tabs(["Forest Plot", "Coefficient Detail"])

with tab_forest:
    title = f"Seasonal_Ratio coefficient ({spec_label}, {variant} model)"
    fig = forest_plot(forest_rows, title)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Error bars show 95% confidence intervals. "
        "Pooled uses exact CI from the regression table; "
        "state-level uses +/-1.96 x SE. SEs clustered by district."
    )

with tab_detail:
    if state_option == "All States (pooled)":
        try:
            tbl = load_pooled_table(outcome, estimator, variant)
        except (FileNotFoundError, KeyError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Could not load pooled table: {e}")
        else:
            st.subheader(f"Pooled - {spec_label}, {variant}")
            st.dataframe(_format_coef_table(tbl), use_container_width=True, hide_index=True)

    elif state_option == "Compare All States":
        try:
            coef_df, stats_df = load_comparison_table(outcome, estimator, variant)
        except (FileNotFoundError, KeyError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Could not load comparison table: {e}")
        else:
            st.subheader(f"All states side-by-side - {spec_label}, {variant}")
            st.caption(
                "Each cell shows the coefficient with significance stars "
                "(*** p<0.01, ** p<0.05, * p<0.10)."
            )
            st.dataframe(coef_df, use_container_width=True, hide_index=True)
            with st.expander("Model statistics (Observations, R-sq, etc.)"):
                st.dataframe(stats_df, use_container_width=True, hide_index=True)

    else:
        state_key = next(k for k, d in states if d == state_option)
        try:
            tbl = load_state_table(outcome, estimator, variant, state_key)
        except (FileNotFoundError, KeyError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Could not load {state_option} table: {e}")
        else:
            st.subheader(f"{state_option} - {spec_label}, {variant}")
            st.dataframe(_format_coef_table(tbl), use_container_width=True, hide_index=True)

st.divider()
with st.expander("Specification notes"):
    if outcome == "NL" and estimator == "OLS":
        st.markdown(
            """
            **Dependent variable:** Delta log(NL) - year-on-year growth in night-light radiance.
            **Estimator:** pyfixest.feols - AC + year fixed effects (primary estimator per dissertation).
            **Standard errors:** Clustered by district (108 clusters pooled; 19-37 by state).
            """
        )
    elif outcome == "NDBI" and estimator == "OLS":
        st.markdown(
            """
            **Dependent variable:** NDBI_t (level), with lagged NDBI on RHS (LDV specification).
            **Estimator:** pyfixest.feols - AC + year fixed effects (primary estimator per dissertation).
            **Nickell bias caveat:** With T ~ 5, the lagged-DV coefficient has ~20% downward bias.
            The flood coefficient (beta_1) is far less affected.
            **Standard errors:** Clustered by district (108 clusters pooled; 19-37 by state).
            """
        )
    elif outcome == "NL" and estimator == "TWFE":
        st.markdown(
            """
            **Dependent variable:** Delta log(NL) - year-on-year growth in night-light radiance.
            **Estimator:** linearmodels PanelOLS - two-way FE (cross-check of pyfixest primary).
            **Standard errors:** Clustered by district.
            """
        )
    else:
        st.markdown(
            """
            **Dependent variable:** NDBI_t (level), with lagged NDBI on RHS (LDV specification).
            **Estimator:** linearmodels PanelOLS - two-way FE (cross-check of pyfixest primary).
            **Nickell bias caveat:** With T ~ 5, the lagged-DV coefficient has ~20% downward bias.
            The flood coefficient (beta_1) is far less affected.
            **Standard errors:** Clustered by district.
            """
        )
