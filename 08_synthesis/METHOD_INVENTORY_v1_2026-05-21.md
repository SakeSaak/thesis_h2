# COMPLETE METHODE-INVENTARISATIE v1

**Auteur**: Sake Saakstra (samengesteld na user-correctie op gap analyse v4)
**Datum**: 21 mei 2026
**Status**: Definitief overzicht van ALLE bestaande analyses, scripts, en bevindingen
**Doel**: voorkomen dat we methoden "missen" die er al zijn, voor en NA de v4-correctie

---

## 1. EXECUTIVE SUMMARY

### Cijfers
- **80 Python scripts** in 12 subdirectories van `06_thesis_extensions/`
- **3 R scripts** (Bayesian methodology setup)
- **11 Pijler-reports** in markdown
- **135 CSV result files** in `results/` directories
- **83 figuur-bestanden** (PDF + PNG)
- **515 bestanden** tracked op GitHub
- **0 untracked** bestanden — repo volledig in sync

### Twee verhaallijnen
Het thesis-corpus dekt feitelijk **twee analytisch verschillende verhalen**:

| | Verhaal A: Carbon-Conditional Blue/Green | Verhaal B: Carrot-Policy + Offtake |
|---|---|---|
| Vraag | Is Blue/Green hazard EUA-prijsafhankelijk? | Welke beleid + mechanismes voorkomen project-failure? |
| Sample | v7 (N=714) + S&P-replicatie | S&P (N=1354) |
| Methoden | Cox PH, GAS-TVP, state-space, MCMC | Modern DiD (TWFE/SA/BJS), SDID, matching, Honest DiD |
| Pijlers | 1-13 (oud), 24a-c, 29 | 14-46 (nieuw na 18 mei) |
| Chapters in thesis_v1 | 7 (verbatim uit chapter7_v2.tex) | 6, 8, 9 (nieuw geschreven) |

Dit is een **belangrijke structurele observatie** voor de v2-revisie: chapter 7 verwijst nog naar het oude carbon-conditional verhaal, terwijl chapters 6/8/9 over carrot-policies gaan. Voor coherentie moeten we kiezen:
- **Optie 1**: Chapter 7 herschrijven voor het nieuwe verhaal (TVP-DiD op carrot-policies)
- **Optie 2**: Chapter 7 expliciet positioneren als "Result II: Independent confirmation via carbon-conditional channel" en de bridge bouwen
- **Optie 3**: Carbon-conditional als appendix verplaatsen, focus puur op carrot-policy verhaal

---

## 2. PER-PIJLER INVENTARIS

### Tier 1: Carbon-Conditional Verhaal (Pijlers 1-13, 24a-c, 29)

#### Pijler 1-3 — Bayesian methodology + Public CCUS
- **Pijler 1**: Bayesian Cox PH baseline op v7 (4-prior sensitivity grid)
  - `01_bayesian_methodology/01_bayesian_cox_baseline.R` + PyMC versie
  - **Status**: ✅ Done, in code | ❌ Niet expliciet in thesis_v1
  - Resultaten: `bayesian_cox_summary_*.csv` per prior
  
- **Pijler 2**: NL Policy Chapter (outline)
  - `02_nl_policy_chapter/`
  - **Status**: ⚠️ 15-pag outline alleen, geen scripts
  
- **Pijler 3**: Public IEA CCUS robustness
  - `03_public_data_robustness/01_build_*.py`, `02_cox_ph_public_ccus.py`
  - **Status**: ✅ Done in code | ❌ Niet in thesis_v1
  - 98 H2-CCUS projecten + 3 Cox PH modellen

#### Pijler 4 — Carbon-conditional core (Spoor B)
- **Pijler 4**: Carbon-conditional frequentist + Bayesian
  - `04_carbon_conditional/03_carbon_conditional_freq.py`
  - `04_carbon_conditional/04_carbon_conditional_bayes.py`
  - **Status**: ✅ Done in code | ⚠️ Verbatim in chapter 7 (originele paper)
  - Bevinding: HR=4.67 Blue×EUA interaction (replicatie v7)

