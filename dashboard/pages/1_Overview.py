from pathlib import Path

import streamlit as st

from utils.data_loader import load_panel

REPO_ROOT = Path(__file__).resolve().parents[2]
FIGURES = REPO_ROOT / "outputs" / "figures"

st.set_page_config(page_title="Overview", layout="wide")
st.header("Dataset Overview")

df = load_panel()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Assembly Constituencies", df["AC_UID"].nunique())
col2.metric("States", df["STATE"].nunique())
col3.metric("Years", f"{int(df['YEAR'].min())}–{int(df['YEAR'].max())}")
col4.metric("District clusters", df["DIST_NAME"].nunique())

st.divider()

st.subheader("Variable trends across states (2014–2019)")
trend_img = FIGURES / "trend_grid_all_variables.png"
if trend_img.exists():
    st.image(str(trend_img), use_container_width=True)
else:
    st.warning(f"Figure not found: {trend_img}")

st.divider()

st.subheader("Summary statistics")
summary_cols = [
    "Seasonal_Ratio",
    "NL_median",
    "NL_mean",
    "NDBI_median",
    "NDBI_mean",
    "NDVI_median",
    "NDVI_mean",
]
available = [c for c in summary_cols if c in df.columns]
st.dataframe(
    df[available].describe().round(4),
    use_container_width=True,
)
