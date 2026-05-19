"""
01_cbam_equity_event_study.py — Equity event study rond CBAM definitive launch.

Treatment moment: 2 januari 2026 (eerste trading day onder CBAM definitive period).
Three event-date candidates getest:
  - 2 januari 2026 (definitive launch — PRIMARY)
  - 3 maart 2026 (EC besluit CBAM NIET op te schorten voor H2-fertilizers)
  - 9 december 2025 (kort daarvoor: 3 weken before launch, salience build-up)

Treatment groups (CBAM-exposed):
  A. Hydrogen-based fertilizer producers (Yara, Nutrien, CF Industries)
  B. Steel met H2-DRI ambities (ArcelorMittal, SSAB, Salzgitter)
  C. Blue-heavy oil majors (BP, Shell, Equinor, TotalEnergies)

Control groups (less / non-CBAM exposed):
  D. PEM pure-plays (Nel, ITM, Plug, Ballard, Bloom)
  E. Industrial gas (Linde, Air Products, Air Liquide) — minder direct CBAM-blootgesteld
  F. Pure benchmark: SPY, KEUA voor controle

Methodology volgens Hanemaaijer-Ketel-Marie (2024):
  CAR_i,t = sum over event window van (R_i,t - alpha_i - beta_i * R_market,t)
  Vergelijk treated groep CAR vs control groep CAR rond event date.
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
from datetime import datetime

OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/08_cbam_event_study")
(OUT / "figures").mkdir(parents=True, exist_ok=True)

# ============================================================================
# TICKERS — categorized by CBAM exposure
# ============================================================================
TICKERS = {
    # GROUP A: Fertilizer/chemicals — CBAM direct-coverage from Jan 2026
    'YAR.OL': ('FERTILIZER', 'Yara International'),
    'NTR':    ('FERTILIZER', 'Nutrien'),
    'CF':     ('FERTILIZER', 'CF Industries'),
    'ICL':    ('FERTILIZER', 'ICL Group'),
    
    # GROUP B: Steel — CBAM-covered Blue H2 consumers
    'MT':     ('STEEL', 'ArcelorMittal'),
    'SSAB-B.ST': ('STEEL', 'SSAB'),
    'SZG.DE': ('STEEL', 'Salzgitter'),
    
    # GROUP C: Blue-heavy oil majors (indirect upstream CBAM exposure)
    'BP':     ('OIL_MAJOR', 'BP plc'),
    'SHEL':   ('OIL_MAJOR', 'Shell plc'),
    'EQNR':   ('OIL_MAJOR', 'Equinor ASA'),
    'TTE':    ('OIL_MAJOR', 'TotalEnergies'),
    'XOM':    ('OIL_MAJOR', 'Exxon Mobil'),
    
    # GROUP D: PEM pure-plays (control — no fossil input, expected less CBAM signal)
    'NEL.OL': ('PEM_PURE', 'Nel ASA'),
    'PLUG':   ('PEM_PURE', 'Plug Power'),
    'ITM.L':  ('PEM_PURE', 'ITM Power'),
    'BLDP':   ('PEM_PURE', 'Ballard Power'),
    'BE':     ('PEM_PURE', 'Bloom Energy'),
    
    # GROUP E: Industrial gas (intermediate exposure)
    'LIN':    ('INDGAS', 'Linde'),
    'APD':    ('INDGAS', 'Air Products'),
    'AI.PA':  ('INDGAS', 'Air Liquide'),
    
    # GROUP F: Benchmarks
    'SPY':    ('BENCHMARK', 'S&P 500'),
    'KEUA':   ('BENCHMARK', 'EUA proxy ETF'),
    '^STOXX50E': ('BENCHMARK', 'EuroStoxx 50'),
}

EVENT_DATES = {
    'CBAM_definitive_launch': '2026-01-02',
    'EC_rejects_suspension':  '2026-03-03',
    'CBAM_three_months_pre':  '2025-09-30',  # PLACEBO
    'CBAM_one_year_pre':      '2025-01-02',  # PLACEBO
}

# Estimation window: 250 trading days BEFORE event (CAPM beta estimation)
# Event window: [-10, +20] trading days around event
EST_WINDOW = 250
EVT_PRE = 10
EVT_POST = 20

def hdr(t): print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# ============================================================================
# 1. DOWNLOAD DATA
# ============================================================================
hdr("Download equity data (Aug 2023 - May 2026)")

tickers_list = list(TICKERS.keys())
print(f"Aantal tickers: {len(tickers_list)}")

raw = yf.download(tickers_list, start="2023-08-01", end="2026-05-19",
                  auto_adjust=True, progress=False)

if isinstance(raw.columns, pd.MultiIndex):
    px = raw['Close'].copy()
else:
    px = raw.copy()

px = px.dropna(axis=1, how='all')
print(f"Tickers met data: {px.shape[1]}")
print(f"Tickers missing: {sorted(set(tickers_list) - set(px.columns))}")

px = px.dropna(thresh=int(px.shape[1] * 0.5)).ffill().dropna()
rets = np.log(px / px.shift(1)).dropna(how='any')
print(f"Daily returns matrix: {rets.shape}")
print(f"Date range: {rets.index[0].strftime('%Y-%m-%d')} → {rets.index[-1].strftime('%Y-%m-%d')}")


# ============================================================================
# 2. EVENT STUDY PER EVENT DATE
# ============================================================================
def event_study(rets, event_date, est_window=250, evt_pre=10, evt_post=20,
                market_ticker='SPY'):
    """
    Bereken Cumulative Abnormal Returns (CAR) per ticker rond event_date.
    Estimation window: [event_date - est_window - evt_pre, event_date - evt_pre - 1]
    Event window: [event_date - evt_pre, event_date + evt_post]
    """
    event_dt = pd.Timestamp(event_date)
    
    # Find nearest trading day on or after event_date
    available_dates = rets.index
    if event_dt not in available_dates:
        future = available_dates[available_dates >= event_dt]
        if len(future) == 0:
            return None
        event_dt = future[0]
    
    event_idx = available_dates.get_loc(event_dt)
    
    # Estimation window
    est_start = max(0, event_idx - est_window - evt_pre)
    est_end = event_idx - evt_pre
    if est_end - est_start < 50:
        return None  # niet genoeg estimation data
    
    # Event window
    evt_start = max(0, event_idx - evt_pre)
    evt_end = min(len(available_dates) - 1, event_idx + evt_post)
    
    est_data = rets.iloc[est_start:est_end]
    evt_data = rets.iloc[evt_start:evt_end + 1]
    
    if market_ticker not in rets.columns:
        return None
    
    results = {}
    for ticker in rets.columns:
        if ticker == market_ticker:
            continue
        # CAPM estimation
        r_i = est_data[ticker]
        r_m = est_data[market_ticker]
        X = sm.add_constant(r_m.values)
        try:
            mdl = sm.OLS(r_i.values, X).fit()
            alpha, beta = mdl.params[0], mdl.params[1]
            sigma_e = np.sqrt(mdl.mse_resid)
        except Exception:
            continue
        
        # Abnormal returns over event window
        r_i_evt = evt_data[ticker]
        r_m_evt = evt_data[market_ticker]
        ar = r_i_evt - alpha - beta * r_m_evt
        car = ar.cumsum()
        
        # Standardize CAR by sqrt(L) * sigma_e (Brown-Warner 1985)
        car_t = car / (np.sqrt(np.arange(1, len(car) + 1)) * sigma_e)
        
        results[ticker] = {
            'event_dt_actual': event_dt,
            'ar': ar,
            'car': car,
            'car_t': car_t,
            'beta': beta,
            'alpha': alpha,
            'sigma_e': sigma_e,
            'evt_days': np.arange(-evt_pre, evt_post + 1)[:len(car)],
        }
    return results


# ============================================================================
# 3. RUN EVENT STUDY FOR EACH EVENT DATE
# ============================================================================
all_results = {}
for event_name, event_date in EVENT_DATES.items():
    hdr(f"Event study: {event_name} ({event_date})")
    res = event_study(rets, event_date,
                      est_window=EST_WINDOW, evt_pre=EVT_PRE, evt_post=EVT_POST)
    if res is None:
        print(f"  Geen data beschikbaar voor {event_date}")
        continue
    
    # Aggregate per group
    group_cars = {}
    group_t = {}
    for ticker, r in res.items():
        group = TICKERS[ticker][0]
        if group == 'BENCHMARK':
            continue
        if group not in group_cars:
            group_cars[group] = []
            group_t[group] = []
        group_cars[group].append(r['car'].values)
        group_t[group].append(r['car_t'].values)
    
    # Average CAR per group
    print(f"\nCAR (Cumulative Abnormal Return) per groep, event day +20:")
    print(f"{'Group':<14s} | CAR end (%) | t-stat | n")
    print("-" * 50)
    
    group_summary = {}
    for group in ['FERTILIZER', 'STEEL', 'OIL_MAJOR', 'INDGAS', 'PEM_PURE']:
        if group not in group_cars:
            continue
        cars = np.array(group_cars[group])
        # Align to minimum length
        min_len = min(len(c) for c in group_cars[group])
        cars_arr = np.array([c[:min_len] for c in group_cars[group]])
        mean_car = cars_arr.mean(axis=0)
        # t-stat for mean CAR at end
        if cars_arr.shape[0] > 1:
            t_end = mean_car[-1] / (cars_arr[:, -1].std() / np.sqrt(cars_arr.shape[0]))
        else:
            t_end = np.nan
        n = cars_arr.shape[0]
        print(f"{group:<14s} | {mean_car[-1]*100:+7.2f}%    | {t_end:+5.2f}  | {n}")
        group_summary[group] = {'mean_car': mean_car, 't_end': t_end, 'n': n}
    
    all_results[event_name] = {'tickers': res, 'groups': group_summary}


# ============================================================================
# 4. CROSS-EVENT COMPARISON
# ============================================================================
hdr("CROSS-EVENT VERGELIJKING — CAR aan event day +20 per groep")

print(f"\n{'Group':<14s} | CBAM-launch | EC-reject  | 3mo-pre*   | 1yr-pre*")
print(f"{'':14s} | (Jan 2, 26) | (Mar 3, 26)| placebo    | placebo")
print("-" * 70)

ordered = ['FERTILIZER', 'STEEL', 'OIL_MAJOR', 'INDGAS', 'PEM_PURE']
for grp in ordered:
    row = f"{grp:<14s} |"
    for ev_name in ['CBAM_definitive_launch', 'EC_rejects_suspension',
                    'CBAM_three_months_pre', 'CBAM_one_year_pre']:
        if ev_name in all_results and grp in all_results[ev_name]['groups']:
            car_val = all_results[ev_name]['groups'][grp]['mean_car'][-1] * 100
            row += f" {car_val:+8.2f}%  |"
        else:
            row += "     n/a    |"
    print(row)
print("\n* placebo dates: same time of year, no real CBAM event")


# ============================================================================
# 5. VISUALISATIE — CAR paths per groep voor primary event
# ============================================================================
primary_event = 'CBAM_definitive_launch'
if primary_event in all_results:
    fig, ax = plt.subplots(figsize=(12, 7))
    colors = {
        'FERTILIZER': '#882255',  # rood — most exposed
        'STEEL': '#CC6677',       
        'OIL_MAJOR': '#DDCC77',    
        'INDGAS': '#999933',      
        'PEM_PURE': '#117733',    # groen — control
    }
    
    for grp in ordered:
        if grp not in all_results[primary_event]['groups']:
            continue
        mean_car = all_results[primary_event]['groups'][grp]['mean_car']
        n = all_results[primary_event]['groups'][grp]['n']
        days = np.arange(-EVT_PRE, -EVT_PRE + len(mean_car))
        ax.plot(days, mean_car * 100, '-o', color=colors[grp], lw=2,
                markersize=4, label=f"{grp} (n={n})")
    
    ax.axvline(0, ls='--', color='black', alpha=0.6, lw=1.5, label='CBAM launch (Jan 2, 2026)')
    ax.axhline(0, ls=':', color='gray', alpha=0.5)
    ax.set_xlabel("Trading days relative to CBAM definitive launch")
    ax.set_ylabel("Mean Cumulative Abnormal Return (%)")
    ax.set_title("CBAM event study: CAR by exposure group around 2 January 2026 launch")
    ax.legend(loc='best')
    ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(OUT / "figures/cbam_event_study.pdf")
    plt.close()
    print(f"\nFiguur: {OUT}/figures/cbam_event_study.pdf")

# Save summary table
summary_rows = []
for ev_name, ev_data in all_results.items():
    for grp, grp_data in ev_data['groups'].items():
        summary_rows.append({
            'event': ev_name,
            'group': grp,
            'CAR_end_pct': grp_data['mean_car'][-1] * 100,
            't_stat': grp_data['t_end'],
            'n_tickers': grp_data['n'],
        })
pd.DataFrame(summary_rows).to_csv(OUT / "cbam_event_study_summary.csv", index=False)
print(f"\nSummary tabel: {OUT}/cbam_event_study_summary.csv")