#### Pijler 5 — TVP state-space (Chapter 7 hoofdwerk)
- `05_state_space_tvp/` heeft 12 Python scripts:
  - `01_tvp_hazard_pilot.py` — Pilot random walk on β_int(t)
  - `02_tvp_hazard_blocks.py` — Block-stratified estimates
  - `03_block2_diagnostic.py` — 2023-2024 null check
  - `04_gas_hazard.py` — **GAS-TVP (296 regels, citeert Creal-Koopman-Lucas)**
  - `05_robustness_loowaic.py` — Comprehensive robustness
  - `06_refinements_noncentered.py` — Non-centered reparameterization
  - `07_within_sponsor.py` — Within-sponsor causal ID
  - `08_heterogeneous_effects.py` — Multi-level effects
  - `09_eu_deepdive.py` — EU/ETS-bound region focus
  - `10_na_deepdive.py` — North America focus
  - `11_na_only_tvp.py` — NA-cleanest replication
  - `12_pooled_sponsor_control.py` — All regions with sponsor controls
  - **Status**: ✅ Done in code | ✅ Verbatim in chapter 7 (volledig overgenomen)

#### Pijler 6-7 — Real options + Event study
- **Pijler 6**: Real-options numerical calibration
  - `06_real_options_calibration/01_calibrate.py`
  - **Status**: ✅ Done | ⚠️ Theory in chapter 3
  
- **Pijler 7**: EUA event-study
  - `07_event_study/01_eua_event_study.py`
  - **Status**: ✅ Done | ❌ Niet in thesis_v1

#### Pijler 8-9 — CBAM event-study + cross-sectional
- **Pijler 8**: CBAM event-study (5 scripts)
  - `08_cbam_event_study/01-05_*.py` (equity, DiD correction, project-level, triple-diff, robust 2x2)
  - **Status**: ✅ Done | ⚠️ Was Chapter 8 in oude paper, niet in thesis_v1 actief
  
- **Pijler 9**: S&P Global CBAM analyses (4 scripts)
  - `09_sp_global_cbam/01-04_*.py`
  - **Status**: ✅ Done | ❌ Niet expliciet in thesis_v1

#### Pijler 10-11 — IEA cross-validatie + v7-S&P matching
- **Pijler 10**: IEA cross-validation
  - `10_iea_cross_validation/01-02_*.py`
  - **Status**: ✅ Done | ❌ Niet in thesis_v1
  
- **Pijler 11**: v7 ↔ S&P matching (sample-overlap check)
  - `11_v7_sp_matching/01_reconstruct_v7.py`, `02_clean_matching.py`
  - **Status**: ✅ Done | ❌ Niet expliciet in thesis_v1
  - Belangrijk: HR_cancel 13.19 v7 → 2.94 S&P (sample-dependence finding)

### Tier 2: Robustness Battery (Pijlers 12-21 + 24-29) — `12_advanced_robustness/`

Deze 43 scripts vormen de complete moderne econometrische toolkit:

| Script | Pijler | Methode | Status thesis |
|---|---|---|---|
| `01_honest_did_v2.py` | — | Honest DiD via LPM | ⚠️ Pijler 44 vervangt dit |
| `02_wild_cluster_bootstrap.py` | — | Wild Cluster Bootstrap (Cameron 2008) | ❌ Niet in thesis |
| `03_permutation_inference.py` | — | Randomization inference | ❌ Niet in thesis |
| `04_bayesian_diagnostics_v2.py` | — | Bayesian fit + moderne diagnostiek | ❌ Niet in thesis |
| `05_hazard_diagnostics_suite.py` | — | Hazard-diagnostiek (Hosmer-Lemeshow, AUC, Schoenfeld) | ⚠️ Deels in ch7 |
| `06_oos_cv_and_functional_form.py` | — | OOS CV + Roth-Sant'Anna FF test | ⚠️ Deels in ch7 |
| `07_outlier_influence.py` | — | Cook's distance + DFBETA | ❌ Niet in thesis |
| `08_event_study_pretrends.py` | — | Event-study leads/lags + pretrends test | ❌ Niet in thesis |
| `09_monte_carlo_power.py` | — | MC power-simulatie | ❌ Niet in thesis |
| `10_oster_bounds.py` | — | Oster (2019) OVB bounds | ⚠️ Deels in ch8 |
| `11_heterogeneous_effects_ira_mechanism.py` | — | IRA mechanism HTE | ❌ Niet in thesis |
| **`12_synthetic_did.py`** | **5** | **SDID (Arkhangelsky et al 2021 AER)** | **❌ Niet in thesis** |
| **`13_competing_risks.py`** | — | **Cause-Specific Cox PH (Fine-Gray)** | **❌ Niet in thesis** |
| **`14_conditional_score_residuals.py`** | — | **CSR diagnostic (Blasques-Gorgi-Koopman 2025)** | **⚠️ Deels in ch7** |
| `15_honest_did_smoothness.py` | — | Honest DiD smoothness restricties | ❌ Niet in thesis |
| **`16_causal_forests.py`** | — | **Causal Forests (Athey-Wager)** | **❌ Niet in thesis** |
| **`17_stochastic_volatility.py`** | — | **Score-Driven SV extension (Creal-Koopman-Lucas)** | **❌ Niet in thesis** |
| `18_deaner_ku_hazard_did.py` | **14** | Deaner-Ku 2024 hazard-DiD op v7 | ❌ Niet in thesis |
| `19_deaner_ku_sp_dual_treatment.py` | **15** | DK replication op S&P met dual treatment | ❌ Niet in thesis |
| `20_multistate_sp.py` | **16** | Multistate Lifecycle Analysis | ❌ Niet in thesis |
| **`21_sequential_sdid.py`** | **17** | **Sequential SDID (Arkhangelsky-Samkov 2024)** | **❌ Niet in thesis** |
| `22_45v_three_pillars.py` | **18** | US 45V three-pillars DDD effect | ❌ Niet in thesis |
| `23_causal_forests_sp.py` | **19** | Causal Forests op S&P | ❌ Niet in thesis |
| `24_master_cox_ph_sp.py` | **20** | Master Cox PH regressie S&P | ❌ Niet in thesis |
| **`25_sdid_project_level_sp.py`** | **21** | **Project-level SDID + 1-NN matching + classic SC** | **❌ Niet in thesis** |
| `26_45v_bootstrap_inference.py` | 18b | 45V bootstrap inference | ❌ Niet in thesis |
| `27_carbon_conditional_sp.py` | — | Carbon-conditional op S&P | ❌ Niet in thesis |
| `28_cross_country_carbon_price.py` | — | Cross-country carbon prijs analyse | ❌ Niet in thesis |
| `29_tvp_state_space_sp.py` | 24a | TVP state-space op S&P | ❌ Niet in thesis |
| `30_45v_45q_decomposition.py` | — | 45V vs 45Q decompositie | ❌ Niet in thesis |
| **`31_innovation_fund_effect.py`** | — | **EU Innovation Fund DiD** | ✅ In chapter 6 |
| `32_tvp_state_space_v2.py` | 24b | TVP state-space v2 | ✅ In chapter 7 als M2 |
| `33_tvp_threshold_v3.py` | 24c | TVP threshold publication-grade | ✅ In chapter 7 als M3 |
| **`34_uk_track_har_effects.py`** | **27** | **UK Track-1/HAR1 effect** | ✅ In chapter 6 |
| `35_uk_qualitative_decomposition.py` | 27a | UK kwalitatieve selectie-funnel | ⚠️ Vermeld in ch6 |
| **`36_china_14fyp_effect.py`** | **28** | **China 14th FYP effect** | ✅ In chapter 6 |
| `38_tvp_publication_grade.py` | 24c-final | TVP final publication-grade | ✅ In chapter 7 |
| `39_causal_forest_HTE_carrots.py` | 30 | Causal Forest HTE op carrots | ⚠️ Vermeld in ch6/discussion |
| `40_sectoral_triple_did.py` | 31 | Sectorale triple-DiD | ⚠️ Resultaten in ch8 |
| `41_subgroup_did_validation.py` | 33 | Subgroup DiD validatie | ❌ Niet in thesis |
| **`42_modern_did_robustness.py`** | **32** | **TWFE + Sun-Abraham + BJS-imputation** | ✅ In chapter 6 |
| **`43_offtake_effect_identification.py`** | **34** | **Offtake-effect 5-methods** | ✅ In chapter 8 |
| **`44_honest_did_bounds.py`** | **39** | **Honest DiD bounds (Rambachan-Roth)** | ✅ In chapter 6 |

### Tier 3: Theoretical + Counterfactual (Pijlers 29, 40, 36)

- **Pijler 29 / 40**: Real-options × mechanism design framework
  - `13_theoretical/37_real_options_empirical_test.py`
  - `13_theoretical/45_real_options_numerical.py`
  - **Status**: ✅ Done | ✅ In chapter 3
  
