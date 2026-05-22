# GAP ANALYSIS v2
## MSc EOR Thesis — Wat is gedaan, wat ontbreekt, wat is prioriteit

**Auteur**: Sake Saakstra
**Datum**: 20 mei 2026
**Versie**: v2 (update na Pijlers 24b/24c/27/27a/28/29)
**Voorganger**: GAP_ANALYSIS_2026-05-20.md (v1 → vooral pre-route-A)

---

## EXECUTIVE SUMMARY

### Status nu
30+ pijlers compleet, 5 jurisdicties geanalyseerd, 5 publication-grade findings, theoretical framework geïntegreerd. Repo + alle commits gepusht naar GitHub.

### Top-3 prioriteit-1 gaps (MUST-DO voor PhD-defense)
1. **Chapter 5-6 outline** schrijven (real-options framework integratie) — 2-3 uur
2. **Chapter 7 outline** schrijven (TVP-state-space methodologie) — 1-2 uur
3. **POLICY_BRIEFINGS_v2** update met UK selection-funnel + China benchmark — 1 uur

### Top-3 prioriteit-2 gaps (BELANGRIJK, niet kritiek voor defense)
1. **Australia case study** (Pijler 30) — 73 projecten, 38.4% failure
2. **Energy Policy paper concept** — 45Q als hero finding
3. **Counterfactual extension** met carrot taxonomie

### Top-3 prioriteit-3 gaps (FUTURE WORK)
1. Japan + South Korea analyse (32+36 projecten)
2. India + sectoral end-use comparison (55 projecten)
3. US state-level decompositie (Texas, California, Louisiana)

---

## SECTIE 1: WAT IS GEDAAN (ITEMIZED VOORTGANG)

### Sinds GAP_ANALYSIS v1 (sessie 20-mei)

**Route A — TVP fix (Pijlers 24/24a/24b/24c)**
- ✅ Pijler 24 RW probleem geïdentificeerd (1000 divergences)
- ✅ Pijler 24a non-centered RW gepoogd (2001 divergences) — failed
- ✅ Pijler 24b threshold model SUCCESS (Wald p<0.0001)
- ✅ Pijler 24c PUBLICATION-GRADE AR(1) via pytensor.scan (0 div, r_hat 1.00)

**Route B — UK case study (Pijlers 27/27a)**
- ✅ Pijler 27 UK Track-1/HAR1 effect (DiD +0.235 / +0.154, p < 0.02)
- ✅ Pijler 27a UK qualitative decomposition (mega-project + oil-major analysis)
- ✅ Selection-funnel reinterpretation (niet policy failure)

**Route D — China extension (Pijler 28)**
- ✅ Pijler 28 China 14th FYP DiD = −0.057, p = 0.014
- ✅ SOE perfect track record analysis (0/35 failures)
- ✅ Provinciale heterogeneity

**Route E — Theoretical foundation (Pijler 29)**
- ✅ Real options framework document (1454 woorden)
- ✅ Empirical test van 4 predicties
- ✅ Forecast capability via AR(1)

**Route H — Methodologische fix (Pijler 24c)**
- ✅ PyTensor scan oplossing voor numba compile probleem
- ✅ Drie convergerende TVP methoden verkregen

**Synthese**
- ✅ FINAL_SYNTHESIS_v4 (3274 woorden, vandaag)
- ✅ GAP_ANALYSIS_v2 (this document)
- ⏳ POLICY_BRIEFINGS_v2 (volgende sessie)

### Eerder voltooid (pre-route-A)

| Pijler | Status | Type |
|---|---|---|
| 1-13 | ✅ Paper baseline N=714 v7 | Methodologisch + empirisch |
| 14-21 | ✅ S&P replicatie N=1354 | Empirisch |
| 22 | ✅ Statisch interactie β_int = −0.325 (NS) | Empirisch |
| 23 | ✅ Cross-country 4-way | Empirisch |
| 24 | ✅ RW Bayesian (failed) | Methodologisch (informative) |
| 25 | ✅ 45V/45Q decompositie | Empirisch + beleid |
| 26 | ✅ EU Innovation Fund | Empirisch + beleid |

**Totaal: 30+ pijlers compleet.**

---

## SECTIE 2: PRIORITEIT-1 GAPS (MUST-DO VOOR PHD-DEFENSE)

