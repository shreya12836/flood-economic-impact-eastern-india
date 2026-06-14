import streamlit as st

from utils.charts import trend_chart
from utils.data_loader import load_panel

st.set_page_config(page_title="Overview", layout="wide")
st.header("Dataset Overview")

df = load_panel()
all_states = sorted(df["STATE"].unique().tolist())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Assembly Constituencies", df["AC_UID"].nunique())
col2.metric("States", df["STATE"].nunique())
col3.metric("Years", f"{int(df['YEAR'].min())}–{int(df['YEAR'].max())}")
col4.metric("District clusters", df["DIST_NAME"].nunique())

st.divider()

with st.sidebar:
    st.subheader("Controls")
    states = st.multiselect("States", all_states, default=all_states)
    agg = st.radio("Aggregation", ["Median", "Mean"]).lower()

if not states:
    st.warning("Select at least one state.")
    st.stop()

st.subheader("Variable trends by state and year")

_VARIABLES = [
    ("Night Lights (NL)", f"NL_{agg}"),
    ("Built-up Index (NDBI)", f"NDBI_{agg}"),
    ("Vegetation Index (NDVI)", f"NDVI_{agg}"),
    ("Flood Coverage (Seasonal Ratio)", "Seasonal_Ratio"),
]

row1_cols = st.columns(2)
row2_cols = st.columns(2)
grid = [row1_cols[0], row1_cols[1], row2_cols[0], row2_cols[1]]

for (title, col), container in zip(_VARIABLES, grid):
    fig = trend_chart(df, col, states)
    fig.update_layout(
        title=title,
        yaxis_title=col,
        margin=dict(t=40, b=30),
        height=300,
        legend=dict(orientation="h", y=-0.25),
    )
    container.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Summary statistics")
summary_cols = [
    "Seasonal_Ratio",
    f"NL_{agg}",
    f"NDBI_{agg}",
    f"NDVI_{agg}",
]
available = [c for c in summary_cols if c in df.columns]
st.dataframe(
    df[df["STATE"].isin(states)][available].describe().round(4),
    use_container_width=True,
)
