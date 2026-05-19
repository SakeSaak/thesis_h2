"""
01_eua_event_study.py — Market-implied carbon-conditional bewijs via stock prices.

Hypothese: Als het carbon-conditional mechanisme uit Chapter 7 echt is, dan zouden
pure-PEM hydrogen aandelen (Nel, ITM, Plug, Ballard) sterker moeten reageren op
EUA-prijsbewegingen dan Blue-zware oil majors (BP, Shell, Exxon, Equinor, Chevron).

Drie tests:
  A. Time-series CAPM met EUA-loading: r_i = α + β_market*r_SPY + γ_eua*r_KEUA + ε
     Vergelijk γ_eua tussen groepen
  B. Event study rond extreme EUA-dagen (top/bottom 5% returns)
     Bereken mean abnormal returns per groep
  C. Differentiële test: γ_PEM - γ_oil voor formele identificatie
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import yfinance as yf
import statsmodels.api as sm
import matplotlib.pyplot as plt

OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/07_event_study")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "figures").mkdir(exist_ok=True)

# ============================================================================
# 1. TICKER LIJSTEN
# ============================================================================

# Pure PEM / Green hydrogen pure-plays
GREEN_PURE = {
    'NEL.OL':  'Nel ASA',              # Noorse PEM manufacturer
    'PLUG':    'Plug Power',           # US fuel cell + electrolyser
    'ITM.L':   'ITM Power',            # UK PEM manufacturer
    'BLDP':    'Ballard Power',        # Fuel cell
    'BE':      'Bloom Energy',         # Solid oxide
}

# Blue-exposed oil majors (allemaal hebben Blue projecten in onze v7 sample)
BLUE_HEAVY = {
    'BP':      'BP plc',
    'SHEL':    'Shell plc',
    'XOM':     'Exxon Mobil',
    'EQNR':    'Equinor ASA',
    'CVX':     'Chevron',
    'TTE':     'TotalEnergies',
}

# Industrial gas (gemengde exposure, vergelijkingsgroep)
INDUSTRIAL_GAS = {
    'LIN':     'Linde plc',
    'APD':     'Air Products',
    'AI.PA':   'Air Liquide',
}

# Baselines & EUA proxy
BASELINE = {
    'KEUA':    'KraneShares EUA Strategy ETF (EUA proxy)',
    'SPY':     'S&P 500 ETF (market)',
    'XLE':     'Energy Select Sector ETF',
    'ICLN':    'iShares Global Clean Energy ETF',
}

ALL_TICKERS = {**GREEN_PURE, **BLUE_HEAVY, **INDUSTRIAL_GAS, **BASELINE}

# Sample periode: KEUA bestaat sinds juli 2021
START_DATE = "2021-08-01"
END_DATE = "2025-06-30"


def hdr(t): print("\n" + "=" * 76 + f"\n{t}\n" + "=" * 76)


# ============================================================================
# 2. DOWNLOAD STOCK DATA
# ============================================================================
hdr(f"Download stock prices: {len(ALL_TICKERS)} tickers, {START_DATE} → {END_DATE}")

tickers_list = list(ALL_TICKERS.keys())
print(f"Tickers: {tickers_list}")

raw = yf.download(tickers_list, start=START_DATE, end=END_DATE,
                  auto_adjust=True, progress=False)

# Extract Close prices
if isinstance(raw.columns, pd.MultiIndex):
    px = raw['Close'].copy()
else:
    px = raw.copy()

# Check welke tickers gelukt zijn
px = px.dropna(axis=1, how='all')
print(f"\nGedownload (na cleanup): {px.shape[1]} tickers")
print(f"Gefaald: {set(tickers_list) - set(px.columns)}")
print(f"Date range: {px.index[0]} → {px.index[-1]}")
print(f"Aantal trading days: {len(px)}")

# Drop rows met meer dan 50% missing
px = px.dropna(thresh=int(px.shape[1] * 0.5))

# Forward fill remaining gaps (bijvoorbeeld holidays in EU markets)
px = px.ffill().dropna()
print(f"Na cleanup: {len(px)} dagen × {px.shape[1]} tickers")


# ============================================================================
# 3. DAILY RETURNS
# ============================================================================
rets = np.log(px / px.shift(1)).dropna(how='any')
print(f"\nDaily returns matrix: {rets.shape}")
print(f"\nDescriptive stats (annualized %):")
desc = pd.DataFrame({
    'mean_annual_%': (rets.mean() * 252 * 100).round(2),
    'vol_annual_%': (rets.std() * np.sqrt(252) * 100).round(2),
    'sharpe': (rets.mean() / rets.std() * np.sqrt(252)).round(2),
})
print(desc.to_string())


# ============================================================================
# 4. TEST A: TIME-SERIES CAPM MET EUA-LOADING
# ============================================================================
hdr("TEST A: Time-series CAPM met EUA-loading per ticker")
print("\nModel: r_i,t = α + β_market * r_SPY,t + γ_eua * r_KEUA,t + ε_i,t\n")

if 'KEUA' not in rets.columns or 'SPY' not in rets.columns:
    print("KEUA of SPY ontbreekt — niet uitvoerbaar")
else:
    r_spy = rets['SPY']
    r_keua = rets['KEUA']
    
    results = []
    for ticker, name in ALL_TICKERS.items():
        if ticker not in rets.columns or ticker in ('SPY','KEUA','XLE','ICLN'):
            continue
        if ticker == 'KEUA' or ticker == 'SPY':
            continue
        r_i = rets[ticker]
        X = pd.DataFrame({'r_spy': r_spy, 'r_keua': r_keua})
        X = sm.add_constant(X)
        try:
            model = sm.OLS(r_i, X, missing='drop').fit()
            results.append({
                'ticker': ticker,
                'name': name,
                'group': ('GREEN' if ticker in GREEN_PURE else 
                          'OIL' if ticker in BLUE_HEAVY else
                          'INDGAS'),
                'alpha_daily_%': model.params['const']*100,
                'beta_market': model.params['r_spy'],
                'beta_market_t': model.tvalues['r_spy'],
                'gamma_eua': model.params['r_keua'],
                'gamma_eua_t': model.tvalues['r_keua'],
                'r2': model.rsquared,
                'n_obs': int(model.nobs),
            })
        except Exception as e:
            print(f"  Failed {ticker}: {e}")
    
    res_df = pd.DataFrame(results)
    res_df = res_df.sort_values(['group','gamma_eua'], ascending=[True, False])
    print(res_df.round(4).to_string(index=False))
    
    # Group means
    print("\nGemiddelde γ_eua per groep:")
    grp_summary = res_df.groupby('group').agg(
        mean_gamma=('gamma_eua', 'mean'),
        mean_gamma_t=('gamma_eua_t', 'mean'),
        n_tickers=('ticker', 'size'),
    ).round(4)
    print(grp_summary)
    
    res_df.to_csv(OUT / 'capm_eua_loadings.csv', index=False)


# ============================================================================
# 5. TEST B: EVENT STUDY ROND EXTREME EUA-DAGEN
# ============================================================================
hdr("TEST B: Event study rond extreme EUA-dagen (top/bottom 5%)")

if 'KEUA' in rets.columns:
    eua_ret = rets['KEUA']
    q95 = eua_ret.quantile(0.95)
    q05 = eua_ret.quantile(0.05)
    
    up_days = eua_ret[eua_ret >= q95].index
    down_days = eua_ret[eua_ret <= q05].index
    
    print(f"EUA daily return cutoffs:")
    print(f"  Top 5% (up-shocks):   ≥ {q95*100:+.2f}%  ({len(up_days)} dagen)")
    print(f"  Bottom 5% (down):     ≤ {q05*100:+.2f}%  ({len(down_days)} dagen)")
    print(f"  EUA mean abs return op up days: {eua_ret.loc[up_days].mean()*100:+.2f}%")
    print(f"  EUA mean abs return op down days: {eua_ret.loc[down_days].mean()*100:+.2f}%")
    
    # Compute abnormal returns op event days (controlling for SPY)
    print("\nAbnormal returns op EUA up/down dagen:")
    print("(Abnormal return = ticker return - β_market * SPY return)\n")
    
    abnormal_results = []
    for ticker in [t for t in rets.columns if t not in ('SPY','KEUA','XLE','ICLN')]:
        name = ALL_TICKERS.get(ticker, ticker)
        group = ('GREEN' if ticker in GREEN_PURE else 
                 'OIL' if ticker in BLUE_HEAVY else
                 'INDGAS' if ticker in INDUSTRIAL_GAS else 'OTHER')
        
        # Compute beta via market model excluding event days
        non_event = rets.index.difference(up_days.union(down_days))
        beta_market = np.cov(rets[ticker].loc[non_event], rets['SPY'].loc[non_event])[0,1] / np.var(rets['SPY'].loc[non_event])
        
        # Abnormal return = R_i - β * R_SPY
        ar = rets[ticker] - beta_market * rets['SPY']
        
        ar_up_mean = ar.loc[up_days].mean() * 100
        ar_down_mean = ar.loc[down_days].mean() * 100
        ar_diff = ar_up_mean - ar_down_mean  # Symmetric response
        
        # T-stat for ar_up_mean (Welch's)
        t_up = ar.loc[up_days].mean() / (ar.loc[up_days].std() / np.sqrt(len(up_days)))
        t_down = ar.loc[down_days].mean() / (ar.loc[down_days].std() / np.sqrt(len(down_days)))
        
        abnormal_results.append({
            'ticker': ticker, 'group': group, 'name': name,
            'AR_up_mean_%': ar_up_mean, 'AR_up_t': t_up,
            'AR_down_mean_%': ar_down_mean, 'AR_down_t': t_down,
            'AR_diff_%': ar_diff,
            'beta_market': beta_market,
        })
    
    ar_df = pd.DataFrame(abnormal_results).sort_values(['group','AR_diff_%'], ascending=[True, False])
    print(ar_df.round(3).to_string(index=False))
    
    # Group level summary
    print("\nGemiddelde abnormal returns per groep:")
    grp_ar = ar_df.groupby('group').agg(
        mean_AR_up=('AR_up_mean_%', 'mean'),
        mean_AR_down=('AR_down_mean_%', 'mean'),
        mean_AR_diff=('AR_diff_%', 'mean'),
    ).round(3)
    print(grp_ar)
    
    ar_df.to_csv(OUT / 'event_study_abnormal_returns.csv', index=False)


# ============================================================================
# 6. TEST C: FORMELE DIFFERENTIAL TEST
# ============================================================================
hdr("TEST C: Differentiële test — γ_GREEN vs γ_OIL")

if 'res_df' in locals() and len(res_df) > 0:
    green_gamma = res_df[res_df['group']=='GREEN']['gamma_eua'].values
    oil_gamma = res_df[res_df['group']=='OIL']['gamma_eua'].values
    
    print(f"GREEN pure-plays ({len(green_gamma)}): γ_eua = {green_gamma}")
    print(f"  Gemiddelde: {green_gamma.mean():+.4f}")
    print(f"  Std:        {green_gamma.std():.4f}")
    print(f"\nOIL majors ({len(oil_gamma)}): γ_eua = {oil_gamma}")
    print(f"  Gemiddelde: {oil_gamma.mean():+.4f}")
    print(f"  Std:        {oil_gamma.std():.4f}")
    
    from scipy import stats
    t_stat, p_value = stats.ttest_ind(green_gamma, oil_gamma)
    print(f"\nWelch's t-test (GREEN - OIL): t = {t_stat:.3f}, p = {p_value:.4f}")
    diff = green_gamma.mean() - oil_gamma.mean()
    print(f"Verschil GREEN - OIL: {diff:+.4f}")
    
    if p_value < 0.05 and diff > 0:
        print("\n✓ STATISTISCH SIGNIFICANT: GREEN pure-plays hebben hogere EUA-loading dan OIL majors")
        print("  → Market-implied bewijs voor het carbon-conditional mechanisme!")
    elif diff > 0:
        print(f"\n~ GREEN hogere loading dan OIL maar niet significant (p={p_value:.3f})")
        print(f"  Sample size beperkt; richting is consistent met theorie")
    else:
        print(f"\n✗ OIL HOGERE LOADING dan GREEN — onverwacht")


# ============================================================================
# 7. VISUALISATIE
# ============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: γ_eua per ticker, gekleurd per groep
if 'res_df' in locals() and len(res_df) > 0:
    ax = axes[0]
    colors = {'GREEN': '#228833', 'OIL': '#882255', 'INDGAS': '#888888'}
    for g, sub in res_df.groupby('group'):
        ax.barh(sub['ticker'].values, sub['gamma_eua'].values,
                color=colors.get(g,'#888'), label=g, alpha=0.8)
    ax.axvline(0, color='black', lw=1)
    ax.set_xlabel(r"$\gamma_{\mathrm{eua}}$ (EUA return loading)")
    ax.set_title("EUA-loading per ticker, gegroepeerd")
    ax.legend()
    ax.grid(alpha=0.3, axis='x')

# Plot 2: Abnormal returns op event days
if 'ar_df' in locals() and len(ar_df) > 0:
    ax = axes[1]
    x = np.arange(len(ar_df))
    w = 0.35
    bars1 = ax.bar(x - w/2, ar_df['AR_up_mean_%'].values, w, label='AR op EUA-up dagen', color='#4477AA')
    bars2 = ax.bar(x + w/2, ar_df['AR_down_mean_%'].values, w, label='AR op EUA-down dagen', color='#CC6677')
    ax.axhline(0, color='black', lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(ar_df['ticker'].values, rotation=45, ha='right')
    ax.set_ylabel("Abnormal return (%)")
    ax.set_title("Abnormal returns op EUA-shock dagen")
    ax.legend()
    ax.grid(alpha=0.3, axis='y')

plt.tight_layout()
fig.savefig(OUT / "figures/event_study_results.pdf")
plt.close()
print(f"\nFiguur opgeslagen: {OUT}/figures/event_study_results.pdf")
print(f"\nAlle output in: {OUT}")