### Gap 1: Chapter 5-6 outline (Theoretical framework)

**Wat ontbreekt**:
- Formele uitwerking real-options model
- Sub-secties 5.1 → 5.6 outline
- Concrete vragen voor literatuurzoektocht

**Wat we hebben**:
- PIJLER29_REAL_OPTIONS_FRAMEWORK.md (1454 woorden synthese)
- 37_real_options_empirical_test.py (empirical predictions tested)
- 6 referenties (Pindyck, Dixit-Pindyck, McDonald-Siegel, etc.)

**Wat nog moet**:
1. Detailed model spec voor sequential exercise stadia
2. Closed-form expressions voor V_s* per stadium s
3. Carbon-prijs als μ-shifter mathematics
4. Empirical hypothesis testing framework

**Effort**: 2-3 uur

### Gap 2: Chapter 7 outline (TVP methodology)

**Wat ontbreekt**:
- Detailed motivation waarom static model insufficient
- AR(1) vs RW vs threshold methodology comparison
- Convergence diagnostics standard
- Identification analysis (why T=9 is challenging)

**Wat we hebben**:
- Drie convergerende methodes empirisch
- Publication-grade AR(1) convergence
- Bayesian + frequentist crosscheck

**Wat nog moet**:
1. Sub-sectie outline 7.1 → 7.6
2. Why state-space model is needed
3. Comparison met Sun et al. (2024) static approach
4. Why our identification works (number of events, info content)

**Effort**: 1-2 uur

### Gap 3: POLICY_BRIEFINGS_v2

**Wat ontbreekt**:
- Update voor EU met UK selection-funnel les
- Update voor NL/KGG met China benchmark
- Update voor Gasunie met import-risico assessment
- Updated KPI recommendations

**Wat we hebben**:
- POLICY_BRIEFINGS v1 (15552 bytes, mei 2026)
- Volledige FINAL_SYNTHESIS_v4

**Wat nog moet**:
1. Briefing per stakeholder (3 documenten of 1 met 3 secties)
2. One-pager executive samenvattingen
3. Concrete beleidsrecommendaties met empirische ondersteuning

**Effort**: 1-2 uur

---

## SECTIE 3: PRIORITEIT-2 GAPS (BELANGRIJK)

### Gap 4: Australia case study (Pijler 30)

**Sample**: 73 Australia projecten, 38.4% failure rate (28/73 failures)

**Why interesting**:
- 3e grootste sample na US (164), Germany (154)
- Hoge failure rate (similar UK, lower China)
- Major policy events: Hydrogen Headstart, Critical Minerals Fund
- Vergelijking met China voor mining + iron-ore connection
- Oil-major announcement patroon (Woodside, Origin, etc.)

**Why hopefully effective**:
- Adds southern hemisphere jurisdiction
- Tests if oil-major dominance is structureel of UK-specifiek
- Australia = potential H2-exporter, dus relevant voor EU import policy

**Hypothese**:
- DiD na Headstart 2023 (analoog 45Q)
- DiD voor Critical Minerals Fund
- Sponsor decomposition: BP, Shell, Origin Energy, Woodside vs startups

**Effort**: 4-6 uur

### Gap 5: Energy Policy paper concept

**Doel**: publiek-toegankelijke versie van 5 publication-grade findings
- Target journal: Energy Policy (Elsevier)
- Concept: 45Q als hero finding + carrot taxonomie + UK selection-funnel
- Lengte: ~6000 woorden + 4-6 figuren
- Voor PhD-defense waardevol als "publication-track output"

**Effort**: 4-6 uur (concept), nog meer voor review-ready

### Gap 6: Counterfactual extension met carrot taxonomie

**Wat we hebben**: Pijler 18 counterfactual (Deaner-Ku)
**Wat ontbreekt**:
- Counterfactual met cross-jurisdiction adjustments
- "Wat als EU 45Q-equivalent had?"
- "Wat als UK output-credit ipv selection-tender?"
- Scenario analyse met AR(1) forecast 2027-2030

**Effort**: 3-4 uur

---

## SECTIE 4: PRIORITEIT-3 GAPS (FUTURE WORK)

### Gap 7: Japan + South Korea analyse

**Sample**: 
- Japan: 32 projecten, 18.8% failure rate
- South Korea: 36 projecten, 38.9% failure rate

