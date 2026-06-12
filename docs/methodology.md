# Methodology

## Panel structure

- **Unit of observation:** Assembly Constituency (AC)
- **States:** Bihar, Jharkhand, Odisha, West Bengal
- **Raw panel:** 779 ACs × 6 years (2014–2019) = 4,674 rows; balanced
- **Estimation sample:** ~3,890 observations after dropping 2014 (no t−1 covariates available) and absorbing one AC via fixed effects
- **Entity key:** `AC_UID` = `ST_CODE_AC_NO`
- **Clustering variable:** `DISTRICT_ID` = `ST_CODE_DT_CODE`; 108 district clusters in pooled regressions

### State-level sample sizes (estimation sample)

| State | Obs | ACs | District clusters |
|---|---:|---:|---:|
| Bihar | 1,215 | 243 | 37 |
| Jharkhand | 475 | 95 | 22 |
| Odisha | 735 | 147 | 30 |
| West Bengal | 1,465 | 293 | 19 |

---

## Data cleaning decisions

**LC_SUM fill (2014):** The 2014 raw files are missing `LC_SUM` for some rows. These were reconstructed by summing raw land cover pixel counts (`LC_*` columns). All `LC_X_ratio` and water ratio columns were then recomputed for consistency.

**2014 drop from estimation:** Year 2014 is present in the panel solely to construct t−1 lag columns. It is excluded from all regressions because `NL_{t-1}` (i.e., 2013 values) is not available.

**Area approximation:** Bihar, Odisha, and West Bengal source files do not include `Area_AC`. It is approximated from `Shape_Area` (degrees²) using a latitude cosine correction at state-mean latitude. Validation on Jharkhand (where true area is available) gives median error 0.76%. This approximated area is stored separately in `data/processed/Area_AC_calculated.csv` and is not used in the regression specifications.

**WB 2015 filename:** The file `WestBengalFloods_2015_processed.csv` has a trailing space in the filename (`WestBengalFloods_2015 _processed.csv`). This is a source artefact; load it with the exact filename including the space, or rename before processing.

---

## Regression specifications

### Equation 1 — Night-lights (economic activity)

```
Δlog(NL_it) = β₁ · Seasonal_Ratio_it
             + β₂ · NDVI_{i,t−1}
             + β₃ · NDBI_{i,t−1}
             + αᵢ + γₜ + εᵢₜ
```

- Outcome: first-differenced log nighttime lights (`log NL_t − log NL_{t−1}`)
- Estimator: `pyfixest.feols` with `| AC_UID + YEAR` absorbing both fixed effects
- Standard errors: clustered by `DISTRICT_ID` (district-level clustering)

Two variants estimated: **Median** (uses `NL_median`, `NDVI_median_t_minus_1`, `NDBI_median_t_minus_1`) and **Mean** (uses `_mean_` analogues).

### Equation 2 — NDBI (built-up infrastructure)

```
ΔNDBI_it = β₀ + β₁ · Seasonal_Ratio_it
          + β₂ · NDVI_{i,t−1}
          + β₃ · NL_{i,t−1}
          + αᵢ + γₜ + εᵢₜ
```

- Outcome: first-differenced NDBI in levels (`NDBI_t − NDBI_{t−1}`)
- Estimator: `linearmodels.PanelOLS` with `entity_effects=True, time_effects=True, drop_absorbed=True`
- Standard errors: clustered by `DISTRICT_ID`

NDBI is used in level differences (not log) because it is bounded in [−1, 1] and frequently negative in rural ACs. Log-transforming NDBI would drop most of the rural sample and introduce severe outliers near zero.

---

## Why TWFE

Two-way fixed effects removes two sources of confounding:

1. **AC fixed effects (αᵢ):** absorb all time-invariant characteristics of each constituency — terrain, proximity to rivers, historical urbanisation, institutional quality. Without αᵢ, estimated flood effects would reflect geography rather than a causal impact.

2. **Year fixed effects (γₜ):** absorb macroeconomic shocks, climate trends, and policy changes that affect all ACs in a given year (e.g., national electricity expansion, monsoon anomalies).

The identifying assumption is conditional parallel trends: after removing αᵢ and γₜ, remaining variation in `Seasonal_Ratio` is as-good-as-random with respect to the idiosyncratic error εᵢₜ.

---

## OLS robustness

Pooled OLS (no fixed effects, district-clustered SEs) is run as a robustness check. Scripts: `run_nl_ols_pooled.py`, `run_nl_ols_by_state.py`, `run_ndbi_ols_pooled.py`, `run_ndbi_ols_by_state.py`.

The OLS flood coefficient on Δlog NL is null pooled and positive (wrong sign) for Bihar in the by-state specification. This sign reversal is expected: flood-prone ACs in Bihar tend to have faster NL growth for reasons unrelated to flooding (lower initial base, infrastructure catch-up). The TWFE specification removes this cross-sectional confound; OLS does not. The contrast between TWFE and OLS strengthens the case for the fixed-effects design.

---

## Estimation details

### R-squared reporting convention

Only **R² (within)** is reported in the main tables. Under `linearmodels.PanelOLS`, R² (between) and R² (overall) are frequently negative because the fixed effects deliberately remove cross-sectional variation; those metrics are not informative for a TWFE specification. This matches the output of Stata's `xtreg, fe`.

### District clustering and the Cameron-Miller rule

The pooled sample has 108 district clusters — comfortably above the Cameron-Miller (~50) threshold for reliable cluster-robust inference. State-by-state regressions have fewer clusters (19–37), which is below the threshold. Wild cluster bootstrap is planned as a robustness check (see `docs/roadmap.md`).

### Intercept in Equation 2

`linearmodels.PanelOLS` with `entity_effects=True` absorbs a constant into the entity means. An explicit constant column is included in the regressor matrix so that β₀ is reported; this does not affect the slope coefficients.
