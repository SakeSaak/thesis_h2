"""
24_paper_v3_robustness_battery.py

Complete robuustheidschecks voor Blue_CCS working paper v3, in respons op
reviewer feedback. Implementeert in een Python script:

  1. Cluster-robuuste standaardfouten (sponsor, sponsor x region)
  2. Cox proportional hazards model + Schoenfeld residual test
  3. Macro-financial interacties (Blue_CCS x gas, x carbon, x WUI)
  4. Entropy balancing (manual implementatie via scipy.optimize)
  5. Overlap visualisaties (PS density, Love plot, weight distribution)

Items 6 (Fine-Gray competing risks) en 7 (shared frailty) zitten in
separate R script (25_competing_risks_frailty.R) omdat die statistieken
robuuster zijn in R via cmprsk en survival packages.

Vereist: pip install lifelines
"""

from pathlib import Path
import re
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.neighbors import NearestNeighbors
from scipy.optimize import minimize
import matplotlib.pyplot as plt
warnings.filterwarnings("ignore")

try:
    from lifelines import CoxPHFitter
    from lifelines.statistics import proportional_hazard_test
    LIFELINES_AVAILABLE = True
except ImportError:
    print("WAARSCHUWING: lifelines niet geinstalleerd")
    print("  Installeer met: pip install lifelines")
    LIFELINES_AVAILABLE = False

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
IEA_FILE = PROJECT_ROOT / "data" / "raw" / "Hydrogen_projects_master_data_table_24-03-26.xlsx"
MASTER_PANEL = PROJECT_ROOT / "output_data" / "master_panel_daily.csv"
OUT = PROJECT_ROOT / "output_data"
FIGURES = PROJECT_ROOT / "figures"
FIGURES.mkdir(exist_ok=True)
CURRENT_YEAR = 2026

# ============================================================
# HELPERS
# ============================================================
def to_year_safe(x):
    if pd.isna(x): return np.nan
    try:
        v = float(x)
        if 1900 <= v <= 2100: return int(v)
    except: pass
    return np.nan

def parse_capacity_mw(row):
    cap = row.get("Electrolyzer capacity")
    unit = str(row.get("Electrolyzer capacity unit", "")).lower().strip()
    if pd.isna(cap): return np.nan
    try: val = float(cap)
    except:
        try: val = float(re.search(r"[\d.]+", str(cap)).group())
        except: return np.nan
    if "gigawatt" in unit: return val * 1000
    if "kilowatt" in unit: return val / 1000
    return val

def region_group(c):
    if pd.isna(c): return "Other"
    c = str(c).strip()
    eu27 = ["Netherlands","Germany","France","Spain","Denmark","Belgium","Italy",
             "Sweden","Finland","Portugal","Austria","Poland"]
    if any(e in c for e in eu27): return "EU"
    if c in ("United Kingdom","UK","Norway","Switzerland","Iceland"): return "Other_Europe"
    if c in ("United States","USA","Canada","Mexico"): return "North_America"
    if c in ("Japan","South Korea","China","India","Singapore","Taiwan"): return "Asia"
    if c in ("Australia","New Zealand"): return "ANZ"
    if c in ("Saudi Arabia","UAE","Oman","Qatar","Egypt","Morocco","Israel"): return "MENA"
    return "Other"

def tech_group(t):
    if pd.isna(t): return "Other"
    s = str(t).lower()
    if "pem" in s: return "PEM"
    if "alkaline" in s: return "Alkaline"
    if "ccs" in s: return "Blue_CCS"
    return "Other"

SPONSOR_MAP = {"shell":"Oil_major","bp":"Oil_major","totalenergies":"Oil_major","equinor":"Oil_major",
               "repsol":"Oil_major","eni":"Oil_major","aramco":"Oil_major","rwe":"Utility",
               "iberdrola":"Utility","orsted":"Utility","engie":"Utility","enel":"Utility",
               "air liquide":"Industrial_gas","air products":"Industrial_gas","linde":"Industrial_gas",
               "arcelormittal":"Steel","thyssenkrupp":"Steel","plug power":"Pure_play","nel":"Pure_play"}

def sponsor_type(s):
    if pd.isna(s): return "Unknown"
    s_low = str(s).lower().strip()
    for k, v in SPONSOR_MAP.items():
        if k in s_low: return v
    return "Other"

# ============================================================
# DATA OPBOUW
# ============================================================
print("=" * 70)
print("DEEL 1: DATA")
print("=" * 70)

