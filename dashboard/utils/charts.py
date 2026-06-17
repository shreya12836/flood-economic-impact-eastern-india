from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_STATE_COLORS = {
    "Bihar": "#636EFA",
    "Jharkhand": "#EF553B",
    "Odisha": "#00CC96",
    "WB": "#AB63FA",
    "West Bengal": "#AB63FA",
}

_SIG_LABELS = {
    "p < 0.01": "***",
    "p < 0.05": "**",
    "p < 0.10": "*",
    "n.s.": "",
}


def trend_chart(
    df: pd.DataFrame,
    col: str,
    states: list[str],
) -> go.Figure:
    subset = df[df["STATE"].isin(states)] if states else df
    grouped = subset.groupby(["STATE", "YEAR"])[col].mean().reset_index()

    fig = go.Figure()
    for state in grouped["STATE"].unique():
        sdf = grouped[grouped["STATE"] == state]
        fig.add_trace(
            go.Scatter(
                x=sdf["YEAR"],
                y=sdf[col],
                mode="lines+markers",
                name=state,
                line=dict(color=_STATE_COLORS.get(state)),
            )
        )

    fig.update_layout(
        xaxis_title="Year",
        yaxis_title=col,
        legend_title="State",
        hovermode="x unified",
        margin=dict(t=20, b=40),
    )
    return fig


def state_boundary_map(
    geojson: dict,
    state_colors: dict[str, str],
    state_name_field: str,
    state_name_map: dict[str, str],
    ac_counts: dict[str, int],
) -> go.Figure:
    fig = go.Figure()
    shown: set[str] = set()

    for feature in geojson["features"]:
        geo_name = feature["properties"][state_name_field]
        panel_key = next(
            (k for k, v in state_name_map.items() if v == geo_name), geo_name
        )
        color = state_colors.get(panel_key, "#888888")
        n = ac_counts.get(panel_key, "—")

        geom = feature["geometry"]
        rings = (
            [geom["coordinates"][0]]
            if geom["type"] == "Polygon"
            else [poly[0] for poly in geom["coordinates"]]
        )

        for ring in rings:
            lons, lats = zip(*ring)
            fig.add_trace(
                go.Scattergeo(
                    lon=list(lons),
                    lat=list(lats),
                    fill="toself",
                    fillcolor=color,
                    line=dict(color="rgba(255,255,255,0.25)", width=0.8),
                    mode="lines",
                    name=geo_name,
                    showlegend=(geo_name not in shown),
                    legendgroup=geo_name,
                    hovertemplate=(
                        f"<b>{geo_name}</b><br>"
                        f"Constituencies: {n}<extra></extra>"
                    ),
                )
            )
            shown.add(geo_name)

    fig.update_geos(
        scope="asia",
        showland=True,      landcolor="#1e2130",
        showocean=True,     oceancolor="#0e1117",
        showcountries=True, countrycolor="#555555",
        showsubunits=True,  subunitcolor="#333333",
        center=dict(lon=85, lat=23),
        projection_scale=7,
        bgcolor="#0e1117",
    )
    fig.update_layout(
        height=320,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#0e1117",
        geo_bgcolor="#0e1117",
        legend=dict(font=dict(color="#ccc", size=11), bgcolor="rgba(0,0,0,0)"),
        showlegend=True,
        hovermode="closest",
    )
    return fig


def forest_plot(rows: list[dict], title: str) -> go.Figure:
    labels = [r["label"] for r in rows]
    coefs = [r["coef"] for r in rows]
    ci_lows = [r["ci_low"] for r in rows]
    ci_highs = [r["ci_high"] for r in rows]
    sigs = [_SIG_LABELS.get(str(r["sig"]).strip(), "") for r in rows]
    colors = ["#2C3E50" if r["is_pooled"] else "#2980B9" for r in rows]

    error_minus = [c - l for c, l in zip(coefs, ci_lows)]
    error_plus = [h - c for c, h in zip(coefs, ci_highs)]

    fig = go.Figure()

    fig.add_vline(x=0, line_dash="dash", line_color="grey", line_width=1)

    fig.add_trace(
        go.Scatter(
            x=coefs,
            y=labels,
            mode="markers",
            marker=dict(color=colors, size=10, symbol="square"),
            error_x=dict(
                type="data",
                symmetric=False,
                array=error_plus,
                arrayminus=error_minus,
                color="#555",
                thickness=1.5,
                width=6,
            ),
            text=[f"{c:.3f}{s}" for c, s in zip(coefs, sigs)],
            hovertemplate="%{y}<br>β = %{text}<br>95% CI: [%{customdata[0]:.3f}, %{customdata[1]:.3f}]<extra></extra>",
            customdata=list(zip(ci_lows, ci_highs)),
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="Coefficient on Seasonal_Ratio (flood coverage)",
        yaxis=dict(autorange="reversed"),
        margin=dict(t=50, b=40, l=160),
        height=320,
    )
    return fig
