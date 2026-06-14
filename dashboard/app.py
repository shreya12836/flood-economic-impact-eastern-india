import streamlit as st

st.set_page_config(
    page_title="Flood & Economic Activity — Eastern India",
    page_icon="🌊",
    layout="wide",
)

st.title("Flood Impact on Economic Activity — Eastern India (2014–2019)")
st.markdown(
    """
    Panel econometric analysis of seasonal flood exposure on night-light growth and
    built-up index change across 765 Assembly Constituencies in Bihar, Jharkhand,
    Odisha, and West Bengal.

    **Navigate using the sidebar** to explore trends or regression results.
    """
)

st.info(
    "Use the pages in the sidebar: **Overview** · **Trend Explorer** · **Regression Results**"
)