iea = pd.read_excel(IEA_FILE, sheet_name="Export")
iea["project_status"] = iea["project_status"].astype(str).str.strip()
iea["year_announced"] = iea["Year announced"].apply(to_year_safe)
iea["year_online"] = iea["Date online"].apply(to_year_safe)
iea["capacity_mw"] = iea.apply(parse_capacity_mw, axis=1)
iea["log_capacity_mw"] = np.log1p(iea["capacity_mw"].fillna(0))
iea["region"] = iea["Geography"].apply(region_group)
iea["tech"] = iea["H2 Technology"].apply(tech_group)
iea["sponsor_type"] = iea["Primary owner"].apply(sponsor_type)
iea["sponsor_owner"] = iea["Primary owner"].fillna("Unknown")  # voor clustering

# Blue_CCS + PEM subset
df = iea[iea["tech"].isin(["Blue_CCS", "PEM"])].copy()
df = df.dropna(subset=["year_announced", "log_capacity_mw"])
df["is_blue_ccs"] = (df["tech"] == "Blue_CCS").astype(int)

ACTIVE_FAILURE = {"Plans cancelled", "On-hold (confirmed)"}
ON_HOLD = {"On-hold (confirmed)"}
CANCELLED = {"Plans cancelled"}
SUCCESS = {"Fully commissioned","Partially commissioned","Under construction",
           "Permitted","Financed"}

df["event_any"] = df["project_status"].isin(ACTIVE_FAILURE).astype(int)
df["event_cancelled"] = df["project_status"].isin(CANCELLED).astype(int)
df["event_onhold"] = df["project_status"].isin(ON_HOLD).astype(int)
df = df.reset_index(drop=True)
df["project_id"] = df.index
df["sponsor_region"] = df["sponsor_type"] + "_" + df["region"]

# Person-year panel met DUUR voor Cox
panel_rows = []
for idx, row in df.iterrows():
    status = row["project_status"]
    t_start = int(row["year_announced"])
    if status == "Decommissioned": continue
    t_online = row["year_online"] if pd.notna(row["year_online"]) and row["year_online"] >= t_start else CURRENT_YEAR
    t_online = int(min(t_online, CURRENT_YEAR + 5))
    if status in SUCCESS:
        t_end = min(t_online, CURRENT_YEAR); event_any = 0
        event_cancelled = 0; event_onhold = 0
    elif status in CANCELLED:
        target = min(t_online, CURRENT_YEAR)
        t_end = max(t_start, int((t_start + target) / 2))
        event_any = 1; event_cancelled = 1; event_onhold = 0
    elif status in ON_HOLD:
        target = min(t_online, CURRENT_YEAR)
        t_end = max(t_start, int((t_start + target) / 2))
        event_any = 1; event_cancelled = 0; event_onhold = 1
    else:
        t_end = CURRENT_YEAR; event_any = 0
        event_cancelled = 0; event_onhold = 0
    
    duration = max(1, t_end - t_start)
    
    for t in range(t_start, t_end + 1):
        panel_rows.append({
            "project_id": int(idx), "year_calendar": t,
            "year_since_start": t - t_start,
            "duration": duration,
            "event_any_yr": int((t == t_end) and event_any == 1),
            "event_cancelled_yr": int((t == t_end) and event_cancelled == 1),
            "event_onhold_yr": int((t == t_end) and event_onhold == 1),
            "is_blue_ccs": int(row["is_blue_ccs"]),
            "log_capacity_mw": row["log_capacity_mw"],
            "region": row["region"],
            "sponsor_type": row["sponsor_type"],
            "sponsor_owner": row["sponsor_owner"],
            "sponsor_region": row["sponsor_region"],
            "year_announced": t_start,
        })

panel = pd.DataFrame(panel_rows)
print(f"  Person-year panel: {len(panel)} rijen")
print(f"    events_any: {panel['event_any_yr'].sum()}")
print(f"    events_cancelled: {panel['event_cancelled_yr'].sum()}")
print(f"    events_onhold: {panel['event_onhold_yr'].sum()}")

# Bouw macro covariaten in panel
mp = pd.read_csv(MASTER_PANEL, index_col=0, parse_dates=True)
yearly_macro = mp.resample("YE").mean(numeric_only=True)
yearly_macro["year_calendar"] = yearly_macro.index.year
for c in ["eua","ttf_gas","VIXCLS","USEPUINDXD"]:
    if c in yearly_macro.columns:
        panel = panel.merge(yearly_macro[[c,"year_calendar"]], on="year_calendar", how="left")
        panel = panel.rename(columns={c: f"mkt_{c}"})

# Standardize macro vars voor interpretabel interactiemodel
for col in ["mkt_eua","mkt_ttf_gas","mkt_VIXCLS","mkt_USEPUINDXD"]:
    if col in panel.columns:
        panel[col] = panel[col].fillna(panel[col].median())
        panel[f"{col}_z"] = (panel[col] - panel[col].mean()) / panel[col].std()