- **Pijler 36**: Counterfactual scenarios met bootstrap
  - `14_counterfactual/46_counterfactual_scenarios.py`
  - **Status**: ✅ Done | ✅ In chapter 9 (5 scenarios)

---

## 3. PER-CHAPTER INVENTARIS

### Chapter 6 (Main DiD)
**Bevat**:
- Pijler 32 (modern DiD: TWFE+SA+BJS) ✅
- Pijler 39 (Honest DiD bounds) ✅
- Pijler 27 (UK Track) ✅
- Pijler 28 (China 14th FYP) ✅
- Pijler 31 (EU Innovation Fund, hoewel script-output) ✅

**Mist**:
- Pijler 17 (Sequential SDID) — robustness uitbreiding
- Pijler 21 (Project-level SDID) — robustness
- Pijler 14/15 (Deaner-Ku) — hazard-DiD voor staggered

### Chapter 7 (TVP State-Space)
**Bevat** (uit chapter7_v2.tex):
- Pijler 5 (random walk TVP M2) ✅
- Pijler 24c (publication-grade AR(1) M2) ✅
- Pijler 24c/38 (GAS-TVP als M3) ✅
- Schoenfeld test motivatie ✅
- Within-sponsor causal ID ✅
- NA-only DiD around IRA ✅

**Mist of conflicteert**:
- ⚠️ **Verhaal-discontinuiteit**: chapter 7 over Blue/Green carbon-conditional terwijl rest van thesis over carrot-policies gaat
- CSR diagnostic (script 14) vermeldt resultaten maar niet de complete diagnostic
- SV extension (script 17) is geheel afwezig

### Chapter 8 (Offtake Mechanism)
**Bevat**:
- Pijler 34 (offtake 5-method ID) ✅
- Sector heterogeniteit (Pijler 31 deels) ✅
- Oster δ_null = 20.23 ✅

**Mist**:
- Pijler 21 (Project-level SDID voor CBAM/Green) — sterke robustness
- Pijler 13 (Competing Risks) — voor multi-mode failure interpretatie

### Chapter 9 (Counterfactual)
**Bevat**:
- Pijler 36 (5 scenarios met bootstrap) ✅

**Mist**: niets kritisch

### Chapter 3 (Theoretical)
**Bevat**:
- Real-options Dixit-Pindyck framework ✅
- Pijler 40 mechanism-design uitbreiding ✅

**Mist**:
- Empirische kalibratie (Pijler 6) — kan worden toegevoegd

### Wat staat NERGENS in de thesis maar wel in code (lange lijst)

**Methodologische scripts die niet zijn opgenomen**:
1. `02_wild_cluster_bootstrap.py` — Wild Cluster Bootstrap inference
2. `03_permutation_inference.py` — Randomization inference
3. `04_bayesian_diagnostics_v2.py` — Volledige Bayesian diagnostiek
4. `07_outlier_influence.py` — Cook's distance + DFBETA
5. `08_event_study_pretrends.py` — Event-study leads/lags
6. `09_monte_carlo_power.py` — MC power-simulatie
7. `13_competing_risks.py` — Cause-Specific Cox PH (Fine-Gray)
8. `15_honest_did_smoothness.py` — Smoothness Honest DiD
9. `16_causal_forests.py` (en `23_causal_forests_sp.py`) — Causal Forests
10. `17_stochastic_volatility.py` — Score-Driven SV extension
11. `18-19_deaner_ku_*.py` — Deaner-Ku hazard-DiD (Pijlers 14-15)
12. `20_multistate_sp.py` — Multistate Lifecycle (Pijler 16)
13. `22_45v_three_pillars.py` + `26_45v_bootstrap_inference.py` — US 45V DDD (Pijler 18+18b)
14. `12_synthetic_did.py` + `21_sequential_sdid.py` + `25_sdid_project_level_sp.py` — drie SDID-varianten

**Bevindingen die nog niet in thesis_v1 staan**:
- US 45V three-pillars DDD = +0.285, p<0.001 (Pijler 18, publication-grade)
- Multistate transition rates per failure-mode (Pijler 16)
- Sample-dependence v7→S&P (Pijler 11) — methodologische discussie
- HR_cancel reversal: 13.19 (v7) → 2.94/2.30 (S&P)
- "Don't pause" claim van v7 gefalsifieerd op S&P
- CBAM informative null over 8 onafhankelijke methoden

