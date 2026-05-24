# GAP ANALYSE v4 — POST-THESIS-DRAFT STRATEGISCHE BEOORDELING

**Auteur**: Sake Saakstra
**Datum**: 21 mei 2026
**Status**: Na voltooiing thesis_v1 draft (22.443 woorden, 90 pp PDF)
**Doel**: Identificeren wat nog kan/moet verbeteren voor v2 (supervisor-feedback iteratie) en wat als PhD-uitbreidingsmateriaal kan dienen
**Vorige versie**: `GAP_ANALYSIS_v3_STAKEHOLDERS_2026-05-20.md` (gefocust op stakeholder-waarde)

---

## EXECUTIVE SUMMARY

De thesis-draft v1 is empirisch en methodologisch substantieel: 1.354 projecten, vier carrot-policies, het offtake-mechanisme als nieuwe bevinding, vijf counterfactual-scenarios, een real-options theoretisch kader. Tracks A+B+C (Pijler 30-40) hebben de grootste v3-gaps gesloten — offtake-effect (gap 1), counterfactual (gap 2), Honest DiD (gap 7), real-options × mechanism design (gap 6).

**Wat staat nu**:
- ✅ 7 publication-grade findings, 5 robust + 2 qualified
- ✅ Methodologische triangulatie binnen elke claim
- ✅ Theoretisch kader sluit aan op empirie
- ✅ Externe validatie via 2024-26 cancellation-wave

**Vier categorieën gaps voor v2**:
1. **Andere papers/research** — actuele literatuur die we missen (~12 papers)
2. **Aansluiting Koopman expertise** — GAS-models, DFM, particle filtering (4 specifieke methoden)
3. **Aansluiting Ketel expertise** — synthetic control, RDD, marginal treatment effects (3 methoden)
4. **Econometrische modellen** — competing risks, multi-state, spatial, Bayesian model averaging (5 modellen)
5. **Nieuws en events** — wat is er gebeurd na onze 24-maart 2024 S&P snapshot

**Prioritering**:
- **MUST voor v2** (voor supervisor-feedback): synthetic control, competing risks, GAS-model voor TVP, recent literatuur-update — 4 items, ~3 weken werk
- **SHOULD voor PhD-uitbreiding**: dynamic factor model, multi-state survival, RDD CBAM, particle filtering — 4 items, ~2 maanden werk
- **COULD voor nice-to-have**: spatial econometrie, Bayesian model averaging — 2 items, ~1 maand werk

---

## CATEGORIE A: ANDERE PAPERS EN RESEARCH

### A.1 Wat we citeren (huidige references.bib — 42 entries)

We hebben de canonical literatuur op orde voor:
- Hydrogen empirisch: Odenweller 2025, Ueckerdt 2024, IEA, Hydrogen Council
- Real-options: Dixit-Pindyck 1994, Pindyck 1991, Fuss 2012, Barradale 2014
- Modern DiD: Sun-Abraham 2021, Borusyak 2024, Callaway 2021, Goodman-Bacon 2021
- Honest sensitivity: Rambachan-Roth 2023, Roth 2022
- Selectie: Oster 2019, Altonji 2005
- Adjacent clean energy: Bento 2018, Aldy 2016, Popp 2010
- Survival: Cox 1972, Grambsch 1994, Hosmer 2013
- State-space: Durbin-Koopman 2012, Creal-Koopman-Lucas 2013

### A.2 Specifieke papers die we MISSEN en zouden moeten lezen

**Hoge prioriteit (must-cite voor credibility)**:

1. **Glenk & Reichelstein (2022) — "The economic dynamics of competing power generation sources"** in Renewable & Sustainable Energy Reviews. Geeft levelized-cost framework voor hydrogen vs alternatieven, citeerbaar in Chapter 4 (data) en Chapter 8 (offtake-mechanism).

2. **Klemun, Trancik et al. (2023) — "Empirically grounded technology forecasts and the energy transition"**. MIT-team, geeft methodologisch framework voor announce-vs-realisatie gap dat ons werk complementeert. Citeerbaar in Chapter 1 (motivatie).

3. **Brandt et al. (2024) — "Renewable hydrogen vs. natural gas: lifecycle and economic competitiveness"**. Lifecycle-perspective dat onze cost-arbitrage interpretatie ondersteunt.

