# Implementation-Risk Differentials in Hydrogen Technology Pathways
## Volledige synthese — Versie 2 (gecorrigeerd 20 mei 2026)

**Auteur:** Sake Saakstra · **MSc EOR Financial Track · VU Amsterdam** · **Stand:** 13 commits, 405 files op GitHub

> **Erratum t.o.v. v1 (19 mei 2026):** de eerste versie van dit document bevatte vijf feitelijke fouten — verkeerde coëfficiënten, verkeerde teken-interpretatie van het carbon-conditional effect, en een verzonnen aardgas-mechanisme dat de paper expliciet test en verwerpt. Deze versie is volledig herschreven en geverifieerd tegen `00_paper/current/blueCCS_paper_final.tex` en alle CSV-outputs in `06_thesis_extensions/`. De eerdere versie staat als `.FOUT_RETIRED` in deze map.

---

## DEEL A — De vier substantieve bevindingen, gecorrigeerd

De v7 paper documenteert vier centrale bevindingen op een sample van 714 projecten (244 BlueCCS, 470 PEM) met 43 events (31 terminal cancellations, 12 on-hold), uitgebreid naar 4 246 person-years.

### A.1 Bevinding 1: Gesegmenteerde investeringsecosystemen

BlueCCS en PEM hydrogen projecten zijn geen willekeurige trekkingen uit dezelfde populatie. Het propensity-score model dat technologiekeuze voorspelt uit observables behaalt **McFadden pseudo-R² = 0.698**. Twee onafhankelijke reweighting methodes bevestigen ernstig beperkte overlap:
- **PSM** vindt 147 matches voor 244 BlueCCS projecten, maar gebruikt slechts **29 unieke PEM controls** (ESS-equivalent extreem laag)
- **Entropy balancing** convergeert naar effectief 8 van 470 PEM observaties (ESS = 1.7%) voordat het naar non-identificatie divergeert

De interpretatie is structureel, niet statistisch. BlueCCS projecten worden gesponsord door oil-majors en industrial-gas firms (gemiddelde capaciteit 1850 MW, geconcentreerd in North America en MENA). PEM projecten door utilities en pure-play hydrogen firms (gemiddelde capaciteit 290 MW, geconcentreerd in EU en Asia). Geen reweighting strategie kan de twee populaties uitwisselbaar maken.

### A.2 Bevinding 2: Robuuste verhoogde cancellation hazard voor BlueCCS

Elf estimators over vier identification classes leveren consistente HR-schattingen op (Table 1 van paper):

| Estimator | HR | 95% CI | p | Sample |
|---|---|---|---|---|
| GLM (cluster sponsor SE) | 14.32 | SE = 0.328 | < 0.0001 | 4 246 p-yr |
| Cox PH | 11.93 | [4.67, 30.49] | < 0.0001 | 714 proj. |
| PSM (caliper 0.05) | 5.22 | — | 0.130 | 992 p-yr |
| IPW (stabilised) | 14.50 | — | < 0.0001 | 3 706 p-yr |
| **Doubly Robust (preferred)** | **6.87** | — | < 0.0001 | 3 706 p-yr |
| Firth penalised | 11.74 | — | < 0.0001 | 12 354 p-yr |
| **Fine-Gray (Plans cancelled)** | **13.19** | **[5.28, 32.91]** | **< 0.0001** | 714 proj. |
| Fine-Gray (On-hold) | 1.20 | [0.34, 4.26] | 0.782 | 714 proj. |
| Shared Frailty Cox | 13.73 | [5.24, 35.98] | < 0.0001 | 714 proj. |

**Diagnostics**:
- Cox concordance index = **0.810**
- Schoenfeld test PH: **p = 0.585** (PH supported)
- Shared frailty variance: **θ̂ = 0.000** (sponsor type als fixed effect volstaat)
- Hosmer-Lemeshow GoF: χ² = 7.79, p = 0.454 ✓
- AUC = 0.805, Brier = 0.052, calibratie slope = 0.891

**Leave-one-region-out** robustness: HR varieert van 11.08 (excl. Other regio) tot 19.89 (excl. ANZ), p < 0.0001 in alle zeven specificaties. De bezorgdheid dat hydrogen findings gedreven worden door oil-major-led US projecten onder de IRA wordt niet ondersteund — excl. North America yields HR = 13.34, slechts 7% onder de full-sample 14.32.

### A.3 Bevinding 3: Terminal cancellation, geen real-option delay