# Project niveau ook standardize
df_proj = panel.groupby("project_id").first().reset_index()
df_proj["t_start"] = df_proj["year_announced"]
df_proj["t_end"] = df_proj["year_announced"] + df_proj["duration"]
df_proj["event_any"] = panel.groupby("project_id")["event_any_yr"].max().values
df_proj["event_cancelled"] = panel.groupby("project_id")["event_cancelled_yr"].max().values
df_proj["event_onhold"] = panel.groupby("project_id")["event_onhold_yr"].max().values

# ============================================================
# DEEL 2: CLUSTER-ROBUUSTE STANDAARDFOUTEN
# ============================================================
print("\n" + "=" * 70)
print("DEEL 2: CLUSTER-ROBUUSTE STANDAARDFOUTEN")
print("=" * 70)

# Hazard model
HAZARD_FORMULA = (
    "event_any_yr ~ is_blue_ccs + year_since_start + I(year_since_start**2) "
    "+ log_capacity_mw "
    "+ C(region, Treatment(reference='EU')) "
    "+ C(sponsor_type, Treatment(reference='Oil_major'))"
)

# Baseline GLM met iid SE
m_iid = smf.glm(HAZARD_FORMULA, data=panel, family=sm.families.Binomial()).fit()

# Cluster-robuuste SE op sponsor_owner niveau
m_cluster_sponsor = smf.glm(HAZARD_FORMULA, data=panel,
                              family=sm.families.Binomial()).fit(
    cov_type="cluster",
    cov_kwds={"groups": panel["sponsor_owner"]}
)

# Cluster-robuuste SE op sponsor_region niveau
m_cluster_sr = smf.glm(HAZARD_FORMULA, data=panel,
                         family=sm.families.Binomial()).fit(
    cov_type="cluster",
    cov_kwds={"groups": panel["sponsor_region"]}
)

print(f"\n  Blue_CCS coefficient onder verschillende clustering:")
print(f"    IID SE:                    coef={m_iid.params['is_blue_ccs']:.3f}, "
       f"SE={m_iid.bse['is_blue_ccs']:.3f}, p={m_iid.pvalues['is_blue_ccs']:.4f}")
print(f"    Cluster sponsor_owner:     coef={m_cluster_sponsor.params['is_blue_ccs']:.3f}, "
       f"SE={m_cluster_sponsor.bse['is_blue_ccs']:.3f}, "
       f"p={m_cluster_sponsor.pvalues['is_blue_ccs']:.4f}")
print(f"    Cluster sponsor_region:    coef={m_cluster_sr.params['is_blue_ccs']:.3f}, "
       f"SE={m_cluster_sr.bse['is_blue_ccs']:.3f}, "
       f"p={m_cluster_sr.pvalues['is_blue_ccs']:.4f}")

# Vergelijkingstabel
cluster_comparison = pd.DataFrame({
    "variable": m_iid.params.index,
    "coef": m_iid.params.values,
    "SE_iid": m_iid.bse.values,
    "SE_cluster_sponsor": m_cluster_sponsor.bse.values,
    "SE_cluster_sr": m_cluster_sr.bse.values,
    "p_iid": m_iid.pvalues.values,
    "p_cluster_sponsor": m_cluster_sponsor.pvalues.values,
    "p_cluster_sr": m_cluster_sr.pvalues.values,
})
cluster_comparison["SE_inflation_sponsor"] = (
    cluster_comparison["SE_cluster_sponsor"] / cluster_comparison["SE_iid"]
)

# ============================================================
# DEEL 3: COX PROPORTIONAL HAZARDS
# ============================================================
print("\n" + "=" * 70)
print("DEEL 3: COX PROPORTIONAL HAZARDS MET SCHOENFELD TEST")
print("=" * 70)