4. **Sant'Anna & Zhao (2020) — "Doubly robust difference-in-differences estimators"** in Journal of Econometrics. Aanvulling op onze DiD-toolkit. Mogelijk citeerbaar in Chapter 5 (methodology) ter onderbouwing van IPWRA-keuze.

5. **Abadie (2021) — "Using synthetic controls: feasibility, data requirements, and methodological aspects"** in Journal of Economic Literature. Onmisbaar als we synthetic control toevoegen (zie Categorie D).

6. **de Chaisemartin & D'Haultfœuille (2024) — "Two-Way Fixed Effects and DiD with Heterogeneous Treatment Effects: A Survey"** in Econometrics Journal. Up-to-date review die onze methodologische keuzes contextualiseert.

**Medium prioriteit (versterkt theoretical framework)**:

7. **Bolton & Kacperczyk (2021) — "Do investors care about carbon risk?"** in Journal of Financial Economics. Onze theoretical framework refereert er al naar, maar verdient diepere bespreking in Chapter 3.

8. **Acemoglu, Aghion, Bursztyn, Hemous (2012) — "The environment and directed technical change"** in AER. Foundationeel paper voor argumentatie dat mechanism design innovation-paden vormgeeft.

9. **Newell & Stavins (2003) — "Cost heterogeneity and the potential savings from market-based policies"**. Relevant voor onze sector-heterogeniteit bevindingen (Chapter 8.4).

10. **Hafstead & Williams (2018) — "Unemployment and environmental regulation in general equilibrium"** in Journal of Public Economics. Voor de discussie over arbeidsmarkt-effecten van mechanism keuze.

**Specifiek voor hydrogen, recent**:

11. **Princeton's "Net Zero America" project follow-ups (2024-2025)** — vooral Jenkins-team publicaties over IRA implementatie en hydrogen-specifieke modeling. Externe validatie van onze counterfactual-scenarios.

12. **IEA Global Hydrogen Review (laatste editie)** — naast 2024 versie ook 2025 update controleren. Mogelijke benchmark voor onze cancellation-statistieken.

**Verifiëren post-cutoff (januari 2026+)**:

- Of er sinds januari 2026 nieuwe top-tier publicaties zijn in:
  - Nature Energy
  - Joule
  - Energy Economics
  - Environmental & Resource Economics
  - Energy Policy
- Specifiek zoeken naar: "hydrogen cancellation", "green hydrogen FID", "EU Hydrogen Bank evaluation"

### A.3 Concrete actie

**Voor v2**:
- Voeg 6 high-priority papers toe aan literatuurreview (Chapter 2)
- Update references.bib met 12 nieuwe entries
- In Chapter 2, voeg een subsection toe "Recent industry analyses" die onze findings positioneert tegen 2024-2026 industry-tracking literatuur

**Voor PhD-uitbreiding**:
- Systematic literature review (PRISMA-stijl) van hydrogen-policy evaluatie 2015-2026
- Identificeer onze contribution explicit in een Venn diagram

---

## CATEGORIE B: AANSLUITING BIJ KOOPMAN EXPERTISE

### B.1 Wat Koopman's onderzoeksprofiel is

Prof. the external reviewer is een wereldautoriteit op:
- **State-space modelling** (boek met Durbin, *Time Series Analysis by State Space Methods*, OUP 2012)
- **Generalized Autoregressive Score (GAS) models** (Creal-Koopman-Lucas 2013, JAE; uitbreiding observation-driven framework)
- **Dynamic factor models** (uitgebreid werk in macro-economische nowcasting)
- **Particle filtering** voor non-Gaussian state-space (Koopman-Lucas-Scharth 2016, REStat)
- **Robust score-driven models** (Blasques-Koopman-Lucas, recente werken)
- **Tinbergen Institute** affiliatie en gerelateerde dissertaties

### B.2 Wat we WEL hebben gedaan dat aansluit

✅ **Bayesiaanse TVP-DiD via state-space** (Pijler 24c, Chapter 7) — drie state-space specificaties (threshold, AR(1), random walk) met MCMC-inferentie. Dit is een direct toepassing van Koopman-stijl methodologie.

✅ **Kalman filter implementatie** voor de AR(1) specificatie.

✅ **Structurele breuk-detectie** rond τ*=2020 via state-space.

### B.3 Wat we MISSEN en zou Koopman waarderen

**Hoge prioriteit (versterkt Chapter 7 substantieel)**:

