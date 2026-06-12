# Data

## Processed CSVs — state-year panel files

One file per state per year. Each row is one Assembly Constituency (AC).

| File pattern | State | Years |
|---|---|---|
| `BiharFloods_20XX_processed.csv` | Bihar | 2015–2019 |
| `JharkhandFloods_20XX_processed.csv` | Jharkhand | 2015–2019 |
| `OdishaFloods_20XX_processed.csv` | Odisha | 2015–2019 |
| `WBFloods_20XX_processed.csv` | West Bengal | 2016–2019 |
| `WestBengalFloods_2015_processed.csv` | West Bengal | 2015 |

All files share the same column schema. The 2014 files exist in the raw panel but are retained only for constructing t−1 lags; they are not included in the estimation sample.

---

## Merged regression panel

`processed/final_regression_dataset.xlsx`

Left join of `master_dataset_T_clean.csv` (current-year variables) and `master_dataset_T_minus_1_clean.csv` (lagged variables) on `UNIT_ID + YEAR`. Join is one-to-one; no observations are lost. 4,674 rows × 80 columns.

This file is the input to all regression scripts in `src/regression/`.

---

## Area file

`processed/Area_AC_calculated.csv`

Approximated AC area (m²) for Bihar, Odisha, and West Bengal ACs, which lack `Area_AC` in their source files. Formula:

```
Area_AC ≈ Shape_Area (deg²) × (111320 m/deg)² × cos(state-mean latitude)
```

State-mean latitudes: Bihar 25.5°N, Jharkhand 23.5°N, Odisha 20.5°N, West Bengal 23.5°N.

Validation on the 470 Jharkhand rows where the true value is known: median error 0.76%, 95th percentile 1.52%, max 1.71%. Error arises from using state-mean latitude instead of per-AC centroid coordinates.

---

## Key column definitions

### Identifiers

| Column | Description |
|---|---|
| `ST_CODE` | State numeric code |
| `DT_CODE` | District numeric code within state |
| `AC_NO` | Assembly Constituency number within state |
| `AC_NAME` | AC name (string) |
| `AC_UID` | `ST_CODE_AC_NO` — unique AC panel key |
| `UNIT_ID` | `ST_CODE_DT_CODE_AC_NO_PC_NO` — unique observation key for panel joins |
| `YEAR` | Calendar year |
| `DISTRICT_ID` | `ST_CODE_DT_CODE` — used as the clustering variable |

### Flood exposure

| Column | Description |
|---|---|
| `Seasonal_Ratio` | Fraction of AC area classified as seasonally flooded water (JRC GSW); main treatment variable |
| `Permanent_Ratio` | Fraction of AC area classified as permanently flooded (JRC GSW) |
| `Water_SUM` | Total water pixels within AC boundary (JRC GSW pixel count) |

### Economic and infrastructure outcomes

| Column | Description |
|---|---|
| `NL_mean` | Mean nighttime light radiance within AC (VIIRS/DMSP) |
| `NL_median` | Median nighttime light radiance within AC |
| `NDBI_mean` | Mean Normalised Difference Built-up Index within AC (Landsat-8 SR) |
| `NDBI_median` | Median NDBI within AC |

### Vegetation control

| Column | Description |
|---|---|
| `NDVI_mean` | Mean Normalised Difference Vegetation Index within AC (Landsat-8 SR) |
| `NDVI_median` | Median NDVI within AC |

### Lagged controls (from T-1 file, joined into panel)

`NDVI_mean_t_minus_1`, `NDVI_median_t_minus_1`, `NDBI_mean_t_minus_1`, `NDBI_median_t_minus_1`, `NL_mean_t_minus_1`, `NL_median_t_minus_1`, `Water_SUM_t_minus_1`, `Water_SUM_t_minus_2`

### Land cover ratios

`LC_X_ratio` columns give the fraction of AC area in each MODIS/GlobeLand30 land cover class. Key classes used in analysis:

| Column | Land cover class |
|---|---|
| `LC_11_ratio` | Wetlands |
| `LC_12_ratio` | Cropland |
| `LC_13_ratio` | Urban / built-up |
| `LC_17_ratio` | Water bodies |

---

## Raw data sources

| Dataset | Provider | Access |
|---|---|---|
| JRC Global Surface Water | European Commission JRC | [global-surface-water.appspot.com](https://global-surface-water.appspot.com) |
| VIIRS Nighttime Lights | NOAA / NASA | [eogdata.mines.edu](https://eogdata.mines.edu/products/vnl/) |
| Landsat-8 SR | USGS / Google Earth Engine | [earthengine.google.com](https://earthengine.google.com) |
| AC Boundaries | Election Commission of India | Delimitation Order 2008 |
