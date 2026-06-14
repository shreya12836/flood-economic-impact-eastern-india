import streamlit as st

from utils.charts import trend_chart
from utils.data_loader import load_panel

st.set_page_config(page_title="Trend Explorer", layout="wide")
st.header("Trend Explorer")

df = load_panel()
all_states = sorted(df["STATE"].unique().tolist())

_VARIABLE_MAP = {
    "Night lights — NL (median)": "NL_median",
    "Night lights — NL (mean)": "NL_mean",
    "Built-up index — NDBI (median)": "NDBI_median",
    "Built-up index — NDBI (mean)": "NDBI_mean",
    "Vegetation — NDVI (median)": "NDVI_median",
    "Vegetation — NDVI (mean)": "NDVI_mean",
    "Flood coverage — Seasonal Ratio": "Seasonal_Ratio",
}

with st.sidebar:
    st.subheader("Controls")
    outcome_label = st.selectbox("Outcome variable", list(_VARIABLE_MAP.keys()))
    states = st.multiselect("States", all_states, default=all_states)

col = _VARIABLE_MAP[outcome_label]

if not states:
    st.warning("Select at least one state.")
else:
    fig = trend_chart(df, col, states)
    fig.update_layout(yaxis_title=outcome_label)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("State-year averages (raw data)"):
        subset = df[df["STATE"].isin(states)]
        tbl = subset.groupby(["STATE", "YEAR"])[col].mean().round(4).reset_index()
        tbl.columns = ["State", "Year", outcome_label]
        st.dataframe(tbl, use_container_width=True)