---

## 4. WERKELIJKE BEVINDINGEN-OVERZICHT

### Op basis van de FINAL_SYNTHESIS_v4 (5 publication-grade findings):
1. **F1**: US 45Q (sequestration credit) protectief, DiD −0.147, p=0.020 ✅ in thesis ch6
2. **F2**: EU CBAM informative null over 8 methoden ⚠️ niet expliciet in thesis (Chapter 8 oud)
3. **F3**: TVP sign-shift τ*=2020 (β_pre +3.40 → β_post −1.25), Wald p<0.0001 ✅ in chapter 7
4. **F4**: UK Track-1 selection-funnel artefact ✅ in chapter 6
5. **F5**: China 14th FYP protectief, DiD −0.057, p=0.014 ✅ in chapter 6

### Nieuwe findings na Track A+B+C (toegevoegd 20-21 mei):
6. **F6**: Offtake-commitment −11..−13 pp, Oster δ_null=20.23 ✅ in chapter 8
7. **F7**: 6 counterfactual scenarios met bootstrap CIs ✅ in chapter 9
8. **F8**: Real-options × mechanism design framework ✅ in chapter 3
9. **F9**: σ-channel sectoral heterogeniteit ✅ in chapter 8

### Findings die nog NIET in thesis_v1 staan:
10. **F10** (verdiend?): US 45V three-pillars DDD = +0.285, p<0.001 (Pijler 18)
11. **F11**: Multistate transitie-analyse over 3+ failure-paden (Pijler 16)
12. **F12**: Sample-dependence v7↔S&P — methodologische honest discussion (Pijler 11)

---

## 5. GITHUB SYNC STATUS

### Cijfers
- **515 tracked files** op GitHub (`SakeSaak/thesis_h2` private repo)
- **0 untracked** in werkdirectory
- **Branch**: `main`, in sync met `origin/main`
- **Backup**: `backup-before-history-rewrite-2026-05-21` op GitHub
- **Repo size**: 25 MB (na history rewrite van 77 MB)

### Distributie per directory
```
06_thesis_extensions/12_advanced_robustness/   227 files (43 py + 120 csv + 16 pdf)
06_thesis_extensions/05_state_space_tvp/        32 files (12 py +  9 csv +  8 pdf)
06_thesis_extensions/09_sp_global_cbam/         26 files ( 4 py + 14 csv +  8 pdf)
06_thesis_extensions/08_cbam_event_study/       18 files ( 6 py +  8 csv +  4 pdf)
06_thesis_extensions/01_bayesian_methodology/   13 files ( 1 py +  1 csv +  3 pdf)
06_thesis_extensions/04_carbon_conditional/     10 files ( 2 py +  5 csv +  3 pdf)
06_thesis_extensions/03_public_data_robustness/  8 files ( 2 py +  3 csv +  1 pdf)
06_thesis_extensions/13_theoretical/             8 files ( 2 py +  3 csv +  0 pdf)
06_thesis_extensions/10_iea_cross_validation/    5 files ( 2 py +  3 csv +  0 pdf)
06_thesis_extensions/07_event_study/             4 files ( 1 py +  2 csv +  1 pdf)
06_thesis_extensions/11_v7_sp_matching/          4 files ( 2 py +  2 csv +  0 pdf)
06_thesis_extensions/14_counterfactual/          4 files ( 1 py +  2 csv +  0 pdf)
06_thesis_extensions/06_real_options_calibration/3 files ( 1 py +  1 csv +  1 pdf)
06_thesis_extensions/02_nl_policy_chapter/       2 files ( 0 py +  0 csv +  1 pdf)
```

### Recente commits (laatste 10)
```
8663e52 Gap analyse v4.1 CORRECTIE: GAS en Synthetic Control zijn al gedaan
25093c6 Gap analyse v4: post-thesis-draft strategische beoordeling
9a8cdc1 Thesis v1: PDF compileert (90 pagina's, 720 KB)
32b93f0 Email-draft voor supervisor feedback (Koopman + Ketel)
e311e5d Thesis manuscript v1 draft (22,450 words)
8da1306 Repo optimization: hygiene + documentation
9f71538 Track C COMPLEET: POLICY_BRIEFINGS_v2
f616582 Pijler 36: Counterfactual scenarios
d5497fd Pijler 40: Real-options x mechanism design
2add7b8 Pijler 39: Honest DiD bounds
```