**Why interesting**:
- Japan: Green Innovation Fund (2021), Basic Hydrogen Strategy 2017
- South Korea: H2 Economy Roadmap (2019), Hydrogen Law (2020)
- Asian carrot mechanism patterns

**Effort**: 3-4 uur

### Gap 8: India case study

**Sample**: 55 India projecten, 14.5% failure rate

**Why interesting**:
- National Green Hydrogen Mission (2023)
- Grote sample, lage failure (~ China pattern?)
- Different policy design (PLI scheme = output-conditioned)

**Effort**: 3-4 uur

### Gap 9: US state-level decompositie

**Wat we hebben**: US analyse op nationaal niveau (Pijlers 25)
**Wat ontbreekt**:
- Texas (oil-state) vs California (renewables) vs Louisiana (CCS hub)
- US state-level subsidies (zonder federal 45Q)
- IRA state-level rollout effecten

**Effort**: 5-6 uur

### Gap 10: Sectoral end-use comparison

**Wat we hebben**: S&P end-use sector data
**Wat ontbreekt**:
- Refinery feedstock vs steel vs transport effects
- Sectoral failure rate decompositie
- End-use specific subsidies (DRI steel, ammonia, methanol)

**Effort**: 4-5 uur

---

## SECTIE 5: METHODOLOGISCHE GAPS

### Gap 11: Robustness checks voor 45Q finding

**Currently**: Pijler 25 standard DiD + bootstrap inference
**Could add**:
- Synthetic control method (Abadie)
- Event study with placebo periods
- Heterogeneous treatment effects via causal forest
- Permutation inference (already in P25)

**Effort**: 4-6 uur

### Gap 12: TVP extension naar multiple coefficient time-variation

**Currently**: TVP voor β_int only (Pijler 24c)
**Could add**:
- TVP voor β_blue main effect
- TVP voor β_eua main effect
- Multivariate state-space (vector form)
- Common factor model

**Effort**: 6-8 uur (significant model extension)

### Gap 13: Bayesian model averaging

**Currently**: AR(1) preferred via LOO (but LOO failed)
**Could add**:
- Proper LOO comparison
- Stacking weights
- Posterior model probabilities

**Effort**: 2-3 uur (technical fix)

### Gap 14: Spatial econometrics