if LIFELINES_AVAILABLE:
    # Build project-level data with duration
    df_cox = df_proj[[
        "project_id", "duration", "event_any", "is_blue_ccs",
        "log_capacity_mw", "region", "sponsor_type", "sponsor_owner"
    ]].copy()
    
    # Encode categorical variables
    df_cox = pd.get_dummies(df_cox,
        columns=["region", "sponsor_type"],
        prefix=["region", "sp"],
        drop_first=True)
    
    cph = CoxPHFitter(penalizer=0.001)  # tiny penalisation for stability
    cox_vars = ["is_blue_ccs", "log_capacity_mw"] + [
        c for c in df_cox.columns if c.startswith("region_") or c.startswith("sp_")
    ]
    
    try:
        cph.fit(
            df_cox[["duration", "event_any"] + cox_vars],
            duration_col="duration",
            event_col="event_any",
            cluster_col=None,
            robust=False
        )
        print(f"\n  Cox PH model: n={len(df_cox)}, events={int(df_cox['event_any'].sum())}")
        print(f"    Concordance: {cph.concordance_index_:.3f}")
        print(f"    Partial LL: {cph.log_likelihood_:.2f}")
        print(f"    Blue_CCS HR: {np.exp(cph.params_['is_blue_ccs']):.2f} "
               f"(95% CI: [{np.exp(cph.confidence_intervals_.loc['is_blue_ccs', '95% lower-bound']):.2f}, "
               f"{np.exp(cph.confidence_intervals_.loc['is_blue_ccs', '95% upper-bound']):.2f}])")
        print(f"    Blue_CCS coef: {cph.params_['is_blue_ccs']:.3f}, "
               f"SE: {cph.standard_errors_['is_blue_ccs']:.3f}, "
               f"p: {cph.summary.loc['is_blue_ccs', 'p']:.4f}")
        
        # Schoenfeld residual test
        ph_test = proportional_hazard_test(cph,
                                            df_cox[["duration", "event_any"] + cox_vars],
                                            time_transform="rank")
        print(f"\n  Schoenfeld proportional hazards test (rank transform):")
        for var in ["is_blue_ccs", "log_capacity_mw"]:
            if var in ph_test.summary.index:
                p_ph = ph_test.summary.loc[var, "p"]
                violation = "PH ASSUMPTION VIOLATED" if p_ph < 0.05 else "OK"
                print(f"    {var}: p={p_ph:.4f} -> {violation}")
        
        global_p = ph_test.summary.loc["TOTAL", "p"] if "TOTAL" in ph_test.summary.index else np.nan
        print(f"    Global PH test: p={global_p:.4f}")
        
        cox_results = {
            "blue_ccs_hr": float(np.exp(cph.params_["is_blue_ccs"])),
            "blue_ccs_coef": float(cph.params_["is_blue_ccs"]),
            "blue_ccs_se": float(cph.standard_errors_["is_blue_ccs"]),
            "blue_ccs_p": float(cph.summary.loc["is_blue_ccs", "p"]),
            "concordance": float(cph.concordance_index_),
            "ph_test_global_p": float(global_p) if not pd.isna(global_p) else None,
        }
    except Exception as e:
        print(f"  Cox fit gefaald: {e}")
        cox_results = None
else:
    cox_results = None

# ============================================================
# DEEL 4: MACRO-FINANCIAL INTERACTIES
# ============================================================
print("\n" + "=" * 70)
print("DEEL 4: MACRO-FINANCIAL INTERACTIES")
print("=" * 70)

# Vier interactiemodellen
interaction_models = {}

# Blue_CCS x gas prijs
panel["blue_x_gas"] = panel["is_blue_ccs"] * panel["mkt_ttf_gas_z"]
FORMULA_GAS = (
    "event_any_yr ~ is_blue_ccs + mkt_ttf_gas_z + blue_x_gas "
    "+ year_since_start + I(year_since_start**2) + log_capacity_mw "
    "+ C(region, Treatment(reference='EU')) "
    "+ C(sponsor_type, Treatment(reference='Oil_major'))"
)
try:
    m_int_gas = smf.glm(FORMULA_GAS, data=panel, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": panel["sponsor_owner"]}
    )
    interaction_models["gas"] = m_int_gas
    print(f"\n  Blue_CCS x gas_price:")
    print(f"    blue main:       coef={m_int_gas.params['is_blue_ccs']:.3f}, "
           f"p={m_int_gas.pvalues['is_blue_ccs']:.4f}")
    print(f"    gas main:        coef={m_int_gas.params['mkt_ttf_gas_z']:.3f}, "
           f"p={m_int_gas.pvalues['mkt_ttf_gas_z']:.4f}")
    print(f"    interaction:     coef={m_int_gas.params['blue_x_gas']:.3f}, "
           f"p={m_int_gas.pvalues['blue_x_gas']:.4f}")
except Exception as e:
    print(f"  Gas interactie gefaald: {e}")

