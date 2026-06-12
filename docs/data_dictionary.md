# Data Dictionary

## Outcome variables

| Variable | Type | Description | Script |
|---|---|---|---|
| `dlog_NL` | Continuous | `log(NL_t) − log(NL_{t−1})` — year-on-year growth in nighttime light radiance | `run_nl_ols_pooled.py`, `run_nl_ols_by_state.py` |
| `delta_ndbi` | Continuous | `NDBI_t − NDBI_{t−1}` — year-on-year change in built-up index (level difference) | `run_ndbi_pooled.py`, `run_ndbi_by_state.py` |

---

## Treatment variable

| Variable | Type | Range | Description |
|---|---|---|---|
| `Seasonal_Ratio` | Continuous | [0, 1] | Fraction of AC area classified as seasonally flooded in a given year. Derived from JRC Global Surface Water 30m monthly composites. A value of 0.2 means 20% of the AC was under seasonal flood water that year. |

---

## Control variables

### Current-year controls

| Variable | Description |
|---|---|
| `NL_mean` | Mean VIIRS/DMSP nighttime light radiance (nW/cm²/sr) within AC boundary |
| `NL_median` | Median nighttime light radiance |
| `NDBI_mean` | Mean NDBI within AC (see index definition below) |
| `NDBI_median` | Median NDBI |
| `NDVI_mean` | Mean NDVI within AC (see index definition below) |
| `NDVI_median` | Median NDVI |

### Lagged controls (t−1)

Suffix `_t_minus_1` denotes the one-year lag of the corresponding variable, constructed by merging the T-1 panel on `UNIT_ID + YEAR`.

| Variable | Used in |
|---|---|
| `NDVI_mean_t_minus_1`, `NDVI_median_t_minus_1` | Eq. 1 (NL outcome) and Eq. 2 (NDBI outcome) |
| `NDBI_mean_t_minus_1`, `NDBI_median_t_minus_1` | Eq. 1 (NL outcome) |
| `NL_mean_t_minus_1`, `NL_median_t_minus_1` | Eq. 2 (NDBI outcome) |
| `Water_SUM_t_minus_1` | Available; not used in main specification |
| `Water_SUM_t_minus_2` | Available; not used in main specification |

---

## Index definitions

### NDVI — Normalised Difference Vegetation Index

```
NDVI = (Band 5 − Band 4) / (Band 5 + Band 4)
```

Landsat-8 OLI bands: Band 4 = Red (0.64–0.67 µm), Band 5 = NIR (0.85–0.88 µm).  
Range: [−1, 1]. Higher values indicate denser green vegetation. Positive in vegetated areas; near zero or negative in bare soil, water, or built-up surfaces.

### NDBI — Normalised Difference Built-up Index

```
NDBI = (Band 6 − Band 5) / (Band 6 + Band 5)
```

Landsat-8 OLI bands: Band 6 = SWIR-1 (1.57–1.65 µm), Band 5 = NIR (0.85–0.88 µm).  
Range: [−1, 1]. Higher values indicate greater proportion of built-up/impervious surface. Frequently negative in rural and forested ACs.

---

## Identifiers

| Column | Format | Description |
|---|---|---|
| `ST_CODE` | Integer | State numeric code (e.g., 10 = Bihar) |
| `DT_CODE` | Integer | District code within state |
| `AC_NO` | Integer | AC number within state |
| `PC_NO` | Integer | Parliamentary Constituency number |
| `AC_NAME` | String | AC name |
| `DIST_NAME` | String | District name |
| `AC_UID` | String | `{ST_CODE}_{AC_NO}` — unique AC identifier across the panel |
| `UNIT_ID` | String | `{ST_CODE}_{DT_CODE}_{AC_NO}_{PC_NO}` — unique join key for T / T-1 merge |
| `DISTRICT_ID` | String | `{ST_CODE}_{DT_CODE}` — district identifier used for clustering |
| `YEAR` | Integer | Calendar year (2014–2019) |

---

## Land cover ratios

Derived from GlobeLand30 / MODIS land cover classification. Each column gives the fraction of AC pixels in that class.

| Column | Land cover class |
|---|---|
| `LC_11_ratio` | Wetlands |
| `LC_12_ratio` | Cropland / agriculture |
| `LC_13_ratio` | Urban and built-up |
| `LC_14_ratio` | Bare land |
| `LC_15_ratio` | Snow / ice |
| `LC_16_ratio` | Shrubland |
| `LC_17_ratio` | Water bodies (permanent) |
| `LC_18_ratio` | Other |

`LC_SUM` = total classified pixels; `LC_X_ratio = LC_X / LC_SUM`.

---

## Area variables

| Column | Description |
|---|---|
| `Shape_Area` | AC polygon area in geographic degrees² (from Election Commission shapefile) |
| `Area_AC` | AC area in m², present only for Jharkhand in source files |
| `Area_AC_calculated` | Approximated AC area in m² (see `data/README.md` for formula); stored in `Area_AC_calculated.csv` |

---

## Flood-related columns (additional)

| Column | Description |
|---|---|
| `Permanent_Ratio` | Fraction of AC area permanently under water (JRC GSW) |
| `Water_SUM` | Total JRC GSW water pixels within AC boundary in year t |
| `Water_SUM_t_minus_1` | Same, year t−1 |
| `Water_SUM_t_minus_2` | Same, year t−2 |
| `HISTO_*` | Raw JRC GSW histogram bands (pixel counts by water occurrence category) |
