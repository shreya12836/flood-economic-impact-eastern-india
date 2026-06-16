from __future__ import annotations

import datetime

import plotly.graph_objects as go
import streamlit as st

from config import (
    DATA_SOURCES,
    DEBUG_MODE,
    FINDINGS_SPECS,
    KEY_FINDINGS,
    METHODS_EXTRA,
    POOLED_NOTE,
    PROJECT_DESCRIPTION,
    PROJECT_SUBTITLE,
    PROJECT_TITLE,
    STATE_CENTROIDS,
    TOOLS,
)
from utils.charts import _STATE_COLORS
from utils.data_loader import (
    DATA,
    STARS,
    TABLES,
    _POOLED_FILES,
    discover_outcomes,
    load_forest_data,
    load_overview_findings,
    load_panel,
    load_robustness_summary,
    load_spec_meta,
    load_state_finding,
)

st.set_page_config(page_title="Overview", layout="wide")

# ── Data ──────────────────────────────────────────────────────────────────────
df = load_panel()
n_acs        = df["AC_UID"].nunique()
n_states     = df["STATE"].nunique()
year_range   = f"{int(df['YEAR'].min())}–{int(df['YEAR'].max())}"
_primary     = FINDINGS_SPECS[0]
_meta        = load_spec_meta(_primary["outcome"], _primary["estimator"], _primary["variant"])
n_obs        = _meta.get("n_obs", f"{len(df):,}")
panel_states = sorted(df["STATE"].unique())
load_ts      = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ── Hero ──────────────────────────────────────────────────────────────────────
st.title(PROJECT_TITLE)
st.caption(f"{PROJECT_SUBTITLE} · {n_states} States · {year_range}")
st.markdown(PROJECT_DESCRIPTION)
st.divider()

# ── KPI row ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Assembly Constituencies", n_acs)
c2.metric("States", n_states)
c3.metric("Years Covered", year_range)
c4.metric("Constituency-Year Observations", n_obs)
st.divider()

# ── Study Area map (left) + Key Findings (right) ──────────────────────────────
_INDIA_FALLBACK = (82.0, 22.0)

map_col, find_col = st.columns([3, 2])

with map_col:
    st.subheader("Study Area")
    lons   = [STATE_CENTROIDS.get(s, _INDIA_FALLBACK)[0] for s in panel_states]
    lats   = [STATE_CENTROIDS.get(s, _INDIA_FALLBACK)[1] for s in panel_states]
    colors = [_STATE_COLORS.get(s, "#888888") for s in panel_states]

    fig = go.Figure(
        go.Scattergeo(
            lon=lons,
            lat=lats,
            text=panel_states,
            mode="markers+text",
            marker=dict(size=22, color=colors, opacity=0.85),
            textposition="bottom center",
            textfont=dict(color="white", size=11),
        )
    )
    fig.update_geos(
        scope="asia",
        showland=True,       landcolor="#1e2130",
        showocean=True,      oceancolor="#0e1117",
        showcountries=True,  countrycolor="#555555",
        showsubunits=True,   subunitcolor="#333333",
        center=dict(lon=85, lat=23),
        projection_scale=7,
        bgcolor="#0e1117",
    )
    fig.update_layout(
        height=320,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#0e1117",
        geo_bgcolor="#0e1117",
    )
    st.plotly_chart(fig, use_container_width=True)

with find_col:
    st.subheader("Key Findings")

    any_loaded = False
    for finding in KEY_FINDINGS:
        result = load_state_finding(
            outcome=finding["outcome"],
            estimator=finding["estimator"],
            state_key=finding["state_key"],
            variable=finding["variable"],
        )

        if result is None:
            st.caption(f"_{finding['label']}: data not found — run pipeline first._")
            continue

        any_loaded = True

        median_r = result.get("Median")
        mean_r   = result.get("Mean")

        if median_r and mean_r:
            # Range from less extreme to more extreme (by absolute value)
            if abs(median_r["coef"]) <= abs(mean_r["coef"]):
                lo_coef, hi_coef = median_r["coef"], mean_r["coef"]
            else:
                lo_coef, hi_coef = mean_r["coef"], median_r["coef"]
            stars    = median_r["stars"]
            sig      = median_r["sig"]
            coef_str = f"β = {lo_coef:.2f} to {hi_coef:.2f}{stars}"
        elif median_r:
            coef_str = f"β = {median_r['coef']:.4f}{median_r['stars']}"
            sig      = median_r["sig"]
        else:
            continue

        st.markdown(f"**{finding['label']}**")
        st.markdown(f"{coef_str} · {sig}")
        st.markdown(finding["interpretation"])
        st.markdown("---")

    # Pooled note always shown at the bottom
    st.markdown("**Pooled Sample**")
    st.caption(POOLED_NOTE)

    if not any_loaded:
        st.info("Run the regression pipeline to populate findings.")

st.divider()

# ── Project Metadata row ──────────────────────────────────────────────────────
outcomes   = discover_outcomes()
estimators = sorted({est for _, est in _POOLED_FILES}) + METHODS_EXTRA
est_range  = f"{int(df['YEAR'].min()) + 1}–{int(df['YEAR'].max())}"
coverage   = [
    f"{n_states} states",
    f"{n_acs} assembly constituencies",
    f"Data Coverage: {year_range}",
    f"Estimation Window: {est_range}",
    f"{len(outcomes)} outcome variable(s): {', '.join(outcomes)}",
]

m1, m2, m3, m4 = st.columns(4)
for col, header, items in [
    (m1, "Methods",  estimators),
    (m2, "Data",     DATA_SOURCES),
    (m3, "Coverage", coverage),
    (m4, "Tools",    TOOLS),
]:
    col.markdown(f"**{header}**")
    for item in items:
        col.markdown(f"· {item}")

st.divider()

# ── Summary statistics (collapsible) ─────────────────────────────────────────
with st.expander("Summary statistics (all states)"):
    _ID_COLS = {
        "AC_UID", "STATE", "YEAR", "DIST_NAME", "PANEL_ID", "OBJECTID",
        "UNIT_ID", "ST_CODE", "ST_NAME", "DT_CODE", "AC_NAME", "PC_NO",
        "PC_NAME", "PC_ID", "STATUS", "AC_NO",
    }
    summary_cols = [c for c in df.columns if c not in _ID_COLS]
    st.dataframe(df[summary_cols].describe().round(4), use_container_width=True)

# ── Debug panel (hidden by default) ──────────────────────────────────────────
if DEBUG_MODE:
    with st.expander("Debug diagnostics", expanded=True):
        st.markdown("**Data file paths**")
        st.code(str(DATA))
        st.code(str(TABLES))

        st.markdown("**Panel data**")
        st.write({
            "rows":    len(df),
            "states":  panel_states,
            "years":   sorted(df["YEAR"].unique().tolist()),
            "columns": len(df.columns),
        })

        st.markdown("**Active findings specs**")
        for spec in FINDINGS_SPECS:
            fname = _POOLED_FILES.get((spec["outcome"], spec["estimator"]), "NOT IN _POOLED_FILES")
            fpath = TABLES / fname if fname != "NOT IN _POOLED_FILES" else None
            st.write({
                **spec,
                "file":        fname,
                "file_exists": fpath.exists() if fpath else False,
            })

        st.caption(f"Page loaded at: {load_ts}")