# Blue_CCS x carbon (EUA z)
panel["blue_x_eua"] = panel["is_blue_ccs"] * panel["mkt_eua_z"]
FORMULA_CARBON = FORMULA_GAS.replace("ttf_gas", "eua").replace("blue_x_gas", "blue_x_eua")
try:
    m_int_eua = smf.glm(FORMULA_CARBON, data=panel, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": panel["sponsor_owner"]}
    )
    interaction_models["eua"] = m_int_eua
    print(f"\n  Blue_CCS x EUA carbon price:")
    print(f"    blue main:       coef={m_int_eua.params['is_blue_ccs']:.3f}, "
           f"p={m_int_eua.pvalues['is_blue_ccs']:.4f}")
    print(f"    eua main:        coef={m_int_eua.params['mkt_eua_z']:.3f}, "
           f"p={m_int_eua.pvalues['mkt_eua_z']:.4f}")
    print(f"    interaction:     coef={m_int_eua.params['blue_x_eua']:.3f}, "
           f"p={m_int_eua.pvalues['blue_x_eua']:.4f}")
except Exception as e:
    print(f"  EUA interactie gefaald: {e}")

# Blue_CCS x VIX (financial uncertainty)
panel["blue_x_vix"] = panel["is_blue_ccs"] * panel["mkt_VIXCLS_z"]
FORMULA_VIX = FORMULA_GAS.replace("ttf_gas", "VIXCLS").replace("blue_x_gas", "blue_x_vix")
try:
    m_int_vix = smf.glm(FORMULA_VIX, data=panel, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": panel["sponsor_owner"]}
    )
    interaction_models["vix"] = m_int_vix
    print(f"\n  Blue_CCS x VIX:")
    print(f"    interaction:     coef={m_int_vix.params['blue_x_vix']:.3f}, "
           f"p={m_int_vix.pvalues['blue_x_vix']:.4f}")
except Exception as e:
    print(f"  VIX interactie gefaald: {e}")

# Blue_CCS x EPU
panel["blue_x_epu"] = panel["is_blue_ccs"] * panel["mkt_USEPUINDXD_z"]
FORMULA_EPU = FORMULA_GAS.replace("ttf_gas", "USEPUINDXD").replace("blue_x_gas", "blue_x_epu")
try:
    m_int_epu = smf.glm(FORMULA_EPU, data=panel, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": panel["sponsor_owner"]}
    )
    interaction_models["epu"] = m_int_epu
    print(f"\n  Blue_CCS x EPU:")
    print(f"    interaction:     coef={m_int_epu.params['blue_x_epu']:.3f}, "
           f"p={m_int_epu.pvalues['blue_x_epu']:.4f}")
except Exception as e:
    print(f"  EPU interactie gefaald: {e}")

# ============================================================
# DEEL 5: ENTROPY BALANCING
# ============================================================
print("\n" + "=" * 70)
print("DEEL 5: ENTROPY BALANCING")
print("=" * 70)
print("  Hainmueller (2012). Vindt gewichten voor control die exact balanceren")
print("  op gespecificeerde moments van de treated covariaten.")

# Project niveau voor entropy balancing
df_eb = df_proj.copy()

# Bouw covariaat matrix
eb_vars = ["log_capacity_mw", "year_announced"]
region_dummies = pd.get_dummies(df_eb["region"], prefix="region", drop_first=True)
sponsor_dummies = pd.get_dummies(df_eb["sponsor_type"], prefix="sp", drop_first=True)
X_eb = pd.concat([df_eb[eb_vars].reset_index(drop=True), region_dummies, sponsor_dummies], axis=1)
T = df_eb["is_blue_ccs"].values.astype(int)

X_treated = X_eb[T == 1].values
X_control = X_eb[T == 0].values

# Target moments: gemiddelde van treated
target_means = X_treated.mean(axis=0)

# Entropy balancing optimalisatie
# Vind gewichten w op control zodat:
#   - sum(w) = n_control
#   - sum(w * X_control) / sum(w) = target_means
# Maximaliseer entropie: -sum(w * log(w/q)) waar q = 1 (uniform start)

n_control = X_control.shape[0]
K = X_control.shape[1]

def neg_entropy_balance_loss(lam, X_c, target_m):
    """Dual formulation: minimize over lam"""
    # Gewichten: w_i = exp(lam @ X_c[i])
    lin = X_c @ lam
    lin = lin - lin.max()  # numerical stability
    w = np.exp(lin)
    Z = w.sum()
    w = w / Z * len(w)  # normalize to sum = n_control
    
    # Constraint violation
    moments = (w[:, None] * X_c).sum(axis=0) / w.sum() * len(w)
    moments_normalized = moments / len(w)  # mean
    violation = moments_normalized - target_m
    
    return 0.5 * np.sum(violation**2)


# Eenvoudige iterative scaling (Newton-Raphson would be better)
# Initialize: lam = 0
lam0 = np.zeros(K)
result = minimize(neg_entropy_balance_loss, lam0,
                    args=(X_control, target_means),
                    method="L-BFGS-B",
                    options={"maxiter": 500, "ftol": 1e-10})

