"""
Generate 4 OLS regression plots for the dissertation.

Inputs:
  - Regression_Results_NL_OLS_Pooled.xlsx
  - Regression_Results_NL_OLS_By_State.xlsx
  - Regression_Results_NDBI_OLS_Pooled.xlsx
  - Regression_Results_NDBI_OLS_By_State.xlsx
  - final_regression_dataset.xlsx (for year FE re-estimation)

Outputs (saved to figures/):
  - forest_plot_flood_OLS.png
  - mean_vs_median_flood_OLS.png
  - heatmap_all_coefficients_OLS.png
  - year_fixed_effects_OLS.png
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import TwoSlopeNorm
import seaborn as sns

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'C:\Users\BIT\Downloads\Processed_Flood_Files'
FIG_DIR = os.path.join(ROOT, 'figures')
os.makedirs(FIG_DIR, exist_ok=True)

STATES = ['Pooled', 'Bihar', 'Jharkhand', 'Odisha', 'West Bengal']
STATE_KEYS = ['BIHAR', 'JHARKHAND', 'ORISSA', 'WB']

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'figure.dpi': 120,
    'savefig.dpi': 200,
    'savefig.bbox': 'tight',
})


def stars(p):
    if pd.isna(p):
        return ''
    if p < 0.01: return '***'
    if p < 0.05: return '**'
    if p < 0.10: return '*'
    return ''


def load_results():
    """Load all OLS regression results into a tidy long dataframe."""
    rows = []
    for outcome, pooled_f, by_state_f in [
        ('NL', 'Regression_Results_NL_OLS_Pooled.xlsx', 'Regression_Results_NL_OLS_By_State.xlsx'),
        ('NDBI', 'Regression_Results_NDBI_OLS_Pooled.xlsx', 'Regression_Results_NDBI_OLS_By_State.xlsx'),
    ]:
        # Pooled — Median
        pdf = pd.read_excel(os.path.join(ROOT, pooled_f), sheet_name='Median_Coef')
        for _, r in pdf.iterrows():
            rows.append(dict(outcome=outcome, agg='Median', state='Pooled',
                             variable=r['Variable'], coef=r['Coefficient'],
                             se=r['Std_Error'], t=r['t_stat'], p=r['p_value'],
                             ci_low=r.get('CI_low_95', np.nan),
                             ci_high=r.get('CI_high_95', np.nan)))
        # Pooled — Mean
        pdf = pd.read_excel(os.path.join(ROOT, pooled_f), sheet_name='Mean_Coef')
        for _, r in pdf.iterrows():
            rows.append(dict(outcome=outcome, agg='Mean', state='Pooled',
                             variable=r['Variable'], coef=r['Coefficient'],
                             se=r['Std_Error'], t=r['t_stat'], p=r['p_value'],
                             ci_low=r.get('CI_low_95', np.nan),
                             ci_high=r.get('CI_high_95', np.nan)))
        # By state
        for state_key, state_label in zip(STATE_KEYS, ['Bihar', 'Jharkhand', 'Odisha', 'West Bengal']):
            for agg in ['Median', 'Mean']:
                sh = f'{state_key}_{agg}'
                df = pd.read_excel(os.path.join(ROOT, by_state_f), sheet_name=sh)
                for _, r in df.iterrows():
                    rows.append(dict(outcome=outcome, agg=agg, state=state_label,
                                     variable=r['Variable'], coef=r['Coefficient'],
                                     se=r['Std_Error'], t=r['t_stat'], p=r['p_value'],
                                     ci_low=np.nan, ci_high=np.nan))
    res = pd.DataFrame(rows)
    # Compute CI where missing
    res['ci_low'] = res['ci_low'].fillna(res['coef'] - 1.96 * res['se'])
    res['ci_high'] = res['ci_high'].fillna(res['coef'] + 1.96 * res['se'])
    return res


def normalize_var(v):
    """Map various column-name encodings of the same variable to a canonical short label."""
    if 'Seasonal_Ratio' in v: return 'Flood'
    if 'NDVI' in v: return 'NDVI_lag'
    if v.startswith('NL_') and 't_minus_1' in v: return 'NL_lag'
    if 'NDBI' in v and 't_minus_1' in v: return 'NDBI_lag'
    return v


# ============================================================
# PLOT 1 — Forest plot of flood coefficients with 95% CI
# ============================================================
def plot_forest(res):
    flood = res[res['variable'].str.contains('Seasonal_Ratio')].copy()
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.5), sharey=True)

    for ax, outcome, title in zip(axes, ['NL', 'NDBI'],
                                  [r'Outcome: $\Delta\log NL$ (Night Lights)',
                                   r'Outcome: $NDBI$ (Built-up Index)']):
        sub = flood[flood['outcome'] == outcome].copy()
        y_positions = []
        labels = []
        for i, state in enumerate(STATES):
            for j, agg in enumerate(['Mean', 'Median']):
                row = sub[(sub['state'] == state) & (sub['agg'] == agg)]
                if row.empty: continue
                r = row.iloc[0]
                y = -(i * 1.0 + (j - 0.5) * 0.35)
                y_positions.append((y, agg, state, r['coef'], r['ci_low'], r['ci_high'], r['p']))
                if j == 0:
                    labels.append((-(i * 1.0), state))

        for y, agg, state, coef, lo, hi, p in y_positions:
            color = '#1f77b4' if agg == 'Mean' else '#d62728'
            ax.errorbar(coef, y, xerr=[[coef - lo], [hi - coef]],
                        fmt='o', color=color, capsize=3, markersize=6,
                        markeredgecolor='black', markeredgewidth=0.5)
            star = stars(p)
            if star:
                ax.text(hi + (hi - lo) * 0.05, y, star, va='center',
                        fontsize=9, fontweight='bold', color=color)

        ax.axvline(0, color='gray', linestyle='--', linewidth=0.8)
        ax.set_yticks([y for y, _ in labels])
        ax.set_yticklabels([s for _, s in labels])
        ax.set_xlabel('Flood coefficient $\\beta_1$ (95% CI)')
        ax.set_title(title)
        ax.grid(axis='x', linestyle=':', alpha=0.4)

    # Legend
    handles = [
        plt.Line2D([0], [0], marker='o', color='#1f77b4', linestyle='', markersize=7,
                   markeredgecolor='black', markeredgewidth=0.5, label='Mean aggregation'),
        plt.Line2D([0], [0], marker='o', color='#d62728', linestyle='', markersize=7,
                   markeredgecolor='black', markeredgewidth=0.5, label='Median aggregation'),
    ]
    fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, -0.02), ncol=2, frameon=False)
    fig.suptitle('Estimated effect of flood exposure on economic activity and built-up index, by state',
                 fontsize=12, y=1.02)
    fig.tight_layout()
    out = os.path.join(FIG_DIR, 'forest_plot_flood_OLS.png')
    fig.savefig(out)
    plt.close(fig)
    print(f'  saved {out}')


# ============================================================
# PLOT 2 — Mean vs Median grouped bar comparison
# ============================================================
def plot_mean_vs_median(res):
    flood = res[res['variable'].str.contains('Seasonal_Ratio')].copy()
    fig, axes = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True)

    width = 0.35
    x = np.arange(len(STATES))
    for ax, outcome, title in zip(axes, ['NL', 'NDBI'],
                                   [r'Panel A: $\Delta\log NL$ (Night Lights)',
                                    r'Panel B: $NDBI$ (Built-up Index)']):
        sub = flood[flood['outcome'] == outcome].copy()
        means = []; medians = []; mean_err = []; median_err = []; mean_p = []; median_p = []
        for state in STATES:
            for agg, store, err, ps in [('Mean', means, mean_err, mean_p),
                                         ('Median', medians, median_err, median_p)]:
                row = sub[(sub['state'] == state) & (sub['agg'] == agg)]
                if row.empty:
                    store.append(np.nan); err.append(0); ps.append(np.nan)
                else:
                    r = row.iloc[0]
                    store.append(r['coef']); err.append(1.96 * r['se']); ps.append(r['p'])

        b1 = ax.bar(x - width/2, means, width, yerr=mean_err, capsize=3,
                    label='Mean aggregation', color='#1f77b4', alpha=0.85,
                    edgecolor='black', linewidth=0.5)
        b2 = ax.bar(x + width/2, medians, width, yerr=median_err, capsize=3,
                    label='Median aggregation', color='#d62728', alpha=0.85,
                    edgecolor='black', linewidth=0.5)

        for i, (m, p) in enumerate(zip(means, mean_p)):
            s = stars(p)
            if s and not np.isnan(m):
                offset = mean_err[i] + abs(m) * 0.05
                yy = m + offset if m >= 0 else m - offset
                ax.text(x[i] - width/2, yy, s, ha='center', va='bottom' if m >= 0 else 'top',
                        fontsize=9, fontweight='bold')
        for i, (m, p) in enumerate(zip(medians, median_p)):
            s = stars(p)
            if s and not np.isnan(m):
                offset = median_err[i] + abs(m) * 0.05
                yy = m + offset if m >= 0 else m - offset
                ax.text(x[i] + width/2, yy, s, ha='center', va='bottom' if m >= 0 else 'top',
                        fontsize=9, fontweight='bold')

        ax.axhline(0, color='gray', linewidth=0.8)
        ax.set_ylabel('Flood coefficient $\\beta_1$')
        ax.set_title(title)
        ax.grid(axis='y', linestyle=':', alpha=0.4)
        ax.legend(loc='upper right', frameon=True, fontsize=9)

    axes[1].set_xticks(x)
    axes[1].set_xticklabels(STATES)
    fig.suptitle('Robustness: Flood coefficient under mean vs median aggregation',
                 fontsize=12, y=1.0)
    fig.tight_layout()
    out = os.path.join(FIG_DIR, 'mean_vs_median_flood_OLS.png')
    fig.savefig(out)
    plt.close(fig)
    print(f'  saved {out}')


# ============================================================
# PLOT 3 — All-coefficients heatmap
# ============================================================
def plot_heatmap(res):
    res = res.copy()
    res['var_short'] = res['variable'].apply(normalize_var)

    fig, axes = plt.subplots(1, 2, figsize=(12, 6.5),
                             gridspec_kw={'width_ratios': [3, 4]})

    # Row order
    row_order = []
    for state in STATES:
        for agg in ['Mean', 'Median']:
            row_order.append((state, agg))
    row_labels = [f'{s} ({a})' for s, a in row_order]

    for ax, outcome, vars_ordered, title in zip(
        axes, ['NL', 'NDBI'],
        [['Flood', 'NDVI_lag', 'NDBI_lag'],
         ['Flood', 'NDVI_lag', 'NL_lag', 'NDBI_lag']],
        [r'Outcome: $\Delta\log NL$', r'Outcome: $NDBI$ (level)']):

        sub = res[res['outcome'] == outcome]
        # Build matrices of coef and stars
        mat = np.full((len(row_order), len(vars_ordered)), np.nan)
        annot = np.full((len(row_order), len(vars_ordered)), '', dtype=object)
        for i, (state, agg) in enumerate(row_order):
            for j, v in enumerate(vars_ordered):
                row = sub[(sub['state'] == state) & (sub['agg'] == agg) &
                          (sub['var_short'] == v)]
                if row.empty: continue
                r = row.iloc[0]
                mat[i, j] = r['coef']
                annot[i, j] = f'{r["coef"]:.3f}{stars(r["p"])}'

        # Diverging colormap centered at 0
        vmax = np.nanmax(np.abs(mat))
        if not np.isfinite(vmax) or vmax == 0:
            vmax = 1
        norm = TwoSlopeNorm(vcenter=0, vmin=-vmax, vmax=vmax)
        sns.heatmap(mat, annot=annot, fmt='', cmap='RdBu_r', norm=norm,
                    xticklabels=vars_ordered, yticklabels=row_labels if ax is axes[0] else False,
                    cbar_kws={'label': 'Coefficient', 'shrink': 0.8},
                    linewidths=0.4, linecolor='white', ax=ax,
                    annot_kws={'fontsize': 8})
        ax.set_title(title)
        ax.set_xlabel('')
        ax.tick_params(axis='x', rotation=0)

    fig.suptitle('Summary of 20 OLS regressions: coefficients with significance stars\n'
                 '(*** p<0.01, ** p<0.05, * p<0.10)',
                 fontsize=11, y=1.02)
    fig.tight_layout()
    out = os.path.join(FIG_DIR, 'heatmap_all_coefficients_OLS.png')
    fig.savefig(out)
    plt.close(fig)
    print(f'  saved {out}')


# ============================================================
# PLOT 4 — Year fixed effects (re-estimated)
# ============================================================
def plot_year_fe():
    df = pd.read_excel(os.path.join(ROOT, 'final_regression_dataset.xlsx'), sheet_name='Panel')
    # Compute outcomes
    df = df[df['YEAR'] >= 2015].copy()  # drop 2014 (no lag)
    df = df[df['NL_mean'] > 0]
    df = df[df['NL_mean_t_minus_1'] > 0]
    df = df[df['NL_median'] > 0]
    df = df[df['NL_median_t_minus_1'] > 0]
    df['dlog_NL_mean'] = np.log(df['NL_mean']) - np.log(df['NL_mean_t_minus_1'])
    df['dlog_NL_median'] = np.log(df['NL_median']) - np.log(df['NL_median_t_minus_1'])

    from linearmodels import PanelOLS

    def fit_and_extract_year_effects(formula_dep, controls, df_):
        # Build explicit year dummies as columns (drop 2015 as reference)
        df_ = df_.dropna(subset=[formula_dep] + controls).copy()
        year_dummies = []
        for yr in sorted(df_['YEAR'].unique()):
            if yr == 2015:
                continue
            col = f'YR_{int(yr)}'
            df_[col] = (df_['YEAR'] == yr).astype(float)
            year_dummies.append(col)
        df_p = df_.set_index(['AC_UID', 'YEAR'])
        rhs = ' + '.join(controls + year_dummies)
        formula = f'{formula_dep} ~ 1 + {rhs} + EntityEffects'
        try:
            mod = PanelOLS.from_formula(formula, data=df_p, drop_absorbed=True)
            res = mod.fit(cov_type='clustered', cluster_entity=False,
                          clusters=df_p['DT_CODE'])
        except Exception as e:
            print(f'    PanelOLS failed for {formula_dep}: {e}; falling back')
            return None
        params = res.params
        ses = res.std_errors
        years = []
        for col in year_dummies:
            if col in params.index:
                yr = int(col.replace('YR_', ''))
                years.append((yr, params[col], ses[col]))
        years = sorted(years)
        return years

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    # NL panel
    ax = axes[0]
    for spec, dep, controls, color, marker in [
        ('NL Mean',   'dlog_NL_mean',   ['Seasonal_Ratio', 'NDVI_mean_t_minus_1', 'NDBI_mean_t_minus_1'],
         '#1f77b4', 'o'),
        ('NL Median', 'dlog_NL_median', ['Seasonal_Ratio', 'NDVI_median_t_minus_1', 'NDBI_median_t_minus_1'],
         '#d62728', 's'),
    ]:
        ye = fit_and_extract_year_effects(dep, controls, df)
        if ye is None: continue
        yrs = [2015] + [y for y, _, _ in ye]
        coefs = [0] + [c for _, c, _ in ye]
        sees  = [0] + [s for _, _, s in ye]
        ax.errorbar(yrs, coefs, yerr=[1.96 * s for s in sees],
                    fmt=marker + '-', color=color, capsize=3, label=spec,
                    markersize=6, markeredgecolor='black', markeredgewidth=0.5)
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Year')
    ax.set_ylabel('Year fixed effect (relative to 2015)')
    ax.set_title(r'Outcome: $\Delta\log NL$')
    ax.set_xticks([2015, 2016, 2017, 2018, 2019])
    ax.legend(frameon=True, fontsize=9)
    ax.grid(linestyle=':', alpha=0.4)

    # NDBI panel
    ax = axes[1]
    for spec, dep, controls, color, marker in [
        ('NDBI Mean',   'NDBI_mean',
         ['Seasonal_Ratio', 'NDVI_mean_t_minus_1', 'NL_mean_t_minus_1', 'NDBI_mean_t_minus_1'],
         '#1f77b4', 'o'),
        ('NDBI Median', 'NDBI_median',
         ['Seasonal_Ratio', 'NDVI_median_t_minus_1', 'NL_median_t_minus_1', 'NDBI_median_t_minus_1'],
         '#d62728', 's'),
    ]:
        ye = fit_and_extract_year_effects(dep, controls, df)
        if ye is None: continue
        yrs = [2015] + [y for y, _, _ in ye]
        coefs = [0] + [c for _, c, _ in ye]
        sees  = [0] + [s for _, _, s in ye]
        ax.errorbar(yrs, coefs, yerr=[1.96 * s for s in sees],
                    fmt=marker + '-', color=color, capsize=3, label=spec,
                    markersize=6, markeredgecolor='black', markeredgewidth=0.5)
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Year')
    ax.set_ylabel('Year fixed effect (relative to 2015)')
    ax.set_title(r'Outcome: $NDBI$ (level)')
    ax.set_xticks([2015, 2016, 2017, 2018, 2019])
    ax.legend(frameon=True, fontsize=9)
    ax.grid(linestyle=':', alpha=0.4)

    fig.suptitle('Year fixed effects from pooled OLS (AC FE absorbed, year dummies relative to 2015)',
                 fontsize=11, y=1.02)
    fig.tight_layout()
    out = os.path.join(FIG_DIR, 'year_fixed_effects_OLS.png')
    fig.savefig(out)
    plt.close(fig)
    print(f'  saved {out}')


if __name__ == '__main__':
    print('Loading regression results...')
    res = load_results()
    print(f'  loaded {len(res)} coefficient rows')
    print('\nGenerating Plot 1: Forest plot of flood coefficients with 95% CI')
    plot_forest(res)
    print('\nGenerating Plot 2: Mean vs Median comparison')
    plot_mean_vs_median(res)
    print('\nGenerating Plot 3: All-coefficients heatmap')
    plot_heatmap(res)
    print('\nGenerating Plot 4: Year fixed effects')
    plot_year_fe()
    print('\nAll plots saved to', FIG_DIR)
