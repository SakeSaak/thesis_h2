"""
28_overlap_visualisations.py

Standalone script dat de vier overlap-diagnostiek figures genereert die
in de paper gerefereerd worden:
  - fig_ps_density.png       (Figure A1 in paper, Sectie 3.2)
  - fig_common_support.png   (Appendix A2)
  - fig_love_plot.png        (Sectie 3.3)
  - fig_weight_distributions.png  (diagnostic)

Deze scheef DEEL 6 van script 24 maar als zelfstandig script,
zodat het niet afhangt van DEEL 5 (entropy balancing) die crashte.

Run:
    python 28_overlap_visualisations.py
"""

from pathlib import Path
import re
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors

warnings.filterwarnings("ignore")

# ============================================================
# CONFIG
# ============================================================
PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
IEA_FILE = PROJECT_ROOT / "data" / "raw" / "Hydrogen_projects_master_data_table_24-03-26.xlsx"
FIGURES = PROJECT_ROOT / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATA HELPERS (identiek aan script 24)
# ============================================================
def to_year_safe(x):
    if pd.isna(x):
        return np.nan
    try:
        v = float(x)
        if 1900 <= v <= 2100:
            return int(v)
    except Exception:
        pass
    return np.nan


def parse_capacity_mw(row):
    cap = row.get("Electrolyzer capacity")
    unit = str(row.get("Electrolyzer capacity unit", "")).lower().strip()
    if pd.isna(cap):
        return np.nan
    try:
        val = float(cap)
    except Exception:
        try:
            val = float(re.search(r"[\d.]+", str(cap)).group())
        except Exception:
            return np.nan
    if "gigawatt" in unit:
        return val * 1000
    if "kilowatt" in unit:
        return val / 1000
    return val


def region_group(c):
    if pd.isna(c):
        return "Other"
    c = str(c).strip()
    eu27 = ["Netherlands", "Germany", "France", "Spain", "Denmark", "Belgium",
            "Italy", "Sweden", "Finland", "Portugal", "Austria", "Poland"]
    if any(e in c for e in eu27):
        return "EU"
    if c in ("United Kingdom", "UK", "Norway", "Switzerland", "Iceland"):
        return "Other_Europe"
    if c in ("United States", "USA", "Canada", "Mexico"):
        return "North_America"
    if c in ("Japan", "South Korea", "China", "India", "Singapore", "Taiwan"):
        return "Asia"
    if c in ("Australia", "New Zealand"):
        return "ANZ"
    if c in ("Saudi Arabia", "UAE", "Oman", "Qatar", "Egypt", "Morocco", "Israel"):
        return "MENA"
    return "Other"


def tech_group(t):
    if pd.isna(t):
        return "Other"
    s = str(t).lower()
    if "pem" in s:
        return "PEM"
    if "alkaline" in s:
        return "Alkaline"
    if "ccs" in s:
        return "Blue_CCS"
    return "Other"


SPONSOR_MAP = {
    "shell": "Oil_major", "bp": "Oil_major", "totalenergies": "Oil_major",
    "equinor": "Oil_major", "repsol": "Oil_major", "eni": "Oil_major",
    "aramco": "Oil_major", "rwe": "Utility", "iberdrola": "Utility",
    "orsted": "Utility", "engie": "Utility", "enel": "Utility",
    "air liquide": "Industrial_gas", "air products": "Industrial_gas",
    "linde": "Industrial_gas", "arcelormittal": "Steel", "thyssenkrupp": "Steel",
    "plug power": "Pure_play", "nel": "Pure_play",
}


def sponsor_type(s):
    if pd.isna(s):
        return "Unknown"
    s_low = str(s).lower().strip()
    for k, v in SPONSOR_MAP.items():
        if k in s_low:
            return v
    return "Other"


# ============================================================
# DATA OPBOUW
# ============================================================
print("=" * 70)
print("DATA OPBOUW VOOR OVERLAP DIAGNOSTICS")
print("=" * 70)

iea = pd.read_excel(IEA_FILE, sheet_name="Export")
iea["project_status"] = iea["project_status"].astype(str).str.strip()
iea["year_announced"] = iea["Year announced"].apply(to_year_safe)
iea["capacity_mw"] = iea.apply(parse_capacity_mw, axis=1)
iea["log_capacity_mw"] = np.log1p(iea["capacity_mw"].fillna(0))
iea["region"] = iea["Geography"].apply(region_group)