**B.3.1. Score-driven (GAS) model voor TVP-DiD**

Onze huidige TVP-DiD heeft drie *parameter-driven* state-space specificaties. Het GAS-framework (Creal-Koopman-Lucas 2013) biedt een *observation-driven* alternatief waarin de tijdsvariërende parameter $\beta_t$ wordt aangedreven door de score van de likelihood:

$$\beta_{t+1} = \omega + \alpha s_t + \rho \beta_t$$

waar $s_t \propto \partial \log L_t / \partial \beta_t$. Dit heeft drie voordelen:
- Single estimator zonder MCMC (efficiency)
- Directe robuustheid via score-clipping (Blasques et al.)
- Natuurlijke koppeling met heavy-tailed conditional distributions

**Substantieel voordeel voor de thesis**: dit is *literally* Koopman's expertisegebied. Een GAS-implementatie naast onze drie parameter-driven specificaties zou:
- Hem direct in zijn comfort-zone trekken
- Een vierde robuustheid-check toevoegen voor de τ*=2020 structurele breuk
- De methodologie elevateren van "applied" naar "in dialogue with the methodological frontier"

**Concrete implementatie**: ~3-5 dagen werk, met behulp van `score-driven` Python implementaties (R `gas` package, of `pyssm`/`statsmodels` extensions).

**B.3.2. Dynamic factor model voor cross-jurisdictie**

Onze vier carrot-policies (US 45Q, EU IF, UK Track-1, China FYP) worden nu *separately* gemodelleerd. Een DFM zou ze als gemeenschappelijke factor + jurisdictie-specifieke loadings karakteriseren:

$$Y_{ijt} = \alpha_i + \gamma_t + \lambda_j F_t + \beta_j D_{ijt} + \epsilon_{ijt}$$

waar $F_t$ een onderliggende latente policy-stringency factor is. Dit:
- Identificeert *gemeenschappelijke* drivers van cross-jurisdictie variatie
- Levert een gestructureerde manier om "wereldwijde hydrogen-policy klimaat" te meten
- Past direct op Koopman's DFM-expertise

**Implementatie**: ~1-2 weken werk via `statsmodels.tsa.statespace.DynamicFactor` of EM-algoritme. Mogelijk te ingrijpend voor v2; meer geschikt voor PhD-uitbreiding.

**B.3.3. Particle filtering voor non-Gaussian residuals**

Onze huidige state-space veronderstelt Gaussian observations. De binary nature van project-failure outcomes maakt dit oneigenlijk. Een particle filter (sequential Monte Carlo) zou:
- Correcte non-Gaussian likelihood (e.g. binomial)
- Volledig respect voor de discrete uitkomstvariabele
- Aansluiten op Koopman-Lucas-Scharth (2016, REStat)

**Implementatie**: ~2-3 weken werk. Aanbevolen voor PhD-uitbreiding, niet v2.

**B.3.4. Forecasting accuracy / predictive validation**

Een verrassend gap: we hebben *causale* identificatie maar geen *predictive* evaluatie. Koopman is groot in forecast-accuracy framework (RMSE, Diebold-Mariano, model confidence sets). Voor de TVP-DiD zouden we kunnen:
- Out-of-sample forecast van failure-hazards
- Diebold-Mariano test tussen onze drie state-space specificaties
- Model Confidence Set (Hansen-Lunde-Nason 2011) om predictively-superior specificatie te identificeren

**Implementatie**: ~1 week werk, hoog rendement voor Koopman's perceptie van de thesis als "methodologically complete".

### B.4 Concrete actie

**MUST voor v2 (kritiek voor Koopman-feedback)**:
- GAS-model implementatie naast huidige drie state-space specificaties (Pijler 41a)
- Diebold-Mariano forecast-comparison tussen de vier (inclusief GAS)
- Sectie 7.X toevoegen "Predictive validation"

**SHOULD voor PhD-uitbreiding**:
- Dynamic factor model voor 4-policy gemeenschappelijke factor
- Particle filter voor binary outcomes

**Verwachting Koopman-respons**: zonder GAS-model en forecasting is hoofdstuk 7 vanuit zijn perspectief incompleet. *Met* die toevoegingen zit het in zijn expertise-comfortzone en wordt het waarschijnlijk zijn favoriete hoofdstuk.

---

## CATEGORIE C: AANSLUITING BIJ KETEL EXPERTISE

