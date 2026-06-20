# Flood Exposure and Economic Activity in Eastern India

Panel regression analysis of how seasonal flood exposure affects economic activity and built-up infrastructure across Assembly Constituencies (ACs) in Bihar, Jharkhand, Odisha, and West Bengal, 2014–2019.

---

## Overview

This project estimates the causal effect of flood exposure on two outcomes:

- **Night-lights intensity** (Δlog NL): proxy for local economic activity
- **Built-up index change** (ΔNDBI): proxy for physical infrastructure

The identification strategy uses two-way fixed effects (TWFE) — AC fixed effects absorb time-invariant local characteristics; year fixed effects absorb common shocks. Standard errors are clustered at the district level.

---

## Data Sources

| Source | Variable | Resolution |
|---|---|---|
| JRC Global Surface Water (GSW) | Seasonal_Ratio, Permanent_Ratio | 30 m |
| VIIRS/DMSP Nighttime Lights | NL_mean, NL_median | ~500 m |
| Landsat-8 SR (OLI bands 4, 5, 6) | NDVI, NDBI | 30 m |
| Election Commission of India | AC boundaries (2008 delimitation) | Vector |

Raster data were aggregated to AC boundaries using QGIS zonal statistics. Processed CSV files are one row per AC per year.

---

## Regression Specifications

**Equation 1 — Night-lights (economic activity)**

```
Δlog(NL_it) = β₁ · Seasonal_Ratio_it + β₂ · NDVI_{i,t−1} + β₃ · NDBI_{i,t−1} + αᵢ + γₜ + εᵢₜ
```

Estimated via `pyfixest.feols`; SEs clustered by district.

**Equation 2 — NDBI (built-up infrastructure)**

```
ΔNDBI_it = β₀ + β₁ · Seasonal_Ratio_it + β₂ · NDVI_{i,t−1} + β₃ · NL_{i,t−1} + αᵢ + γₜ + εᵢₜ
```

Estimated via `linearmodels.PanelOLS`; SEs clustered by district.

NDBI is used in levels (not log) because it is bounded in [−1, 1] and frequently negative in rural constituencies.

---

## Key Findings

**West Bengal — Night-lights**
Higher flood exposure (Seasonal_Ratio) is associated with a statistically significant reduction in night-lights growth. The coefficient on Seasonal_Ratio ranges from −0.32 to −0.39 (p < 0.05) depending on the NL measure (mean vs. median). This implies that a one-unit increase in the seasonal flood water fraction is associated with a 32–39 percent reduction in economic activity growth.

![NL TWFE coefficients by state](outputs/figures/coef_NL_TWFE.png)

**Bihar — NDBI**
Flood exposure predicts a significant decline in built-up index growth in Bihar. The coefficient on Seasonal_Ratio is −0.02 to −0.03 (p < 0.01), suggesting flood-affected constituencies see slower infrastructure accumulation.

![NDBI TWFE coefficients by state](outputs/figures/coef_NDBI_TWFE.png)

**Pooled sample**
No statistically significant effect is detected in pooled regressions. The aggregate null masks heterogeneous state-level effects, consistent with variation in flood frequency, infrastructure quality, and institutional capacity across states.

![State-level coefficient comparison (OLS)](outputs/figures/forest_plot_flood_OLS.png)

---

## Panel Structure

- **Unit of observation:** Assembly Constituency (AC)
- **States:** Bihar, Jharkhand, Odisha, West Bengal
- **Raw panel:** 765 ACs × 6 years (2014–2019) = 4,674 observations
- **Estimation sample:** ~3,890 observations (2014 dropped for lag construction; a small number of ACs dropped due to missing satellite coverage)
- **Clusters:** 108 districts

---

## Repository Structure

```
flood-economic-impact-eastern-india/
├── data/
│   ├── processed/          # State-year AC-level CSVs + merged panel
│   └── README.md           # Column definitions and data provenance
├── src/
│   ├── regression/         # TWFE and OLS estimation scripts
│   └── visualization/      # Coefficient plots and trend figures
├── scripts/                # Paper-ready table builders
├── outputs/
│   ├── figures/            # PNG coefficient and trend plots
│   └── tables/             # Regression result Excel files
├── docs/
│   ├── methodology.md      # Estimation details and data cleaning decisions
│   ├── data_dictionary.md  # Variable definitions
│   └── roadmap.md          # Planned extensions
├── .github/workflows/      # CI: dependency install and syntax check
├── requirements.txt
└── README.md
```

---

## Limitations

- **Outcome proxy:** Night-lights measure commercial and industrial activity but miss subsistence agriculture, which is the dominant livelihood in flood-prone Bihar and Odisha constituencies.
- **Flood measure:** `Seasonal_Ratio` captures inundation extent from satellite imagery but not flood depth, duration, or damage severity. Two constituencies with the same ratio may experience very different economic disruption.
- **Parallel trends:** The TWFE estimator requires that treated and control ACs would have followed parallel outcome trends in the absence of flooding. This assumption is untestable and may be violated if flood-prone ACs are structurally different in ways that interact with the outcome trend.
- **Missing regressor:** Road density is not yet included in the model. If road access correlates with both flood exposure and economic recovery capacity, current estimates may carry omitted variable bias.
- **Estimation window:** 2014 is excluded from estimation for lag construction; results cover 2015–2019 only.
- **Pooled null:** The pooled null result is not evidence of no effect. It reflects cancellation across states with heterogeneous and opposite-sign effects, not a true zero treatment effect.
- **Spatial resolution mismatch:** VIIRS nighttime lights at ~500 m are considerably coarser than the 30 m Landsat and JRC GSW layers. Aggregation to AC-level averages partially mitigates this but introduces measurement error in the outcome variable.

---

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run regressions — night-lights outcome
python src/regression/run_nl_ols_pooled.py
python src/regression/run_nl_ols_by_state.py

# 3. Run regressions — NDBI outcome
python src/regression/run_ndbi_pooled.py
python src/regression/run_ndbi_by_state.py

# 4. Generate plots
python src/visualization/generate_ols_plots.py

# 5. Build paper tables
python scripts/build_paper_table.py
python scripts/build_paper_table_ndbi.py
```

All outputs are written to `outputs/figures/` and `outputs/tables/`.

---

## Requirements

Python 3.9+. See `requirements.txt` for package versions.