lam_hat = result.x
lin = X_control @ lam_hat
lin = lin - lin.max()
w_eb = np.exp(lin)
w_eb = w_eb / w_eb.sum() * n_control  # gewichten op control

# Check balance
balanced_means = (w_eb[:, None] * X_control).sum(axis=0) / w_eb.sum()
imbalance = np.abs(balanced_means - target_means).max()
print(f"\n  Entropy balancing convergence: {result.success}")
print(f"    Max moment imbalance: {imbalance:.5f}")
print(f"    Max weight: {w_eb.max():.3f}")
print(f"    Min weight: {w_eb.min():.5f}")
print(f"    Effective sample size: {w_eb.sum()**2 / (w_eb**2).sum():.0f}")

# Build weighted panel: treated weight 1, control weight w_eb
df_eb["eb_weight"] = 1.0
control_idx = df_eb.index[T == 0].tolist()
df_eb.loc[control_idx, "eb_weight"] = w_eb

# Merge weights into person-year panel
panel = panel.merge(df_eb[["project_id", "eb_weight"]], on="project_id", how="left")
panel["eb_weight"] = panel["eb_weight"].fillna(1.0)

# Fit hazard met entropy balancing gewichten
try:
    m_eb = smf.glm(HAZARD_FORMULA, data=panel,
                     family=sm.families.Binomial(),
                     freq_weights=panel["eb_weight"]).fit(
        cov_type="cluster", cov_kwds={"groups": panel["sponsor_owner"]}
    )
    print(f"\n  Entropy balancing weighted hazard:")
    print(f"    Blue_CCS coef: {m_eb.params['is_blue_ccs']:.3f}")
    print(f"    Blue_CCS HR:   {np.exp(m_eb.params['is_blue_ccs']):.2f}")
    print(f"    SE (cluster):  {m_eb.bse['is_blue_ccs']:.3f}")
    print(f"    p:             {m_eb.pvalues['is_blue_ccs']:.4f}")
except Exception as e:
    print(f"  EB hazard fit gefaald: {e}")
    m_eb = None

# ============================================================
# DEEL 6: OVERLAP VISUALISATIES
# ============================================================
print("\n" + "=" * 70)
print("DEEL 6: OVERLAP VISUALISATIES")
print("=" * 70)

# Bereken propensity scores nogmaals voor visualisaties
ps_formula = (
    "is_blue_ccs ~ log_capacity_mw + year_announced "
    "+ C(region, Treatment(reference='EU')) "
    "+ C(sponsor_type, Treatment(reference='Oil_major'))"
)
ps_model = smf.glm(ps_formula, data=df_proj, family=sm.families.Binomial()).fit()
df_proj["ps"] = ps_model.predict(df_proj)

# Plot 1: PS density by treatment
fig, ax = plt.subplots(figsize=(9, 5))
ps_blue = df_proj[df_proj["is_blue_ccs"] == 1]["ps"]
ps_pem = df_proj[df_proj["is_blue_ccs"] == 0]["ps"]
ax.hist(ps_blue, bins=30, alpha=0.6, color="#C00000", label="Blue_CCS (n=%d)" % len(ps_blue),
         density=True)
ax.hist(ps_pem, bins=30, alpha=0.6, color="#2E75B6", label="PEM (n=%d)" % len(ps_pem),
         density=True)
ax.set_xlabel("Propensity Score Pr(Blue_CCS | X)")
ax.set_ylabel("Density")
ax.set_title("Propensity Score Distributions: Limited Overlap Reveals Segmented Ecosystems")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(FIGURES / "fig_ps_density.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved: fig_ps_density.png")

# Plot 2: Common support histogram
fig, ax = plt.subplots(figsize=(9, 5))
common_low = max(ps_blue.min(), ps_pem.min())
common_high = min(ps_blue.max(), ps_pem.max())
ax.hist(ps_blue, bins=30, alpha=0.7, color="#C00000", label="Blue_CCS")
ax.hist(ps_pem, bins=30, alpha=0.7, color="#2E75B6", label="PEM")
ax.axvspan(common_low, common_high, color="green", alpha=0.15, label="Common support")
ax.set_xlabel("Propensity Score")
ax.set_ylabel("Count")
ax.set_title(f"Common Support: [{common_low:.3f}, {common_high:.3f}] — Narrow Overlap Zone")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(FIGURES / "fig_common_support.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved: fig_common_support.png")

# Plot 3: Love plot voor SMDs before/after matching
# Compute SMDs for matched and unmatched
def smd(t, c):
    return (t.mean() - c.mean()) / np.sqrt((t.var(ddof=1) + c.var(ddof=1)) / 2 + 1e-12)

