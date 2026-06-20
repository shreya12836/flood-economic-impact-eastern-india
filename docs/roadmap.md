# Roadmap

Planned extensions and known limitations of the current analysis.

---

## Roads regressor

The original specification includes road infrastructure density as a control variable. It is not present in the current dataset.

**Plan:** merge district-level road density from the GeoSadak dataset (PMGSY village road network) or NHAI highway shapefiles onto `AC_UID`. Expected completion: end of June 2026 (GeoSadak data pending).

---

## Inference robustness

**Wild cluster bootstrap:** state-by-state regressions have 19–37 district clusters, below the Cameron-Miller (~50) rule of thumb. Wild cluster bootstrap (Rademacher weights) should be run for state-level results. Available via `wildboottest` (Python) or `boottest` (Stata).

**Two-way clustering:** cluster simultaneously on district and year to account for both cross-sectional spatial correlation and within-year common shocks. Available in `linearmodels` via a custom covariance estimator.

**Conley spatial standard errors:** controls for spatial autocorrelation within a distance cutoff. Requires AC centroid latitude/longitude coordinates (not currently in the dataset).

---

## Alternative flood proxies

Current treatment: `Seasonal_Ratio` (fraction of AC area seasonally flooded, JRC GSW).

Alternatives to test:
- `log(Water_SUM + 1)`: captures total water extent rather than fractional share
- `Permanent_Ratio`: isolates perennially flooded areas (drainage rather than seasonal shock)
- Year-of-extreme-event dummies: Bihar 2017 flood was anomalously severe; a dummy for `YEAR == 2017 × Bihar` tests whether the coefficient is driven by that single event
- Lagged flood: include `Seasonal_Ratio_{t−1}` to test whether flood effects persist into the following year

---

## Heterogeneity analysis

**Urban-rural split:** classify ACs by `LC_13_ratio` (urban fraction) above/below the state median and estimate separately. Flood effects on economic activity are likely weaker in more urban ACs with better drainage infrastructure.

**2017 event study:** Bihar experienced a major flood in 2017 affecting 19 districts. An event-study regression around that year would test pre-trend parallel trends and quantify dynamic treatment effects.

**Interaction with baseline development:** interact `Seasonal_Ratio` with baseline `NL_mean` (2014 level) to test whether richer ACs absorb flood shocks differently.

---

## Public release checklist

Before making the repository public:

- [ ] Confirm Election Commission AC boundary shapefile licence permits redistribution
- [ ] Confirm JRC GSW and Landsat-8 output licence (both are public domain / CC)
- [ ] Remove or anonymise any personally identifiable information if added in future data merges
- [ ] Add DOI or citation instructions for the processed dataset
- [ ] Verify `final_regression_dataset.xlsx` can be regenerated from the processed CSVs (document or script the merge step)