### C.1 Wat Ketel's onderzoeksprofiel is

Dr. the second reviewer is gespecialiseerd in:
- **Causale identificatie** in arbeidsmarkt-economie
- **Field experiments en RCTs**
- **Beleidsevaluatie** met natural experiments
- **Panel-data econometrie**
- Werk gepubliceerd o.a. in *American Economic Review*, *Journal of Public Economics*

### C.2 Wat we WEL hebben dat aansluit

✅ **Multi-method causal identification** voor offtake-effect (Pijler 34, Chapter 8) — LPM, PSM, IPWRA, Oster, sector-LPM
✅ **Modern DiD methodology** (Chapter 6) — TWFE, Sun-Abraham, BJS-imputation
✅ **Honest sensitivity bounds** (Chapter 6) — Rambachan-Roth
✅ **Oster (2019) selection-on-unobservables** — δ_null = 20.23 voor offtake

### C.3 Wat we MISSEN en zou Ketel waarderen

**Hoge prioriteit (cruciaal voor Ketel-credibility)**:

**C.3.1. Synthetic Control Method (Abadie 2010, 2021)**

Voor de UK Track-1 case (Chapter 6) waar we een selectie-funnel artefact identificeren, zou Synthetic Control een powerful alternatief zijn:
- Construeer een synthetic "UK zonder Track-1" als gewogen combinatie van controle-regio's
- Vergelijk werkelijke UK-trajectorie met synthetic counterfactual
- Levert visueel sterk argument voor selection-funnel narrative

**Implementatie**: ~1 week. Python `pysyncon` of R `Synth` package. Hoog rendement voor de UK-case en EU IF null result.

**C.3.2. Augmented Synthetic Control (Ben-Michael, Feller, Rothstein 2021)**

Recente uitbreiding van SCM die ridge regression toevoegt voor wanneer de pre-treatment fit incompleet is. Past beter bij ons N=1.354 design.

**C.3.3. Regression Discontinuity Design (RDD) bij CBAM-thresholds**

Het CBAM-mechanisme (Chapter 8 in oorspronkelijke draft, mogelijk te integreren in appendix) heeft een eligibility threshold (carbon intensity). Een sharp RDD rond die threshold zou:
- Quasi-experimental identificatie zonder DiD-assumpties
- Direct beleidsrelevant voor het EU emissions trading systeem
- Past direct op Ketel's causal-inference toolkit

**Implementatie**: ~1-2 weken. Vereist heroriëntatie van een deel van Chapter 4 (data) om carbon-intensity variabele expliciet te maken.

**C.3.4. Marginal Treatment Effects (MTE) / LATE bounds**

Voor het offtake-effect: de IV is in principe niet beschikbaar (geen exogene shift in offtake-commitment), maar MTE-bounds onder partial identification kunnen worden geconstrueerd via:
- Heckman-Vytlacil MTE framework
- Manski (1990) bounds
- Lee (2009) sharp bounds

Dit is conservativer dan ons huidige Oster-resultaat maar methodologisch frontier.