# Match for love plot (replicate 22b matching)
support_mask = (df_proj["ps"] >= common_low) & (df_proj["ps"] <= common_high)
df_support = df_proj[support_mask].copy().reset_index(drop=True)
blue_s = df_support[df_support["is_blue_ccs"]==1].reset_index(drop=True)
pem_s = df_support[df_support["is_blue_ccs"]==0].reset_index(drop=True)
nn = NearestNeighbors(n_neighbors=1)
nn.fit(pem_s[["ps"]].values)
distances, indices = nn.kneighbors(blue_s[["ps"]].values)
within = distances.flatten() <= 0.05
matched_pem = pem_s.iloc[indices.flatten()[within]].copy()
matched_blue = blue_s.iloc[within].copy()

balance_vars = ["log_capacity_mw", "year_announced", "ps"]
for r in ["Asia", "North_America", "MENA", "EU"]:
    df_proj[f"region_{r}"] = (df_proj["region"] == r).astype(float)
    blue_s[f"region_{r}"] = (blue_s["region"] == r).astype(float)
    pem_s[f"region_{r}"] = (pem_s["region"] == r).astype(float)
    matched_blue[f"region_{r}"] = (matched_blue["region"] == r).astype(float)
    matched_pem[f"region_{r}"] = (matched_pem["region"] == r).astype(float)
    balance_vars.append(f"region_{r}")
for s in ["Oil_major", "Utility", "Pure_play", "Industrial_gas"]:
    df_proj[f"sp_{s}"] = (df_proj["sponsor_type"] == s).astype(float)
    blue_s[f"sp_{s}"] = (blue_s["sponsor_type"] == s).astype(float)
    pem_s[f"sp_{s}"] = (pem_s["sponsor_type"] == s).astype(float)
    matched_blue[f"sp_{s}"] = (matched_blue["sponsor_type"] == s).astype(float)
    matched_pem[f"sp_{s}"] = (matched_pem["sponsor_type"] == s).astype(float)
    balance_vars.append(f"sp_{s}")

smd_before = [smd(blue_s[v], pem_s[v]) for v in balance_vars]
smd_after = [smd(matched_blue[v], matched_pem[v]) for v in balance_vars]

fig, ax = plt.subplots(figsize=(8, 7))
y = np.arange(len(balance_vars))
ax.scatter(smd_before, y, color="#C00000", label="Before matching", s=50)
ax.scatter(smd_after, y, color="#2E75B6", label="After matching", s=50)
for i in range(len(balance_vars)):
    ax.plot([smd_before[i], smd_after[i]], [i, i], color="gray", lw=0.5, alpha=0.5)
ax.axvline(0, color="black", lw=0.5)
ax.axvline(0.1, color="green", linestyle="--", lw=0.5, alpha=0.5)
ax.axvline(-0.1, color="green", linestyle="--", lw=0.5, alpha=0.5)
ax.axvline(0.25, color="orange", linestyle="--", lw=0.5, alpha=0.5)
ax.axvline(-0.25, color="orange", linestyle="--", lw=0.5, alpha=0.5)
ax.set_yticks(y)
ax.set_yticklabels(balance_vars)
ax.set_xlabel("Standardised Mean Difference")
ax.set_title("Love Plot: Covariate Balance Before vs After Matching")
ax.legend()
ax.grid(alpha=0.3, axis="x")
plt.tight_layout()
plt.savefig(FIGURES / "fig_love_plot.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved: fig_love_plot.png")

# Plot 4: Weight distribution (IPW + EB)
ps_trimmed = df_proj["ps"].clip(0.05, 0.95)
T_arr = df_proj["is_blue_ccs"].values
p_marg = T_arr.mean()
ipw_weights = np.where(T_arr == 1, p_marg / ps_trimmed, (1 - p_marg) / (1 - ps_trimmed))
eb_weights_full = np.ones(len(df_proj))
ctrl_idx = np.where(T_arr == 0)[0]
eb_weights_full[ctrl_idx] = w_eb[:len(ctrl_idx)] if len(w_eb) >= len(ctrl_idx) else 1.0

fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
ax = axes[0]
ax.hist(ipw_weights[T_arr==0], bins=40, alpha=0.7, color="#2E75B6", label="PEM IPW weights")
ax.hist(ipw_weights[T_arr==1], bins=40, alpha=0.7, color="#C00000", label="Blue_CCS IPW weights")
ax.set_xlabel("Stabilised IPW weight")
ax.set_ylabel("Count")
ax.set_title("IPW Weight Distribution")
ax.legend(); ax.grid(alpha=0.3)