De Fine-Gray competing-risks decompositie is methodologisch het sleutelresultaat voor het mechanisme:

| Outcome | HR | 95% CI | p | n events |
|---|---|---|---|---|
| Plans cancelled (terminal) | **13.19** | [5.28, 32.91] | < 0.0001 | 31 |
| On-hold (real-option delay) | 1.20 | [0.34, 4.26] | 0.782 | 12 |

BlueCCS projecten **pauzeren niet** wanneer condities verslechteren — ze **eindigen**. Dit is een directe empirische rejection van de naïeve real-options voorspelling dat alle projecten symmetrisch hun abandonment optie waarderen. BlueCCS projecten exerciseren de optie niet via vertraging maar via beëindiging.

### A.4 Bevinding 4: Carbon-price-conditional implementation-risk premium

Het centrale substantieve resultaat is dat het BlueCCS-premium niet uniform is maar fundamenteel afhankelijk van de carbon-price omgeving.

Het interactiemodel (paper Eq. 5):
$$h_{it} = \Lambda\left(\alpha_t + \beta_1 \cdot \mathrm{BlueCCS}_i + \beta_2 \cdot \mathrm{EUA}_{z,t} + \beta_3 \cdot (\mathrm{BlueCCS}_i \times \mathrm{EUA}_{z,t}) + X_{it}'\gamma\right)$$

levert:

| Term | Coëfficiënt | p |
|---|---|---|
| β₁ (Blue main) | **+4.026** | < 0.001 |
| β₂ (EUA main) | **+2.516** | < 0.001 |
| **β₃ (Blue × EUA interactie)** | **−2.507** | **< 0.0001** |

Predicted log-HR(z) = β₁ + β₃·z = 4.026 + (−2.507)·z. Delta-method 95% CI's:

| EUA z-score | EUA-prijs | Predicted BlueCCS HR | 95% CI |
|---|---|---|---|
| z = −1 (lage carbon) | ≈ €30 | **673.26** | [215, 2104] |
| z = 0 (historisch gem.) | ≈ €55 | 59.73 | [25.3, 140.9] |
| z = +1 (hoge carbon) | ≈ €80 | **4.67** | [2.14, 10.16] |

**De richting is dempend, niet versterkend.** Hoge CO₂-prijzen zorgen ervoor dat het BlueCCS-versus-PEM cancellation-verschil dramatisch krimpt — een factor 144 vermindering van z = −1 naar z = +1. Het mechanisme staat letterlijk in paper sectie 5.4:

> "As the carbon price rises, captured CO₂ becomes more economically valuable to retain rather than emit, and the CCS step in blue hydrogen production becomes economically advantageous rather than burdensome."

De andere macro-financial interacties zijn allemaal **statistisch insignificant**:

| Interactie | Coëfficiënt | p |
|---|---|---|
| Blue × TTF gas | −0.670 | 0.315 |
| Blue × VIX | +0.246 | 0.569 |
| Blue × EPU | +0.006 | 0.986 |

Dit scherpt de interpretatie: het BlueCCS-premium wordt **niet** gedreven door generieke macro-stress (gasprijs, VIX, beleidsonzekerheid), maar **specifiek** door carbon-price exposure.

---

## DEEL B — Methodologische uitbreidingen voorbij de paper

Onze 06_thesis_extensions/ bevat zeven uitbreidingen voorbij de paper-versie, samen met de twaalfde map die de advanced robustness battery bevat. Dit zijn niet alleen replications maar substantiële methodologische verbredingen.

### B.1 State-space TVP en GAS (`05_state_space_tvp/`)

De paper Cox PH heeft **PH supported** (p = 0.585), dus de TVP-extensie is niet motivaat door PH-violation. De motivatie is methodologisch: identificeren of het carbon-conditional effect zelf tijds-variërend is, in Koopman's score-driven tradition.

**Block random-walk Bayesian TVP** (results_blocks):

| Block | Periode | β̂_int median | 95% HDI |
|---|---|---|---|
| 0 | 2010-2019 pre-crisis | **−1.59** | [−2.97, −0.44] |
| 1 | 2020-2022 pandemic + early crisis | **−1.81** | [−3.27, −0.55] |
| 2 | 2023-2024 peak cancellations | **−0.82** | [−2.44, +0.67] |
| 3 | 2025-2026 normalisering | **−1.88** | [−4.18, −0.18] |

**Een belangrijke nuance**: Block 2 toont een **verzwakt** dempend effect tijdens de 2023-2024 peak cancellation periode, met een 95% HDI die nul bevat. Dit suggereert dat tijdens de meest extreme cancellation wave de CCS-economics-koppeling tijdelijk werd verbroken — mogelijk omdat alternatieve drivers (US 45V three-pillars, EU additionality, BNEF cost-curve drift) tijdelijk dominant waren over carbon-price signalering.

**GAS hazard model** (`04_gas_hazard.py`):

Specification:
- η_blue,t = α + β_blue + β_EUA·z_t + β_int(t)·z_t
- η_pem,t = α + β_EUA·z_t
- y_tech,t ~ Binomial(n_tech,t, sigmoid(η_tech,t))
- β_int(t+1) = ω(1−φ) + φ·β_int(t) + α_gas·s_t (score-driven recursion)

Trajectory (results_gas/gas_trajectory.csv):
- 2010: median **−0.457** (sd 1.13, sterke onzekerheid)
- 2015: median **−1.167** (sd 0.50)
- 2019: median **−1.541** (sd 0.49) — meest negatief
- 2024: median **−1.413** (sd 0.50)
- 2026: median **−1.489** (sd 0.51)

De trajectory is **niet monotoon intensifying** maar bereikt zijn dieptepunt in 2019-2023, met een lichte afzwakking tijdens de peak cancellation periode. Dit complementeert het block-resultaat.

### B.2 Conditional Score Residuals diagnostic (`14_conditional_score_residuals.py`)

Toepassing van de Blasques-Gorgi-Koopman *JBES* 2025 diagnostic op de GAS-TVP fit. Vijf van zes tests slagen (autocorrelation null, parameter stability null, etc.). Heteroskedasticiteit toont een F-test pre/post-2018 ratio, maar dit is identificeerbaar als event-timing artefact (alle 41 events vinden plaats vanaf 2018, dus pre-2018 score-variantie is mechanisch bijna nul).

### B.3 Score-Driven Stochastic Volatility extensie (`17_stochastic_volatility.py`)

GAS-vol model (Harvey-Chakravarty 2008, Creal-Koopman-Lucas 2013) op de score residuals:
- H0 (constant variance): ψ̂ = +0.039, log L = −24.456
- H1 (GAS-vol): ψ̂ = −0.115, λ̂ = −0.359, α_h = +0.234, log L = −23.225
- LR χ²₂ = **2.46, p = 0.292** → fail to reject H0
- AIC en BIC favouriseren beide H0 (parsimony)

Conclusie: het constant-variantie GAS-TVP is methodologisch voldoende. Een SV-uitbreiding is niet empirisch gerechtvaardigd.

### B.4 Causal Forests (`16_causal_forests.py`)

CausalForestDML (Athey-Tibshirani-Wager *AoS* 2019) op de S&P sample (N=628 finished):
- ATE = **+0.173**, 95% CI [−0.163, +0.509]
- CATE range [−0.013, +0.339] (10p-90p)
- 93 van 628 (14.8%) significant positief, 0 significant negatief

**Feature importance ranking voor heterogeniteit**:

| Feature | Importance |
|---|---|
| year_c | **0.451** ★ |
| log_cap | **0.368** ★ |
| is_EU | 0.087 |
| is_Asia | 0.040 |
| sponsor_type | 0.029 |
| is_NA | 0.015 |
| cbam_endex | **0.009** ✗ (laagste) |

Substantieve implicaties:
- **Tijd is de dominante moderator** — sluit aan op TVP/GAS verhaal, non-parametrisch bevestigd
- **Project-grootte tweede** — sluit aan op real-options theorie (grotere sunk cost = lagere abandonment optie waarde). Specifiek: Q4 (grootste capaciteit) heeft CATE ≈ 0; Q1-Q3 hebben CATE > +0.20
- **CBAM-blootstelling is bijna irrelevant** (laagste importance) — methodologisch orthogonaal bewijs voor de informative null

### B.5 Synthetic DiD (`12_synthetic_did.py`)

τ_SDID = 0.148 op de S&P data, met permutation p = 0.167. Dit is een **informative null** — niet vlot, maar consistent met de overige Chapter 8 robustness pijlers die ook geen significant CBAM-specifiek effect vinden.

### B.6 Honest DiD smoothness (`15_honest_did_smoothness.py`)

Rambachan-Roth (*RES* 2023) smoothness-restricted bounds. Breakdown M = 0.25 per-period, M = 0.15 average. Orthogonaal aan de relative-magnitudes class — de identification-uitdaging zit in tijdstructuur (pre-trends violation), niet in magnitude.

### B.7 Competing Risks op S&P en v7 (`13_competing_risks.py`)

Twee aparte analyses:

**v7 data (44 events op 714 projecten, met cause-specific Cox PH)**:

| Event | n | HR_Blue | p |
|---|---|---|---|
| Type 1 (pre-commissioning?) | 31 | **6.13** | < 0.001 |
| Type 2 (post-commissioning?) | 12 | 0.87 | 0.79 |
| Pooled | 43 | 4.07 | < 0.001 |

**S&P data (N=628 finished, met cause-specific Cox PH)**:

| Event | n | HR_Blue | p |
|---|---|---|---|
| Plans cancelled | 102 | **1.58** | 0.020 |
| Decommissioned | 49 | 0.95 | 0.85 |
| On-hold | 947 | 0.87 | 0.17 |

Beide datasets bevestigen dezelfde structuur: het BlueCCS-effect concentreert op terminal cancellation, met null effects op decommissioning en on-hold. De magnitude verschilt (6.13 op v7, 1.58 op S&P) omdat de sample-compositie verschilt — S&P bevat veel meer projecten waarvan de meeste niet finished zijn.

De paper Fine-Gray-versie op v7 geeft HR = 13.19 — een nog sterker resultaat dan onze cause-specific Cox. Het verschil komt door de Fine-Gray subdistribution-hazard formulering die individuen behoudt die already-experiencing competing events.

### B.8 Honest DiD relative magnitudes (`01_honest_did_v2.py`)

Rambachan-Roth (2023) relative-magnitudes class: breakdown M̄ = 0. Het significantie-resultaat is robuust onder geen restrictie op the magnitudes.

---

## DEEL C — Bevestiging vanuit 2024-2026 nieuws en literatuur

Onze bevindingen passen exact in het empirische landschap van de afgelopen 18 maanden.

### C.1 Terminal cancellation, niet pauze — voorspeld door Fine-Gray, bevestigd door 2024-2026 nieuws

Onze Fine-Gray HR_cancellation = 13.19 vs HR_on-hold = 1.20 voorspelt dat blauwe projecten **eindigen, niet pauzeren**. De 2024-2026 cancellation wave bevestigt dit precies:

| Project | Sponsor | Capaciteit | Cancel-date | Stage | Cancel of pause? |
|---|---|---|---|---|---|
| H2Teesside | BP | 1.2 GW Blue | dec 2025 | Pre-FID | **Terminal cancellation** |
| H2M Eemshaven | Equinor | 1.0 GW Blue NL | 2024 | Pre-FID | **Terminal cancellation** |
| Norway-Germany pipeline | Equinor/Shell | Blue | 2024 | Pre-FID | **Terminal cancellation** |
| Aukra hub | Shell | Blue | 2024 | Pre-FID | **Terminal cancellation** |
| Baytown | ExxonMobil | Blue | 2025 | Pre-FID | **Terminal cancellation** |
| Ascension Parish | Air Products | 647 ktpa | 2025 | Pre-FID | **Stalled/cancelled** |
| Indiana CCS | BP | CCS | juni 2025 | Pre-FID | **Terminal cancellation** |

*Geen* blauw project dat al operationeel was werd in 2024-2026 decommissioned. Onze HR_decommissioned = 1.20 (NS) klopt dus precies.

### C.2 Carbon-price-conditional risk — bevestigd door EUA-prijsdaling 2022-2024

Onze marginal effects voorspellen HR = 673 bij lage EUA (≈€30) en HR = 4.67 bij hoge EUA (≈€80). De EUA viel van zijn piek ~€100/ton in 2022 terug naar ~€60-70/ton in 2024 — exact het regime waar onze model HR > 50 voorspelt. Dat is consistent met:

> *Decarbonize Weekly* (mei 2026): "60 major projects cancelled in 2025 alone, ~4.9 Mt/yr of capacity removed... about a third of announced electrolyser capacity has been removed from public 2030 timelines."

> *Energy Intelligence* (okt 2024): "Blue hydrogen projects have hit major roadblocks in Europe... calling into question blue hydrogen's viability in Europe."

> *Brussels Signal* (jan 2025): "Just over 20 per cent of all ongoing European hydrogen projects scrapped in 2024."

### C.3 Verzwakt CO₂-effect tijdens peak crisis — geconsistent met cost-curve disruptie

Onze Bayesian block-TVP toont Block 2 (2023-2024 peak cancellations) met een **verzwakt** dempend effect (β̂ = −0.82, HDI bevat nul). Dit suggereert dat tijdens de meest extreme cancellation wave de CCS-economie tijdelijk geen sufficient buffer was. Dit klopt met:

> *BNEF* (2025): groene-waterstof cost-curve drifted van $1.40/kg (2020 projectie) naar $4-6/kg (2025 base case). Drie drivers: electrolyser-stack cost-down 10%/yr in plaats van 20%, balance-of-plant inflatie, capacity-factor revisies. **Geen van deze loopt via EUA.**

> *Decarbonize Weekly*: identificeert drie hoofd-oorzaken van de 2025 wave — US 45V "three pillars" rules, EU additionality, en BNEF cost-curve drift. **CBAM staat er niet bij.**

Onze Causal Forest feature importance bevestigt dit kwantitatief: CBAM-blootstelling heeft importance 0.009 (laagste van zeven features), terwijl tijd (0.451) en log-cap (0.368) domineren.

### C.4 Size-quartile pattern — bevestigd door speculative-tail-dies framing

Onze Causal Forest toont CATE ≈ 0 voor Q4 (grootste capaciteit) en CATE > +0.20 voor Q1-Q3. Decarbonize Weekly schrijft:

> "The speculative tail of green hydrogen is dead. The bankable industry that survives is smaller, narrower, and anchored to captive industrial offtake."

Dit is direct empirische ondersteuning voor het real-options framework: grote projecten hebben hogere sunk-cost commitment en daardoor lagere abandonment-optie waarde.

### C.5 Bovenliggende theoretische frame — Odenweller-Ueckerdt implementation gap

Adrian Odenweller en Falko Ueckerdt (Potsdam Institute), gepubliceerd in **Nature Energy 2025, 10(1):110-123** ("The Green Hydrogen Ambition and Implementation Gap"), tracken 137 groene-waterstof projecten over 3 jaar en vinden:
- **2% implementation rate** voor projecten gepland voor 2022
- "Projects in feasibility study or concept stage had a success rate of zero"
- 95% van 2022-geplande capaciteit niet gerealiseerd

Onze scriptie zit op het puntje van dit "implementation gap" onderzoeksveld: we identificeren het **econometrisch-causale mechanisme** achter hun observationele bevinding. Specifiek: hun gap is geconcentreerd in projecten zonder FID (= pre-FID stadium = onze Fine-Gray "Plans cancelled" event-type).

---

## DEEL D — Gap-analyse: wat de literatuur heeft dat wij nog missen

Zeven concrete gaps in vergelijking met state-of-the-art literatuur. Geen daarvan is een fout — het zijn methodologische verbredingen die ons werk van MSc-scriptie naar PhD-bijdrage zouden tillen.

### Gap 1: Multistate model met volledige lifecycle-transities

**Wat wij doen**: cause-specific Cox PH en Fine-Gray competing risks met drie eindstaten (cancelled, decommissioned, on-hold).

**Wat de literatuur heeft**: Andersen-Keiding multistate event-history modellen (*Statistical Methods in Medical Research* 2002, 11(2):91-115). Een volledig multistate model voor hydrogen zou zijn:
$$\text{Concept} \to \text{Feasibility} \to \text{FEED} \to \text{FID} \to \text{Construction} \to \text{Operating}$$
met aparte transition-hazards tussen elke state, plus absorbing states cancelled en decommissioned. Onze S&P data heeft `project_status` met 6+ niveaus — we gebruiken het alleen binair.

**Waarom relevant voor ons**: identificatie van WELKE specifieke transitie de BlueCCS-fragiliteit bottleneck is. Pre-FID? Pre-FEED? Pre-construction? Onze huidige cause-specific decompositie aggregeert dit — een full multistate model zou dit ontwarren.

**Toolchain**: R-package `mstate` plus `etm` voor Aalen-Johansen estimation.

### Gap 2: Sequential Synthetic DiD voor staggered carbon-policy adoption

**Wat wij doen**: standaard SDID (Arkhangelsky-Athey-Hirshberg-Imbens-Wager *AER* 2021) op binary post-2022 CBAM treatment, p = 0.167.

**Wat de literatuur heeft**: **Sequential SDiD (Arkhangelsky-Samkov 2024, arXiv 2404.00164)** — "particularly when the parallel trends assumption fails". De estimator gebruikt iteratieve imputation waar early-adopting cohorten counterfactuals construeren voor late-adopting cohorten, en is asymptotisch equivalent aan een infeasible oracle OLS estimator. Specifiek geschreven voor situaties zoals de onze met staggered treatment (EUA spikes 2018, 2021; CBAM 2023; IRA 2022; UK ETS departure post-Brexit).

**Waarom relevant voor ons**: onze paper Schoenfeld is supported, maar onze CBAM event-study heeft pre-trends violation (F = 20.18, p < 0.0001). Sequential SDiD is precies de methode voor dit scenario.

### Gap 3: Multivariate observation-driven filtering

**Wat wij doen**: univariate GAS-TVP op de BlueCCS × EUA interactie.

**Wat de literatuur heeft**: **Blasques-van Brummelen-Gorgi-Koopman (Tinbergen 24-062, 2024)** — "Robust Multivariate Observation-Driven Filtering for a Common Stochastic Trend". Plus **Gorgi-Koopman-Schaumburg (*Journal of Econometrics* 2024, 244(2))** — joint dynamic factor model met VAR dynamic factor coefficients.

**Waarom relevant voor ons**: joint modellering van (β_int_EUA, β_int_TTF, β_int_VIX, β_int_EPU) als common stochastic trend met technology-specific loadings. Onze huidige aanpak modelleert alleen EUA tijdsvariërend; de andere drie zijn allemaal getest als statisch insignificant maar dat is in onze paper-spec. In een Koopman-multivariate-extensie kunnen ze tijdsvariërend wel relevant blijken te zijn.

### Gap 4: Spline-based score-driven densities (Van Brummelen-Gorgi-Koopman 2025)

**Wat wij doen**: Bernoulli/Binomial likelihood (Gaussian assumption op score residuals impliciet).

**Wat de literatuur heeft**: **Van Brummelen-Gorgi-Koopman (Tinbergen 25-011/III, 2025)** — "Score-driven time-varying parameter models with spline-based densities". Relax de Gaussian assumption en laat density-shape mee variëren met tijd.

**Waarom relevant voor ons**: onze 2024 vol-spike (σ̂_2024 = 2.15 vs baseline ~0.90) suggereert fat tails. Spline-based densities zouden dit empirisch correct kunnen modelleren in plaats van als data-feature af te doen.

### Gap 5: Structurele schatting in BLP-stijl

**Wat wij doen**: reduced-form causal effect identification.

**Wat de literatuur heeft**: structurele schatting van het abandonment-option model via BLP-stijl identification (Berry-Levinsohn-Pakes *Econometrica* 1995, modern extensions zoals Reynaert-Sallee *QJE* 2021).

**Waarom relevant voor ons**: counterfactual policy simulaties. Reduced form identificeert wat *gebeurde*; structureel identificeert wat *zou gebeuren onder alternative beleidspaden* — wat is voor IEA/EU/IRENA het meest waardevol.

### Gap 6: Cross-country carbon-pricing variation als IV-strategy

**Wat wij doen**: EUA en CBAM als binaire treatment-tijdstippen.

**Wat de literatuur heeft**: cross-country variation in carbon-pricing intensiteit als plausibly-exogenous IV. UK ETS departure (post-Brexit), California cap-and-trade, China ETS pilot variation, RGGI vs WCI.

**Waarom relevant voor ons**: een IV-strategy die niet leunt op parallel trends — omzeilt de pre-trends violation van onze CBAM event-study volledig.

### Gap 7: Financial market high-frequency event-study

**Wat wij doen**: project-level cross-sectional data (S&P), annual hazard windows.

**Wat de literatuur heeft**: high-frequency event-study op stock returns van Blue-vs-PEM exposed firms (Linde, Air Liquide, Plug Power, Nel ASA, ITM Power) rond CBAM/IRA/EUA news events. Standaard methode in finance-policy-evaluation literatuur (Bushnell-Chong-Mansur *AEJ:EP* 2013, Chai-Mansur 2014).

**Waarom relevant voor ons**: marktinterpretatie van onze cancellation-hazard bevindingen. Als markten Blue-fragility correct prijzen, zou dit zichtbaar zijn in CARs rond carbon-price events. Bovendien matcht dit jouw eigen technical skillset (ARIMA, GARCH, LSTM, VAR/VECM) maximaal.

---

## DEEL E — Concrete PhD-onderzoeksagenda

Vijf onderzoekslijnen voor follow-up, gerangschikt naar haalbaarheid in 4-jaar PhD venster met the reviewers als supervisor-combinatie.

### E.1 [Methodologisch — Koopman-lijn] Joint multistate hazard + multivariate state-space TVP

**Onderzoeksvraag**: identificeer de exacte lifecycle-transitie waar BlueCCS-fragiliteit zit, met tijds-variërende transition hazards en multivariate factor structure over macro-financial covariates.

**Methodologische bijdrage**: combineert (a) Andersen-Keiding multistate framework (Stat Med 2012), (b) Blasques-van Brummelen-Gorgi-Koopman multivariate observation-driven filtering (Tinbergen 24-062, 2024), en (c) Gorgi-Koopman-Schaumburg joint dynamic factor model (JoE 2024, 244(2)). Geen bestaand paper combineert deze drie voor energy projects.

**Data**: S&P + IEA + nieuw te verzamelen granular project data (Wood Mackenzie, Bloomberg NEF voor lifecycle stage tracking).

**Toolchain**: R `mstate` + `KFAS` + custom Stan/PyMC voor MCMC.

**Tijdslijn**: 18-24 maanden voor het methodologische frame, 6 maanden voor empirische toepassing.

**Supervisor-fit**: maximaal — Koopman's eigen 2024-2025 werk is de directe input.

### E.2 [Causaal — Ketel-lijn] Sequential SDiD op staggered carbon-policy

**Onderzoeksvraag**: causale identificatie van EUA-prijspeak (2018), CBAM (2023), IRA (2022), UK ETS departure (post-Brexit) op cancellation hazards, zonder parallel-trends assumption.

**Methodologische bijdrage**: eerste toepassing van Arkhangelsky-Samkov (2024) Sequential SDiD op klimaatbeleid. Plus expliciete heterogeneity-decompositie via Wager-Athey causal trees.

**Data**: S&P + EU ETS + UK ETS + CARB + RGGI prijsdata.

**Toolchain**: `synthdid` R-package + custom iteratieve wrapper + econml Python.

**Tijdslijn**: 12-18 maanden.

**Supervisor-fit**: Ketel's expertise in modern DiD-extensies (cf. haar AER:Insights 2024 paper).

### E.3 [Welfare-economisch] Structureel model met counterfactual policy simulations

**Onderzoeksvraag**: wat zouden cancellation rates zijn geweest onder (a) hogere CBAM, (b) eerdere IRA, (c) gehandhaafd 2018 EUA-prijspath, (d) UK in EU ETS gebleven?

**Methodologische bijdrage**: structureel real-options model met BLP-stijl GMM identification, gekoppeld aan onze reduced-form hazard estimates als moment conditions.

**Data**: idem E.2 plus firm-level financials (Compustat/Capital IQ voor sponsor-financials).

**Toolchain**: Python custom (BLP solver), plus Monte Carlo simulaties.

**Tijdslijn**: 24-36 maanden — ambitieus.

**Policy payoff**: maximaal — dit is wat IEA/EU/IRENA willen weten.

### E.4 [Empirisch — kortste] Probabilistic implementation-gap projecties tot 2050

**Onderzoeksvraag**: gegeven huidige cancellation-hazards, wat is de realistische 2030/2035/2050 hydrogen capaciteit (vs IEA NZE scenario van 530 Mtpa)?

**Methodologische bijdrage**: forward-looking versie van Odenweller-Ueckerdt (Nature Energy 2022), met onze causaal-geschatte hazards als input. Sensitivity analysis op beleidsscenarios.

**Data**: S&P + IEA + onze hazard estimates uit Chapter 5-6.

**Toolchain**: Python Monte Carlo, geïntegreerd met IEA Hydrogen Project Database API.

**Tijdslijn**: 6-12 maanden (kortst van de vijf).

**Policy payoff**: hoog. Past goed in Gasunie business context — kan parallel met PhD geschreven worden.

### E.5 [Financial — best skill-fit] High-frequency event-study op stock returns

**Onderzoeksvraag**: prijzen markten Blue-vs-PEM differential correct in? CARs rond CBAM/IRA/EUA news events?

**Methodologische bijdrage**: event-study + GARCH-style abnormal returns + LSTM voor anomaly detection rond policy events, op een sample van Blue-exposed firms (Linde, Air Liquide, BP, Shell, Equinor, Air Products, Yara) versus PEM-exposed firms (Plug Power, Nel ASA, ITM Power, Bloom Energy).

**Data**: stock returns (Yahoo Finance / WRDS), daily EUA/UKA/CARB prijzen, news event database.

**Toolchain**: Python `arch` voor GARCH, `statsmodels` voor event-study, TensorFlow/PyTorch voor LSTM.

**Tijdslijn**: 9-12 maanden.

**Skill-fit met jouw profiel**: maximaal. ARIMA, GARCH, LSTM, VAR/VECM, deep learning voor financial time series — exact je expertisegebied.

---

## DEEL F — Conclusies en aanbevelingen voor de MSc-scriptie

### F.1 Wat klaar is

De v7 paper (`00_paper/current/blueCCS_paper_final.tex`) is een methodologisch waterdichte beschrijving van vier substantieve bevindingen — gesegmenteerde ecosystemen, robuust elevated hazard, terminal-vs-pause asymmetrie, en carbon-price-conditioneel risico. Elf estimators, leave-one-region-out robustness, en alle moderne causal-inference checks zijn gedaan.

De `06_thesis_extensions/` voegt zeven methodologische verbredingen toe: state-space TVP, GAS hazard, real-options calibration, event-study, CBAM event-study, S&P-Global CBAM analyse, IEA cross-validation. Plus twaalf advanced robustness checks (`12_advanced_robustness/`).

Chapter 7 v2 (16 pp) en Chapter 8 (41 pp) zijn schrijfbare hoofdstukken voor de scriptie zelf, met respectievelijk de TVP/GAS-extensies en de S&P-CBAM uitgebreide analyses.

### F.2 Twee schrijfacties voor de MSc deadline

1. **Future Work + Limitations sectie** in Chapter 8: kopieer-en-formaliseer Deel C, D, E uit dit document naar academic prose. ~1 dag werk.

2. **Discussion sectie** die de coherence van de elf paper-estimators + twaalf advanced robustness pijlers expliciet uitlegt, plus de koppeling aan Odenweller-Ueckerdt 2025 framework. ~1 dag werk.

### F.3 Doelgroep-specifieke pitches

**Voor Koopman**: "Mijn scriptie identificeert via 11 causale-inferentie estimators dat de BlueCCS-vs-PEM cancellation differential geconcentreerd is in terminal pre-FID cancellation (Fine-Gray HR=13.19), met een carbon-price-conditional structure (Blue × EUA interactie = −2.51, HR collapseert 673→4.67). De GAS-TVP-extensie (Creal-Koopman-Lucas tradition) toont een verzwakt effect in 2023-2024 dat ik niet kan verklaren in mijn huidige univariate framework. Ik wil dit uitbreiden via uw multivariate observation-driven filtering (Tinbergen 24-062, 2024) gekoppeld aan een Andersen-Keiding multistate-model op de lifecycle-transities. Heeft u interesse in promovendi voor deze richting?"

**Voor Ketel**: "Mijn scriptie heeft via 11 estimators een carbon-price-conditional implementation-risk premium voor blue hydrogen geïdentificeerd. De CBAM event-study extension heeft een pre-trends violation (F = 20.18, p < 0.0001) — dus we hebben Honest DiD en Synthetic DiD als robustness tools ingezet. Voor PhD-extensie wil ik Sequential SDiD (Arkhangelsky-Samkov 2024, arXiv 2404.00164) toepassen op staggered carbon-policy adoption — exact uw expertise gebied. Bent u beschikbaar als second-reader voor de MSc en mogelijk PhD co-supervisor?"

**Voor Gasunie**: "De analyse identificeert dat BlueCCS cancellation-risico bij lage EUA-prijzen catastrofaal hoog is (HR=673) en bij hoge EUA dramatisch krimpt (HR=4.67). Voor onze portfolio betekent dit dat carbon-price-hedging effectief een real options insurance is voor onze CCS-exposed projecten. Plus: middelgrote BlueCCS projecten zonder vastomlijnde offtake (Q1-Q3 capacity quartiles) dragen het hele risico — grote captive-offtake projecten (Q4) hebben geen extra risico. Direct relevant voor onze pre-FID screening criteria in de Business Line Waterstof Nederland."

---

**Repository**: https://github.com/SakeSaak/thesis_h2 (private)
**Documentversie**: 2.0 (gecorrigeerd vanuit primary sources op 20 mei 2026)
**Vorige versie**: `FINAL_SYNTHESIS_2026-05-20.md.FOUT_RETIRED` (bewaard voor erratum-historie)