**C.3.5. Doubly-robust DiD (Sant'Anna & Zhao 2020)**

Aanvulling op Callaway-Sant'Anna die nog niet in onze toolkit zit. Gebruikt zowel propensity-score als outcome-regression met dubbele robustheid. Logische extensie.

### C.4 Concrete actie

**MUST voor v2 (toont causale-inferentie diepte)**:
- Synthetic Control implementatie voor UK Track-1 case (Pijler 41b)
- Doubly-robust DiD als robuustheidstest voor offtake-effect (Pijler 41c)
- Sectie 8.X toevoegen "Robustness check: synthetic control"

**SHOULD voor PhD**:
- RDD CBAM (vereist data-uitbreiding)
- MTE bounds voor offtake-effect

**Verwachting Ketel-respons**: zonder synthetic control en double-robust DiD vindt zij dat onze causal-identification niet "complete" is voor moderne standaarden. *Met* die toevoegingen sluit het direct aan op haar expertise.

---

## CATEGORIE D: ECONOMETRISCHE MODELLEN (GENERIEK)

### D.1 Wat we hebben

Onze toolkit dekt:
- DiD (TWFE, Sun-Abraham, BJS-imputation)
- TVP-DiD (drie state-space specificaties)
- Survival (Cox PH in chapter 7-archief)
- Matching (PSM, IPWRA)
- Sensitivity (Oster, Rambachan-Roth)
- Causal forest (Pijler 30, voor heterogeniteit)
- Bootstrap inference

### D.2 Wat we missen — generieke modellen

**Survival-specifiek (versterkt Chapter 7)**:

**D.2.1. Competing Risks Model (Fine-Gray 1999)**

Onze huidige hazard-modellen behandelen "project failure" als één outcome. In werkelijkheid zijn er vier failure-modi:
- Cancelled (definitive)
- On-hold (assumed)
- On-hold (confirmed)
- Decommissioned

Een Fine-Gray cumulative incidence function model zou:
- Verschillende risk-factors per failure-type kunnen identificeren
- Substantief richer interpretation (welke policy voorkomt cancellatie maar niet on-hold?)
- Direct relevant voor stakeholder-vraagstuk

**Implementatie**: ~1 week werk in Python `lifelines` of R `cmprsk`. **Hoge prioriteit voor v2**.

**D.2.2. Multi-State Model**

Projecten doorlopen states: Announced → FEED → FID → Construction → Operational. Een multi-state hazard model met state-specifieke transition rates zou:
- De volledige trajectory karakteriseren, niet alleen failure
- Stage-specific policy effects identificeren
- Aansluiten op IEA-style funnel-analyse

**Implementatie**: ~2-3 weken via `mstate` (R) of `msm` (R). PhD-uitbreiding niveau.

**D.2.3. Frailty Models (random-effects survival)**

Sponsor-level random effects in hazard model zouden:
- Sponsor-heterogeniteit modelleren (in plaats van controleren)
- Variantie-decompositie tussen project, sector, sponsor
- Direct aansluiten op observational design

**Spatial & cluster-aware**:

**D.2.4. Conley Spatial Standard Errors**

Onze huidige standard errors clusteren op project-niveau. Voor spatial correlation (hydrogen clusters: HyNet, East Coast Cluster, Aramis-netwerk) zou Conley HAC-correctie:
- Spatial dependence modelleren
- Inference robuuster maken
- Direct relevant voor Gasunie-stakeholder

**Implementatie**: ~3-5 dagen. Past in v2.

**D.2.5. Spatial Econometrics (SAR / SEM)**

Volledig spatial autoregressive model voor project-failure als functie van naburige-project failures. PhD-uitbreiding.

**Bayesian methods**:

**D.2.6. Bayesian Model Averaging (BMA)**

We hebben vier carrot-policy estimates uit drie estimators elk (12 puntschattingen). BMA zou:
- Het beste model identificeren via posterior probabilities
- Model-uncertainty expliciet kwantificeren
- Robust aggregate estimate leveren

**D.2.7. Hierarchical Bayesian Survival**

Multi-level hierarchical model (project nested in sponsor nested in country) zou de volledige hiërarchische data-structuur respecteren.

### D.3 Concrete actie

**MUST voor v2**:
- Competing Risks (Fine-Gray) — Chapter 7 uitbreiding (Pijler 41d)
- Conley Spatial SE als robuustheid in Chapter 6 (Pijler 41e)

**SHOULD voor PhD**:
- Multi-state model
- Frailty / hierarchical Bayesian
- Bayesian Model Averaging

---

## CATEGORIE E: NIEUWS EN EVENTS

### E.1 Wat we citeren als externe validatie

In hoofdstuk 6-11 verwijzen we naar:
- 2024-25 cancellation-wave: ArcelorMittal, BP, EU Hydrogen Bank withdrawals
- Industry sources: Decarbonize Weekly, ING, Buckle Bridge (placeholder citations)
- Odenweller-Ueckerdt 2025 cancellation-tracking

### E.2 Wat we WAARSCHIJNLIJK missen sinds januari 2026

**Verifieer in v2 met expliciete check**:

**E.2.1. EU Hydrogen Bank 3e auction (verwacht maart-april 2026)**

De 1e auction (april 2024) en 2e auction (eind 2024/begin 2025) hebben respectievelijk 7 winners (waarvan 5 valley en 2 maritime) en 15 winners gefinancierd. Een 3e auction is in de pijpleiding. Belangrijk voor:
- Update van EU Hydrogen Bank participatiestatistieken
- Verfijnde withdrawal-rates
- Mogelijk: design-aanpassingen van auction (offtake-eis?)

**Actie**: Web search "EU Hydrogen Bank third auction 2026" voor v2.

**E.2.2. US 45V regulations en politiek**

De Trump-administratie (sinds januari 2025) heeft de IRA in vraag gesteld. Specifiek voor hydrogen:
- 45V Treasury final regulations (eind 2024) bepaalden temporal-matching en additionaliteits-vereisten
- Politieke onzekerheid over 45V continuïteit
- Mogelijk: gedeeltelijke repeal of versmalling onder Reconciliation Bill

**Actie**: Verifieer huidige status 45V regulations in mei 2026.

**E.2.3. China 15th Five-Year Plan finalisering**

De 14th FYP (2021-2025) is per eind 2025 afgesloten. Het 15th FYP (2026-2030):
- Conceptueel goedgekeurd in oktober 2025 plenum
- Definitieve versie verwacht maart 2026 (NPC)
- ING-rapport ("ing2026") suggereert escalatie van hydrogen-prioriteit

**Actie**: Verifieer specifieke hydrogen-bepalingen 15th FYP.

**E.2.4. Specifieke project-cancellations sinds januari 2026**

Mogelijke ontwikkelingen waar we ons van moeten vergewissen:
- Verdere ArcelorMittal-uittredingen?
- BP/Shell andere project-exits?
- Nederlandse projecten (NortH2, HyNetwork)?
- Status German H2-Backbone projecten?

**Actie**: 30-min web search voor "hydrogen project cancellation 2026" en "green hydrogen FID 2026".

**E.2.5. COP31 (geplanned november 2026)**

Te vroeg voor onze defense, maar relevant voor:
- Update Nationally Determined Contributions
- Hydrogen-targets in NDC's
- International cooperation announcements

**E.2.6. Industrieconsolidatie**

Sinds 2024:
- Air Liquide acquired smaller hydrogen players?
- Linde / Air Products consolidatie?
- China hydrogen industry consolidation?

**Actie**: Industry-tracker via Bloomberg / FT.

### E.3 Concrete actie

**MUST voor v2 (laat zien dat thesis up-to-date is)**:
- Een sectie "Updates since database snapshot" in Chapter 4 (data) of in een specifieke appendix
- 1-pagina update over EU Hydrogen Bank 3e auction (zodra resultaten beschikbaar)
- Verifieer en update industry-citations (decarbonizeweekly, ing, bucklebridge) met geverifieerde URLs en datums

**SHOULD voor PhD**:
- Aankondiging van een 2027-update van de S&P-database voor ex-post evaluatie van counterfactual-scenarios

---

## PRIORITEERINGSMATRIX

Tabel: aanbevolen werkvolgorde voor v2 (de-vol-3 weken-iteratie tussen feedback) en PhD-uitbreidingen.

| # | Item | Categorie | Inspanning | Prioriteit | Doel |
|---|---|---|---|---|---|
| 1 | GAS-model TVP-DiD | B (Koopman) | 5d | **MUST v2** | Comfort-zone Koopman |
| 2 | Synthetic Control UK Track-1 | C (Ketel) | 5d | **MUST v2** | Versterkt selection-funnel narratief |
| 3 | Competing Risks (Fine-Gray) | D (econometrisch) | 5d | **MUST v2** | Verrijkt failure-interpretatie |
| 4 | Doubly-robust DiD offtake | C (Ketel) | 3d | **MUST v2** | Volledige causale toolkit |
| 5 | Diebold-Mariano forecast comp | B (Koopman) | 3d | **MUST v2** | Predictive validation |
| 6 | Literatuur-update 6 papers | A (papers) | 3d | **MUST v2** | Credibility |
| 7 | Industry-news update sectie | E (nieuws) | 2d | **MUST v2** | Up-to-date framing |
| 8 | Conley spatial SE robustness | D | 5d | SHOULD v2 | Cluster-correctie |
| 9 | Multi-state model (5 states) | D | 10d | SHOULD PhD | Trajectory analyse |
| 10 | Dynamic Factor Model 4-policy | B (Koopman) | 10d | SHOULD PhD | DFM in zijn expertise |
| 11 | RDD CBAM threshold | C (Ketel) | 10d | SHOULD PhD | Quasi-exp identificatie |
| 12 | Particle filter binary outcomes | B (Koopman) | 15d | SHOULD PhD | Non-Gaussian state-space |
| 13 | Frailty / hierarchical Bayesian | D | 15d | COULD PhD | Sponsor random effects |
| 14 | Bayesian Model Averaging | D | 10d | COULD PhD | Model uncertainty |
| 15 | Spatial econometrics (SAR/SEM) | D | 15d | COULD PhD | Cluster geography |
| 16 | MTE bounds offtake | C (Ketel) | 10d | COULD PhD | Partial identification |

**Totaal MUST voor v2**: 26 werkdagen ≈ 5 weken
**Totaal SHOULD voor PhD-uitbreiding**: 45 werkdagen ≈ 9 weken
**Totaal COULD nice-to-have**: 50 werkdagen ≈ 10 weken

---

## STRATEGISCHE BESLISSING

Gegeven Sake's:
- Verwachte defense in juli 2026 (~2 maanden ver weg)
- 32u/week werk bij Gasunie BL Waterstof Nederland
- Beperkte beschikbare tijd voor v2-iteratie (~6 weken realistisch)

**Aanbevolen scope voor v2** (vóór verzending naar the reviewers):

1. **GEEN nieuwe analyse meer** voor v1-verzending. De huidige draft is voldoende voor *eerste* feedback ronde.
2. **WEL deze v2-uitbreidingen klaarzetten** vóór feedback-ontvangst, zodat we direct kunnen reageren op specifieke vragen:
   - Items 1-7 uit prioriteitsmatrix klaarliggen als "in voorbereiding voor v2"
   - Scripts geschreven en data-pipelines getest, maar nog niet in manuscript
3. **NA feedback** beslissen welke items prioriteit krijgen op basis van wat Koopman/Ketel specifiek vragen

**Voor defense (juli 2026)**:
- Minimum: items 1-3 in manuscript (GAS, Synthetic Control, Competing Risks)
- Optimum: alle 7 MUST-items + 1-2 SHOULD-items als appendix-uitbreiding

**Voor PhD-uitbreiding (post-defense)**:
- Items 8-12 als basis voor 2-3 journal-submissions:
  - Submission 1: Hoofdstuk 7 uitbreiding met GAS+DFM+particle filter → *Journal of Applied Econometrics* of *Journal of Econometrics*
  - Submission 2: Hoofdstuk 8 uitbreiding met synthetic control + competing risks + multi-state → *Energy Economics*
  - Submission 3: Real-options × mechanism-design (Hoofdstuk 3) → *Energy Policy* of *JEEM*

---

## CONCLUSIE: WAT IS DE STATUS NU EN WAT IS DE VOLGENDE STAP

Het manuscript is in zijn huidige vorm:
- **Empirisch substantieel**: 7 findings, 5 robust, methodologisch divers
- **Theoretisch verankerd**: real-options framework met sectoral predictions
- **Stakeholder-relevant**: counterfactual scenarios, briefings voor 3 stakeholder-groepen
- **Methodologisch verdedigbaar**: triangulatie en honest transparency

Het manuscript heeft *één duidelijke zwakte*:
- **Methodologisch onvolledig voor zijn supervisors**: zonder GAS-model is hoofdstuk 7 niet "Koopman-grade"; zonder synthetic control en double-robust DiD is hoofdstuk 8 niet "Ketel-grade".

**Concrete eerstvolgende actie** (24-48 uur):

1. **Verstuur v1 naar the reviewers** zoals het is. De huidige kwaliteit is *meer* dan voldoende voor eerste feedback. Wacht niet op v2-items want dat creates eindeloze opzettelijke vertraging.

2. **Parallel**: start scripts voor items 1-3 (GAS-model, Synthetic Control, Competing Risks). Deze drie zijn de meest direct relevante uitbreidingen die *waarschijnlijk* in de feedback worden genoemd.

3. **Reageer op feedback** met v2 waar zowel inhoudelijke aanpassingen (n.a.v. feedback) als methodologische uitbreidingen (items 1-3) zijn opgenomen.

Deze strategie maximaliseert:
- Snelheid (geen verdere vertraging voor v1-verzending)
- Aansluiting bij supervisor-feedback (we hebben items klaar die zij waarschijnlijk vragen)
- Kwaliteit (v2 is methodologisch sterker dan v1)

---

*Document opgesteld: 21 mei 2026, 10:50 UTC+2*
*Aanbevolen review-frequentie: na ontvangst supervisor-feedback (v3)*