ax = axes[1]
ax.hist(eb_weights_full[T_arr==0], bins=40, alpha=0.7, color="#2E75B6",
        label="PEM EB weights")
ax.set_xlabel("Entropy Balancing weight")
ax.set_ylabel("Count")
ax.set_title("Entropy Balancing Weight Distribution")
ax.legend(); ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(FIGURES / "fig_weight_distributions.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved: fig_weight_distributions.png")

# ============================================================
# DEEL 7: EXCEL OUTPUT
# ============================================================
print("\n" + "=" * 70)
print("EXCEL OUTPUT")
print("=" * 70)

xlsx_path = OUT / "24_paper_v3_robustness.xlsx"
with pd.ExcelWriter(xlsx_path, engine="openpyxl") as w:
    cluster_comparison.to_excel(w, sheet_name="Cluster SE comparison", index=False)
    
    # Interactie samenvatting
    if interaction_models:
        int_rows = []
        for name, m in interaction_models.items():
            int_var = f"blue_x_{name}"
            if int_var in m.params.index:
                int_rows.append({
                    "interaction": name,
                    "blue_main_coef": m.params["is_blue_ccs"],
                    "blue_main_p": m.pvalues["is_blue_ccs"],
                    "interaction_coef": m.params[int_var],
                    "interaction_se": m.bse[int_var],
                    "interaction_p": m.pvalues[int_var],
                })
        if int_rows:
            pd.DataFrame(int_rows).to_excel(w, sheet_name="Macro Interactions", index=False)
    
    # Methode samenvatting
    summary_rows = []
    summary_rows.append({"method": "GLM iid SE",
                          "blue_ccs_coef": m_iid.params["is_blue_ccs"],
                          "blue_ccs_hr": float(np.exp(m_iid.params["is_blue_ccs"])),
                          "se": m_iid.bse["is_blue_ccs"],
                          "p": m_iid.pvalues["is_blue_ccs"]})
    summary_rows.append({"method": "GLM cluster sponsor",
                          "blue_ccs_coef": m_cluster_sponsor.params["is_blue_ccs"],
                          "blue_ccs_hr": float(np.exp(m_cluster_sponsor.params["is_blue_ccs"])),
                          "se": m_cluster_sponsor.bse["is_blue_ccs"],
                          "p": m_cluster_sponsor.pvalues["is_blue_ccs"]})
    summary_rows.append({"method": "GLM cluster sponsor x region",
                          "blue_ccs_coef": m_cluster_sr.params["is_blue_ccs"],
                          "blue_ccs_hr": float(np.exp(m_cluster_sr.params["is_blue_ccs"])),
                          "se": m_cluster_sr.bse["is_blue_ccs"],
                          "p": m_cluster_sr.pvalues["is_blue_ccs"]})
    if cox_results:
        summary_rows.append({"method": "Cox PH",
                              "blue_ccs_coef": cox_results["blue_ccs_coef"],
                              "blue_ccs_hr": cox_results["blue_ccs_hr"],
                              "se": cox_results["blue_ccs_se"],
                              "p": cox_results["blue_ccs_p"]})
    if m_eb is not None:
        summary_rows.append({"method": "Entropy Balancing",
                              "blue_ccs_coef": m_eb.params["is_blue_ccs"],
                              "blue_ccs_hr": float(np.exp(m_eb.params["is_blue_ccs"])),
                              "se": m_eb.bse["is_blue_ccs"],
                              "p": m_eb.pvalues["is_blue_ccs"]})
    pd.DataFrame(summary_rows).to_excel(w, sheet_name="All methods summary", index=False)
    
    pd.DataFrame([
        ["COMPREHENSIVE ROBUSTNESS BATTERY voor PAPER v3"],
        [""],
        ["Implementaties:"],
        ["1. Cluster-robust SE (sponsor + sponsor x region)"],
        [f"2. Cox PH + Schoenfeld test ({'OK' if cox_results else 'FAILED'})"],
        ["3. Macro-financial interacties (gas, eua, vix, epu)"],
        ["4. Entropy balancing"],
        ["5. Overlap visualisaties (4 PNG bestanden)"],
        [""],
        ["NIET in dit script (zie 25_competing_risks_frailty.R):"],
        ["6. Fine-Gray competing risks"],
        ["7. Shared frailty Cox"],
        [""],
        ["Volgende stap: integreer alle resultaten in paper v3"],
    ], columns=["Description"]).to_excel(w, sheet_name="README", index=False)

print(f"  Excel: {xlsx_path}")
print(f"  Figures: {FIGURES}")
print("\nKLAAR. Volg op met R script voor competing risks en frailty.")