---

## 6. ECHTE GAP-ANALYSE (na inventarisatie)

### Eerlijke gap-categorisatie

**Categorie A: AL GEDAAN + IN THESIS** (geen gap)
- GAS-TVP (chapter 7 M3) ✓
- Modern DiD triangulatie (chapter 6) ✓
- Honest DiD Rambachan-Roth (chapter 6) ✓
- Offtake 5-method ID + Oster (chapter 8) ✓
- Real-options theory (chapter 3) ✓
- Counterfactual scenarios (chapter 9) ✓

**Categorie B: AL GEDAAN, NIET IN THESIS** (gap = integratie, niet implementatie)
- Sequential SDID Pijler 17 → ch 6 of 8
- Project-level SDID Pijler 21 → ch 8
- Competing Risks Pijler 13 → ch 7 of 8
- Causal Forest HTE Pijler 30/19 → ch 6 of appendix
- Deaner-Ku hazard-DiD Pijler 14/15 → robuustheid
- Multistate Pijler 16 → chapter 7
- US 45V DDD Pijler 18 → chapter 6 (5e policy?)
- CSR diagnostic + SV extension → chapter 7 uitbreiding
- Wild cluster bootstrap, permutation, MC power → appendix robustness

**Categorie C: ECHT NIET GEDAAN** (true gap)
- Diebold-Mariano forecast comparison
- Sant'Anna-Zhao doubly-robust DiD specifiek (wel IPWRA)
- Dynamic Factor Model voor cross-jurisdictie
- Particle filter voor non-Gaussian state-space
- RDD CBAM threshold (data ontbreekt deels)
- Spatial econometrics (Conley SE etc.)
- Recente literatuur-update (6 papers)
- Nieuws/events update sinds 24-3-2024 snapshot

### Geherprioritiseerde v2-werklast

**MUST voor v2** (focus op INTEGRATIE niet IMPLEMENTATIE):
1. **0.5d** — Pijler 17 (Sequential SDID) integreren in chapter 6
2. **0.5d** — Pijler 21 (Project SDID) integreren in chapter 8
3. **0.5d** — Pijler 13 (Competing Risks) integreren in chapter 7 of appendix
4. **0.5d** — Pijler 14/15/18/19/20 als robustness-appendix verzamelen
5. **3d** — Literatuur update Chapter 2 (6 papers)
6. **2d** — Nieuws/events update post-24-3-2024
7. **1d** — Chapter 7 narrative bridge bouwen tussen carbon-conditional verhaal en carrot-policy verhaal

**Totaal: ~8 dagen werk** (was 26 in v4, blijkt feitelijk minder dan helft)

**SHOULD voor PhD-uitbreiding**:
- Diebold-Mariano forecast comparison (3d)
- Dynamic Factor Model (10d)
- RDD CBAM (10d, vereist extra data)

---

## 7. AANBEVELING

### Voor v1 → v2 iteratie
**Hoofdactie**: integreer bestaande Pijlers 13, 14-15, 16, 17, 18, 19, 21 als robustness sections / appendix in de thesis. Dit is **integratie-werk**, geen nieuwe implementatie. **~3 dagen werk**.

Daarna: literatuur en nieuws update (~5 dagen).

### Voor PhD vervolg
- Hoofdstuk 7 narratief uitbreiden met DFM + particle filter
- Chapter 8 uitbreiden met RDD CBAM
- Submission paper 1: Hoofdstuk 7 (TVP + GAS + DFM) → JAE/JoE
- Submission paper 2: Hoofdstuk 8 (offtake + SDID + CR) → Energy Economics
- Submission paper 3: Hoofdstuk 3+9 (real options + counterfactual) → JEEM

### Voor supervisor-verzending
**Verstuur v1 nu**. De v1 manuscript is *al* sterker dan ik in gap analyse v4 dacht. Verzenden voorkomt verdere vertraging, en supervisor-feedback geeft prioriteiten voor de v2 INTEGRATIE-actie.

---

*Document opgesteld: 21 mei 2026, 11:50 UTC+2*
*Vervangt gap analyses v4 + v4.1 op de inventarisatie-aspecten*
*Behoudt v4.1's correctie van GAS en SDID-status*