# Tech-kolom: probeer "H2 Technology" eerst, val terug op "Technology"
tech_col = "H2 Technology" if "H2 Technology" in iea.columns else "Technology"
iea["tech"] = iea[tech_col].apply(tech_group)
iea["sponsor_type"] = iea["Primary owner"].apply(sponsor_type)
iea["sponsor_owner"] = iea["Primary owner"].fillna("Unknown").astype(str)

df_proj = iea[iea["tech"].isin(["Blue_CCS", "PEM"])].copy()
df_proj = df_proj.dropna(subset=["year_announced", "log_capacity_mw"])
df_proj = df_proj[df_proj["project_status"] != "Decommissioned"].copy()
df_proj["is_blue_ccs"] = (df_proj["tech"] == "Blue_CCS").astype(int)
df_proj = df_proj.reset_index(drop=True)

n_blue = int(df_proj["is_blue_ccs"].sum())
n_pem = int((1 - df_proj["is_blue_ccs"]).sum())
print(f"  Projecten: {len(df_proj)} totaal ({n_blue} Blue_CCS, {n_pem} PEM)")

# ============================================================
# PROPENSITY SCORE FIT
# ============================================================
print("\n" + "=" * 70)
print("PROPENSITY SCORE FIT")
print("=" * 70)

ps_formula = (
    "is_blue_ccs ~ log_capacity_mw + year_announced "
    "+ C(region, Treatment(reference='EU')) "
    "+ C(sponsor_type, Treatment(reference='Oil_major'))"
)
ps_model = smf.glm(ps_formula, data=df_proj, family=sm.families.Binomial()).fit()
df_proj["ps"] = ps_model.predict(df_proj)

# McFadden pseudo R-squared
ll_full = ps_model.llf
ps_null = smf.glm("is_blue_ccs ~ 1", data=df_proj, family=sm.families.Binomial()).fit()
ll_null = ps_null.llf
mcfadden_r2 = 1 - ll_full / ll_null
print(f"  McFadden pseudo-R^2: {mcfadden_r2:.3f}")
print(f"  PS range Blue_CCS: [{df_proj.loc[df_proj['is_blue_ccs']==1,'ps'].min():.3f}, "
      f"{df_proj.loc[df_proj['is_blue_ccs']==1,'ps'].max():.3f}], "
      f"median {df_proj.loc[df_proj['is_blue_ccs']==1,'ps'].median():.3f}")
print(f"  PS range PEM:      [{df_proj.loc[df_proj['is_blue_ccs']==0,'ps'].min():.3f}, "
      f"{df_proj.loc[df_proj['is_blue_ccs']==0,'ps'].max():.3f}], "
      f"median {df_proj.loc[df_proj['is_blue_ccs']==0,'ps'].median():.3f}")

ps_blue = df_proj[df_proj["is_blue_ccs"] == 1]["ps"]
ps_pem = df_proj[df_proj["is_blue_ccs"] == 0]["ps"]

# ============================================================
# FIGUUR 1: PS DENSITY
# ============================================================
print("\n" + "=" * 70)
print("FIGUUR 1: PS DENSITY")
print("=" * 70)

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.hist(ps_blue, bins=30, alpha=0.65, color="#C00000",
        label=f"Blue_CCS (n={len(ps_blue)})", density=True,
        edgecolor="darkred", linewidth=0.5)
ax.hist(ps_pem, bins=30, alpha=0.65, color="#2E75B6",
        label=f"PEM (n={len(ps_pem)})", density=True,
        edgecolor="darkblue", linewidth=0.5)