**Currently**: Geography as fixed effect
**Could add**:
- Spatial autocorrelation (Moran's I)
- Spatial lag/error models
- Diffusion patterns van technology adoption

**Effort**: 5-7 uur

---

## SECTIE 6: THEORETISCHE GAPS

### Gap 15: Game-theoretic extension van real options

**Currently**: Single-firm decision problem (Pijler 29)
**Could add**:
- Strategic interaction tussen oil majors
- Cournot competition voor cluster-tender bidding
- Information cascades in UK case

**Effort**: 8-10 uur

### Gap 16: Carbon-prijs stochastic process modeling

**Currently**: EUA as observed time series
**Could add**:
- Calibrate stochastic process (mean reversion vs GBM)
- Forecast EUA paths for scenario analysis
- Joint model EUA + project survival

**Effort**: 6-8 uur

### Gap 17: Network effects model

**Currently**: Project-level analysis
**Could add**:
- Cluster effects (HyNet, East Coast, etc.)
- Pipeline-dependent projects
- Sponsor-network analysis

**Effort**: 7-9 uur

---

## SECTIE 7: EMPIRISCHE GAPS

### Gap 18: Productie data extension

**Currently**: S&P snapshot 24-3-2024
**Could add**:
- S&P updates (zou data tot 2025/2026)
- Granular productie data (kg H2 per maand)
- Capacity utilization rates

**Constraint**: data licensing + availability

### Gap 19: Cost data integration

**Currently**: announcement-level capex (where available)
**Could add**:
- Operational cost data
- LCOH (Levelized Cost of Hydrogen) calculations
- Cost-curve learning effects

**Effort**: 6-8 uur + data sourcing

### Gap 20: Investor sentiment integration

**Currently**: project-level data
**Could add**:
- Equity market reaction to announcements (event study)
- Bond yield spread changes for sponsor companies
- ESG ratings correlation

**Effort**: 4-6 uur + financial data access

---

## SECTIE 8: WHAT TO PRIORITIZE — DECISION MATRIX

### Voor PhD-thesis defensible (must-do)

| Gap | Effort | Impact PhD | Priority |
|---|---|---|---|
| Gap 1: Chapter 5-6 outline | 2-3u | Hoog | **1** |
| Gap 2: Chapter 7 outline | 1-2u | Hoog | **1** |
| Gap 3: POLICY_BRIEFINGS_v2 | 1-2u | Medium | **1** |

### Voor academic publication track

| Gap | Effort | Impact academic | Priority |
|---|---|---|---|
| Gap 5: Energy Policy paper | 4-6u | Hoog | **2** |
| Gap 4: Australia case | 4-6u | Medium-Hoog | **2** |
| Gap 11: 45Q robustness | 4-6u | Medium | **2** |

### Voor future research agenda

| Gap | Effort | Impact future | Priority |
|---|---|---|---|
| Gap 7-9: Asia + state-level | 10-12u | Medium | **3** |
| Gap 12: TVP extension | 6-8u | Hoog (methodologisch) | **3** |
| Gap 15-17: Theory extensions | 20+ uur | Hoog (theoretical) | **3** |

---

## SECTIE 9: AANBEVOLEN VOLGENDE STAPPEN (NA DEZE SESSIE)

### Sessie 1 (Korte sessie, 2-3 uur)
- ✅ Route F voltooid (deze sessie)
- ➡️ **Chapter 5-6 outline** (Gap 1)

### Sessie 2 (Medium sessie, 3-4 uur)
- ➡️ **Chapter 7 outline** (Gap 2)
- ➡️ **POLICY_BRIEFINGS_v2** (Gap 3)

### Sessie 3 (Lange sessie, 5-6 uur)
- ➡️ **Energy Policy paper concept** (Gap 5)

### Sessie 4 (Medium sessie, 4-6 uur)
- ➡️ **Australia case study Pijler 30** (Gap 4)

### Eventueel later
- Gap 6 (counterfactual extension)
- Gap 11 (45Q robustness checks)
- Gap 12 (TVP extension)

---

## SECTIE 10: WHAT YOU HAVE ENOUGH FOR

### Voor PhD-defense (Koopman + Ketel)

✅ **Empirisch deel**: 5 publication-grade findings, 5 jurisdicties
✅ **Methodologisch deel**: Three convergerende TVP methoden
✅ **Theoretisch deel**: Real options framework (Chapter 5-6 foundation)
✅ **Data**: 1354 Blue+Green projecten + macro panel
✅ **Reproduceerbaarheid**: 36 scripts + 35+ result files in repo
⏳ **Schrijfwerk**: Chapter outlines needed

### Voor Energy Policy submission

✅ **Findings**: 45Q hero finding + carrot taxonomie
✅ **Mechanism interpretation**: real options framework
⏳ **Paper concept**: needs writing (Gap 5)
⏳ **Stakeholder reactions**: optional but helpful

### Voor practitioner audiences

✅ **EU briefing**: ready material in FINAL_SYNTHESIS_v4
✅ **NL/KGG briefing**: ready material
✅ **Gasunie briefing**: ready material
⏳ **Compact one-pagers**: Gap 3 (POLICY_BRIEFINGS_v2)

---

## EINDCONCLUSIE

**Bottom line voor je defense**:

Je hebt nu **30+ pijlers, 5 publication-grade findings, 5 jurisdicties, three-method TVP convergence, en real-options theoretical framework**. Voor de PhD-thesis is dit ruimschoots voldoende voor een verdedigbare bijdrage.

**Wat je nog wel moet doen** (in volgorde van prioriteit):
1. Chapter outlines schrijven (Chapter 5-6 + Chapter 7) — 3-5 uur totaal
2. POLICY_BRIEFINGS_v2 update — 1-2 uur
3. Eventueel: Energy Policy paper concept voor publication track

**Wat je niet meer hoeft te doen** voor de defense:
- Meer jurisdicties (Australia/Japan/India zijn nice-to-have, niet must-have)
- Meer methodologische uitbreiding (TVP-multivariate is future work)
- Meer theoretische uitbreiding (game-theoretic is future work)

Je hebt een **complete dataset voor verdediging** — focus nu op het narratief, de chapter-outlines, en eventueel het policy paper.
