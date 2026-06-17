from __future__ import annotations

import datetime

import streamlit as st

from config import (
    DATA_SOURCES,
    DEBUG_MODE,
    FINDING_FALLBACK_ICON,
    FINDINGS_SPECS,
    GEO_LAYERS,
    HERO_DYNAMIC_TAG_ICONS,
    HERO_TAGS,
    KEY_FINDINGS,
    KPI_ICONS,
    META_ICONS,
    METHODS_EXTRA,
    POOLED_NOTE,
    PROJECT_DESCRIPTION,
    PROJECT_TITLE,
    STATE_GEO_NAME_FIELD,
    STATE_NAME_MAP,
    TOOLS,
)
from utils.charts import _STATE_COLORS, state_boundary_map
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
    load_state_geojson,
)
from utils.theme import (
    accent_header,
    chip_row,
    finding_card,
    finding_missing_card,
    inject_bootstrap_icons,
    kpi_card,
    meta_card,
    pooled_note_card,
)

st.set_page_config(page_title="Overview", layout="wide")
inject_bootstrap_icons()

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
st.markdown(f"# {PROJECT_TITLE} ({year_range})")
_tags = [(t["icon"], t["label"]) for t in HERO_TAGS] + [
    (HERO_DYNAMIC_TAG_ICONS["constituencies"], f"{n_acs:,} Constituencies"),
    (HERO_DYNAMIC_TAG_ICONS["year_range"],     year_range),
]
st.markdown(chip_row(_tags), unsafe_allow_html=True)
st.markdown(PROJECT_DESCRIPTION)
st.divider()

# ── KPI row ───────────────────────────────────────────────────────────────────
_kpi = [
    (KPI_ICONS[0], n_acs,      "Assembly Constituencies"),
    (KPI_ICONS[1], n_states,   "States"),
    (KPI_ICONS[2], year_range, "Years Covered"),
    (KPI_ICONS[3], n_obs,      "Constituency-Year Observations"),
]
for _col, (_icon, _value, _label) in zip(st.columns(4), _kpi):
    _col.markdown(kpi_card(_icon, _value, _label), unsafe_allow_html=True)
st.divider()

# ── Study Area map (left) + Key Findings (right) ──────────────────────────────
map_col, find_col = st.columns([3, 2])

with map_col:
    st.markdown(accent_header("Study Area"), unsafe_allow_html=True)
    try:
        geojson   = load_state_geojson("state")
        ac_counts = df.groupby("STATE")["AC_UID"].nunique().to_dict()
        fig = state_boundary_map(
            geojson=geojson,
            state_colors=_STATE_COLORS,
            state_name_field=STATE_GEO_NAME_FIELD,
            state_name_map=STATE_NAME_MAP,
            ac_counts=ac_counts,
        )
        st.plotly_chart(fig, use_container_width=True)
    except FileNotFoundError as exc:
        st.warning(str(exc))

with find_col:
    st.markdown(accent_header("Key Findings"), unsafe_allow_html=True)

    any_loaded = False
    for finding in KEY_FINDINGS:
        result = load_state_finding(
            outcome=finding["outcome"],
            estimator=finding["estimator"],
            state_key=finding["state_key"],
            variable=finding["variable"],
        )

        if result is None:
            st.markdown(finding_missing_card(finding["label"]), unsafe_allow_html=True)
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
            sig      = median_r["sig"]
            coef_str = f"beta = {lo_coef:.2f} to {hi_coef:.2f}{median_r['stars']}"
        elif median_r:
            coef_str = f"beta = {median_r['coef']:.4f}{median_r['stars']}"
            sig      = median_r["sig"]
        else:
            continue

        st.markdown(
            finding_card(
                finding.get("icon", FINDING_FALLBACK_ICON),
                finding["label"],
                coef_str,
                sig,
                finding["interpretation"],
            ),
            unsafe_allow_html=True,
        )

    st.markdown(pooled_note_card(POOLED_NOTE), unsafe_allow_html=True)

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

for _col, (_header, _items) in zip(
    st.columns(4),
    [
        ("Methods",  estimators),
        ("Data",     DATA_SOURCES),
        ("Coverage", coverage),
        ("Tools",    TOOLS),
    ],
):
    _col.markdown(
        meta_card(META_ICONS.get(_header, "geo-alt"), _header, _items),
        unsafe_allow_html=True,
    )

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