ax.set_xlabel("Propensity Score  Pr(Blue_CCS | X)", fontsize=11)
ax.set_ylabel("Density", fontsize=11)
ax.set_title(
    f"Propensity Score Distributions: Limited Overlap Reveals Segmented Ecosystems\n"
    f"McFadden pseudo-$R^2$ = {mcfadden_r2:.3f}",
    fontsize=11,
)
ax.legend(loc="upper center", fontsize=10)
ax.grid(alpha=0.3)
plt.tight_layout()
out1 = FIGURES / "fig_ps_density.png"
plt.savefig(out1, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved: {out1}")

# ============================================================
# FIGUUR 2: COMMON SUPPORT (DENSE OVERLAP ZONE)
# ============================================================
print("\n" + "=" * 70)
print("FIGUUR 2: COMMON SUPPORT")
print("=" * 70)

# Strikte common support (maximaal interval) - meestal te ruim
strict_low = max(ps_blue.min(), ps_pem.min())
strict_high = min(ps_blue.max(), ps_pem.max())

# Dense overlap zone: 5e-95e percentiel van beide groups, intersectie
blue_p05, blue_p95 = ps_blue.quantile([0.05, 0.95])
pem_p05, pem_p95 = ps_pem.quantile([0.05, 0.95])
dense_low = max(blue_p05, pem_p05)
dense_high = min(blue_p95, pem_p95)

# Fractie observaties die IN de dense overlap zone vallen
in_dense_blue = ((ps_blue >= dense_low) & (ps_blue <= dense_high)).mean()
in_dense_pem = ((ps_pem >= dense_low) & (ps_pem <= dense_high)).mean()

print(f"  Strikte common support: [{strict_low:.3f}, {strict_high:.3f}] (width {strict_high-strict_low:.3f})")
print(f"  Dense overlap (5-95%):  [{dense_low:.3f}, {dense_high:.3f}] (width {dense_high-dense_low:.3f})")
print(f"  Blue_CCS in dense zone: {in_dense_blue:.1%}")
print(f"  PEM in dense zone:      {in_dense_pem:.1%}")

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.hist(ps_blue, bins=30, alpha=0.75, color="#C00000", label="Blue_CCS",
        edgecolor="darkred", linewidth=0.5)
ax.hist(ps_pem, bins=30, alpha=0.75, color="#2E75B6", label="PEM",
        edgecolor="darkblue", linewidth=0.5)
if dense_high > dense_low:
    ax.axvspan(dense_low, dense_high, color="green", alpha=0.22,
               label=f"Dense overlap (5--95th pctile): [{dense_low:.2f}, {dense_high:.2f}]")
else:
    # Empty intersection — no dense overlap
    ax.axvline((dense_low + dense_high) / 2, color="green", linestyle="--",
               label="No dense overlap (5--95th pctile intervals disjoint)")
ax.set_xlabel("Propensity Score", fontsize=11)
ax.set_ylabel("Count", fontsize=11)
title_suffix = (
    f"Strict common support [{strict_low:.2f}, {strict_high:.2f}] is wide, "
    f"but only {in_dense_blue:.0%} of Blue_CCS and {in_dense_pem:.0%} of PEM\n"
    f"fall in the dense overlap zone -- bimodal distributions with sparse middle"
)
ax.set_title(f"Common Support Diagnostic\n{title_suffix}", fontsize=10.5)
ax.legend(loc="upper center", fontsize=9.5)
ax.grid(alpha=0.3)
plt.tight_layout()
out2 = FIGURES / "fig_common_support.png"
plt.savefig(out2, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved: {out2}")

# Aliases voor love plot sectie (verwacht common_low/common_high)
common_low = strict_low
common_high = strict_high

# ============================================================
# FIGUUR 3: LOVE PLOT (SMDs BEFORE/AFTER MATCHING)
# ============================================================
print("\n" + "=" * 70)
print("FIGUUR 3: LOVE PLOT")
print("=" * 70)

def smd(t, c):
    return (t.mean() - c.mean()) / np.sqrt(
        (t.var(ddof=1) + c.var(ddof=1)) / 2 + 1e-12
    )

# 1-to-1 nearest neighbour matching binnen common support, caliper 0.05
support_mask = (df_proj["ps"] >= common_low) & (df_proj["ps"] <= common_high)
df_support = df_proj[support_mask].copy().reset_index(drop=True)
blue_s = df_support[df_support["is_blue_ccs"] == 1].reset_index(drop=True)
pem_s = df_support[df_support["is_blue_ccs"] == 0].reset_index(drop=True)

caliper = 0.05
if len(pem_s) > 0 and len(blue_s) > 0:
    nn = NearestNeighbors(n_neighbors=1)
    nn.fit(pem_s[["ps"]].values)
    dist, idx = nn.kneighbors(blue_s[["ps"]].values)
    keep = dist.ravel() <= caliper
    matched_blue = blue_s[keep].reset_index(drop=True)
    matched_pem_idx = idx[keep].ravel()
    matched_pem = pem_s.iloc[matched_pem_idx].reset_index(drop=True)
    n_unique_pem = pd.Series(matched_pem_idx).nunique()
    print(f"  Matched pairs: {len(matched_blue)}, unieke PEM controls: {n_unique_pem}")
else:
    matched_blue = blue_s
    matched_pem = pem_s
    n_unique_pem = len(pem_s)

# Bereken SMDs op log_capacity_mw, year_announced + region/sponsor dummies
covariates = ["log_capacity_mw", "year_announced"]
region_levels = ["Other_Europe", "North_America", "Asia", "ANZ", "MENA", "Other"]
sponsor_levels = ["Utility", "Industrial_gas", "Steel", "Pure_play", "Unknown", "Other"]

smd_rows = []

# Continuous covariates
for cov in covariates:
    t_pre = df_proj[df_proj["is_blue_ccs"] == 1][cov]
    c_pre = df_proj[df_proj["is_blue_ccs"] == 0][cov]
    t_post = matched_blue[cov] if len(matched_blue) > 0 else t_pre
    c_post = matched_pem[cov] if len(matched_pem) > 0 else c_pre
    smd_rows.append({
        "covariate": cov,
        "smd_before": smd(t_pre, c_pre),
        "smd_after": smd(t_post, c_post),
    })

# Region dummies
for lvl in region_levels:
    t_pre = (df_proj.loc[df_proj["is_blue_ccs"] == 1, "region"] == lvl).astype(int)
    c_pre = (df_proj.loc[df_proj["is_blue_ccs"] == 0, "region"] == lvl).astype(int)
    if len(matched_blue) > 0:
        t_post = (matched_blue["region"] == lvl).astype(int)
        c_post = (matched_pem["region"] == lvl).astype(int)
    else:
        t_post, c_post = t_pre, c_pre
    smd_rows.append({
        "covariate": f"region={lvl}",
        "smd_before": smd(t_pre, c_pre),
        "smd_after": smd(t_post, c_post),
    })

# Sponsor type dummies
for lvl in sponsor_levels:
    t_pre = (df_proj.loc[df_proj["is_blue_ccs"] == 1, "sponsor_type"] == lvl).astype(int)
    c_pre = (df_proj.loc[df_proj["is_blue_ccs"] == 0, "sponsor_type"] == lvl).astype(int)
    if len(matched_blue) > 0:
        t_post = (matched_blue["sponsor_type"] == lvl).astype(int)
        c_post = (matched_pem["sponsor_type"] == lvl).astype(int)
    else:
        t_post, c_post = t_pre, c_pre
    smd_rows.append({
        "covariate": f"sponsor={lvl}",
        "smd_before": smd(t_pre, c_pre),
        "smd_after": smd(t_post, c_post),
    })

smd_df = pd.DataFrame(smd_rows)
smd_df = smd_df.sort_values("smd_before", key=lambda s: s.abs(), ascending=True)

# Plot
fig, ax = plt.subplots(figsize=(9, max(5, 0.32 * len(smd_df))))
y_pos = np.arange(len(smd_df))
ax.axvline(0, color="black", linewidth=0.8)
ax.axvline(0.1, color="gray", linewidth=0.7, linestyle="--", alpha=0.7)
ax.axvline(-0.1, color="gray", linewidth=0.7, linestyle="--", alpha=0.7)
ax.axvline(0.25, color="red", linewidth=0.7, linestyle=":", alpha=0.6)
ax.axvline(-0.25, color="red", linewidth=0.7, linestyle=":", alpha=0.6)
ax.scatter(smd_df["smd_before"], y_pos, color="#C00000", s=70, label="Before matching",
           zorder=3, edgecolor="darkred", linewidth=0.5)
ax.scatter(smd_df["smd_after"], y_pos, color="#2E75B6", s=70, label="After matching (caliper 0.05)",
           zorder=4, edgecolor="darkblue", linewidth=0.5)
for i, (b, a) in enumerate(zip(smd_df["smd_before"], smd_df["smd_after"])):
    ax.plot([b, a], [i, i], color="gray", linewidth=0.6, alpha=0.6, zorder=2)
ax.set_yticks(y_pos)
ax.set_yticklabels(smd_df["covariate"].values, fontsize=9)
ax.set_xlabel("Standardised Mean Difference", fontsize=11)
ax.set_title(
    "Love Plot: Covariate Balance Before and After Propensity Score Matching\n"
    "Dashed grey lines at $\\pm$0.1 (rule of thumb); red dotted lines at $\\pm$0.25",
    fontsize=11,
)
ax.legend(loc="lower right", fontsize=10)
ax.grid(alpha=0.3, axis="x")
plt.tight_layout()
out3 = FIGURES / "fig_love_plot.png"
plt.savefig(out3, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved: {out3}")

# ============================================================
# FIGUUR 4: WEIGHT DISTRIBUTIONS (IPW)
# ============================================================
print("\n" + "=" * 70)
print("FIGUUR 4: IPW WEIGHT DISTRIBUTIONS")
print("=" * 70)

# Stabilised IPW: w = P(T)/e(x) for T=1, (1-P(T))/(1-e(x)) for T=0
p_t = df_proj["is_blue_ccs"].mean()
df_proj["ipw_raw"] = np.where(
    df_proj["is_blue_ccs"] == 1, p_t / df_proj["ps"],
    (1 - p_t) / (1 - df_proj["ps"]),
)
# Trim at 1% and 99%
ipw_low, ipw_high = df_proj["ipw_raw"].quantile([0.01, 0.99])
df_proj["ipw"] = df_proj["ipw_raw"].clip(lower=ipw_low, upper=ipw_high)

print(f"  IPW range (trimmed):  [{df_proj['ipw'].min():.3f}, {df_proj['ipw'].max():.3f}]")
print(f"  IPW mean:             {df_proj['ipw'].mean():.3f}")
print(f"  Effective sample size: {df_proj['ipw'].sum()**2 / (df_proj['ipw']**2).sum():.0f}")

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Panel 1: IPW by treatment
ax = axes[0]
ax.hist(df_proj.loc[df_proj["is_blue_ccs"] == 1, "ipw"], bins=30,
        alpha=0.7, color="#C00000", label="Blue_CCS",
        edgecolor="darkred", linewidth=0.5)
ax.hist(df_proj.loc[df_proj["is_blue_ccs"] == 0, "ipw"], bins=30,
        alpha=0.7, color="#2E75B6", label="PEM",
        edgecolor="darkblue", linewidth=0.5)
ax.set_xlabel("Stabilised IPW", fontsize=11)
ax.set_ylabel("Count", fontsize=11)
ax.set_title("IPW Distribution by Treatment Group\n(trimmed at 1st/99th percentile)",
             fontsize=11)
ax.legend(fontsize=10)
ax.grid(alpha=0.3)

# Panel 2: Log-IPW for skew visualisation
ax = axes[1]
ax.hist(np.log(df_proj.loc[df_proj["is_blue_ccs"] == 1, "ipw"]), bins=30,
        alpha=0.7, color="#C00000", label="Blue_CCS",
        edgecolor="darkred", linewidth=0.5)
ax.hist(np.log(df_proj.loc[df_proj["is_blue_ccs"] == 0, "ipw"]), bins=30,
        alpha=0.7, color="#2E75B6", label="PEM",
        edgecolor="darkblue", linewidth=0.5)
ax.set_xlabel("log(IPW)", fontsize=11)
ax.set_ylabel("Count", fontsize=11)
ax.set_title("Log-IPW Distribution: Heavy Tail Visible",
             fontsize=11)
ax.legend(fontsize=10)
ax.grid(alpha=0.3)

plt.suptitle("Inverse Probability Weighting Diagnostics", fontsize=13, y=1.02)
plt.tight_layout()
out4 = FIGURES / "fig_weight_distributions.png"
plt.savefig(out4, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved: {out4}")

print("\n" + "=" * 70)
print("KLAAR")
print("=" * 70)
print(f"  Vier figures opgeslagen in: {FIGURES}/")
print(f"    1. fig_ps_density.png       (paper Section 3.2, Figure A1)")
print(f"    2. fig_common_support.png   (paper Appendix A2)")
print(f"    3. fig_love_plot.png        (paper Section 3.3)")
print(f"    4. fig_weight_distributions.png  (diagnostic, optioneel)")
