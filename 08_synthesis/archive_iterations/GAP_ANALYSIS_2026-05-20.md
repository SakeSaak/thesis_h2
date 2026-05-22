# GAP ANALYSIS — Wat we nog NIET hebben onderzocht
## Identificatie van witte vlekken in 26-pijler robustness battery

**Auteur**: Sake Saakstra (MSc EOR, VU Amsterdam)
**Datum**: 20 mei 2026
**Doel**: systematische identificatie van gaten die met aanvullende data/events/papers/PhD-research kunnen worden gevuld

---

## 0. Samenvatting

Onze 26 pijlers behandelen vier hoofdthemata robuust (Blue fragility, CBAM null, 45V/45Q dual mechanism, carbon-conditional regime shift). Maar er zijn **vijf categorieën gaten** die de impact en publishability kunnen vergroten:

| Categorie | Omvang | Prioriteit |
|---|---|---|
| **A. Methodologische verfijning** | 5 gaten | Hoog (publication-grade requirement) |
| **B. Empirische uitbreiding** | 6 gaten | Hoog (additional findings) |
| **C. Post-snapshot policy events** | 7 events | Medium (recente actualisatie) |
| **D. Theoretische framework integratie** | 4 papers | Medium (PhD-defense) |
| **E. Stakeholder-specifieke data** | 3 data sources | Medium (briefings versterking) |

---

## A. METHODOLOGISCHE GATEN

### A1. PyMC convergence issues in Pijler 24 (TVP-state-space)

**Probleem**: 1000 divergences in Bayesian random-walk sampling.

**Wat nodig is**:
- Non-centered parameterization voor β_int(t)
- Increase tune steps: 1500 → 3000
- 4 chains in plaats van 2
- target_accept: 0.92 → 0.95
- Alternative: Kalman filter via `statsmodels.tsa.statespace`

**Geschatte tijd**: 2-3 uur
**Status**: openstaand — Pijler 24a herziening nodig
**Impact**: PhD Chapter 7 publication-grade requirement

### A2. Sample-dependent magnitude — wat is de "echte" HR?

**Probleem**: HR_Blue varieert van 1.88 (S&P Model 5) tot 11.93 (v7 paper). Welke is "waar"?

**Wat nodig is**:
- **Simulatie studie**: simulate hazards onder bekende DGP, test hoe HR-estimaten variëren met sample compositie
- **Meta-analyse**: combineer v7 + S&P + (later) IEA via random-effects model
- **Decompositie**: welke fractie van magnitude-gap is sample selection vs covariate adjustment vs estimator?

**Geschatte tijd**: 4-6 uur
**Status**: openstaand — Pijler 27 kandidaat
**Impact**: Methodologische defense van sample-dependence findings

### A3. Cancellation timing proxy (meetfout in event_year)

**Probleem**: huidig event_year = midpoint(announce, estimated_online). Random meetafwijking ±1-2 jaar.

**Wat nodig is**:
- Cross-validatie met IEA Hydrogen Projects Database (exact event dates indien beschikbaar)
- Sensitivity analyse: hoe veranderen Cox HRs als we event_year ±1 jaar perturbieren?
- Alternative duration models met intervals (lifelines.fitters.CoxTimeVaryingFitter)

**Geschatte tijd**: 3-4 uur
**Status**: openstaand
**Impact**: Methodologische robuustheid bevestiging

### A4. Decommissioning selection effect

**Probleem**: HR_Blue,decomm = 0.235 (Pijler 16) is mogelijk pure selection artifact (alleen operational projecten kunnen decomm raken; Green wordt vaker operational dan Blue).

**Wat nodig is**:
- Conditional analyse: gegeven survival tot operational, wat is HR_decomm?
- Joint model voor (commission → decomm) als sequentiële hazard
- Frailty model met sponsor-level random effects

**Geschatte tijd**: 3-5 uur
**Status**: openstaand — interessant voor real-options chapter

### A5. Cross-country effective carbon-price specificatie

**Probleem**: Pijler 23 toont OMGEKEERDE direction (β = +0.289) wanneer we cross-country effective_carbon_price gebruiken. Mogelijk komt dit door:
- 45Q is een CREDIT, niet een PRIJS op emissie (mismatch)
- Selection: landen met hoge carbon-price hebben ook andere project-killing factoren
- Heterogene response: EU/US/China werken via verschillende mechanismen

**Wat nodig is**:
- Separate model voor "carbon-price" (EUA, ETS) vs "carbon-credit" (45Q)
- Country fixed-effects model
- Mediator analyse: is regulatoire stringency een confounder?

**Geschatte tijd**: 3-4 uur
**Status**: openstaand — kritiek voor narrative integriteit

---

## B. EMPIRISCHE UITBREIDINGEN

### B1. China-specifieke analyse (n=209 projecten beschikbaar)

**Niet uitgevoerd**: deep-dive op China's 14th Five-Year Hydrogen Plan (2022) effect

**Beschikbare data**:
- China Blue: 32 projecten
- China Green: 177 projecten
- 14 failure events (6.7% failure rate — laagst van alle major economies)

**Onderzoeksvragen**:
- Heeft 14th Five-Year Plan (maart 2022) project commitment versterkt?
- Provinciale variantie: Shandong vs Hebei vs Inner Mongolia
- State-led vs private-led project survival

**Geschatte tijd**: 4-6 uur
**Status**: openstaand — kandidaat Pijler 28
**Impact**: Asia-Pacific narrative voor cross-country verhaal

### B2. UK Track-1/Track-2 CCUS effect

**Niet uitgevoerd**: UK is een major hydrogen markt met hoge failure rate (42% van 83 projecten)

**Beschikbare data**:
- UK Blue+Green: 83 projecten
- 35 failures (cancel + on-hold + decomm)
- Track-1 CCUS clusters announcement: dec 2022 (HyNet + East Coast)
- Track-2 CCUS clusters: jul 2023 (Acorn + Viking)

**Onderzoeksvragen**:
- Is Track-1 selection-effect (gunning verlaagt failure) of macro-discouragement (niet-laureaten geven op)?
- Hydrogen Allocation Round 1 (HAR1) results
- Brexit-effect: pre-Brexit UK had EUA, post-Brexit eigen UK ETS

**Geschatte tijd**: 3-4 uur
**Status**: openstaand — kandidaat Pijler 29

### B3. Australia Hydrogen Headstart effect

**Niet uitgevoerd**: AU heeft hoge failure rate (38.4% van 73 projecten)

**Beschikbare data**:
- AU Blue+Green: 73 projecten
- Hydrogen Headstart program (AU$2B), aankondiging 2024
- Hydrogen Production Tax Incentive (2025)

**Onderzoeksvragen**:
- Welke pre-Headstart announcement-jaargangen worden geraakt?
- Vergelijking met UK Track-1 mechanism
- Sample voldoende voor DiD?

**Geschatte tijd**: 3 uur
**Status**: openstaand — kandidaat Pijler 30

### B4. Japan GX-ETS pilot effect

**Niet uitgevoerd**: Japan heeft 36 projecten, GX-ETS pilot sinds april 2023

**Onderzoeksvragen**:
- Heeft GX-ETS voluntary pilot effect op project commitment?
- CfD scheme effect (2024+)

**Geschatte tijd**: 2-3 uur
**Status**: openstaand — laagre prioriteit door kleine sample

### B5. End-use sector heterogeniteit voor US Green

**Niet uitgevoerd**: van 79 US Green projecten weten we 70/79 hebben end-use sector info

**Beschikbare data**:
- Transport road: 26 projecten
- Power & heat: 17 projecten
- Industry: 7+4 projecten
- Refineries, ammonia, etc.

**Onderzoeksvragen**:
- Welke sectoren worden het hardst geraakt door 45V three-pillars?
- Heeft sector eligibility variation in 45V regelgeving (e.g. ammonia)?

**Geschatte tijd**: 2-3 uur
**Status**: openstaand — kandidaat Pijler 31

### B6. State-level heterogeniteit voor US

**Niet uitgevoerd**: 72/79 US Green projecten hebben state info

**Beschikbare data**:
- California: 16 projecten (clean energy mandate state)
- Texas: 15 projecten (oil-major dominant state)
- Andere: 41 projecten

**Onderzoeksvragen**:
- Heeft California state-level additional credits Blue/Green effect?
- Texas oil-major dominance vs Louisiana CCS readiness
- DOE Clean Hydrogen Hubs locaties (7 hubs $7B funding)

**Geschatte tijd**: 3-4 uur
**Status**: openstaand — kandidaat Pijler 32

---

## C. POST-SNAPSHOT POLICY EVENTS (24 maart 2024 — nu)

Onze S&P data is een snapshot per 26 maart 2024. Tussen toen en nu (mei 2026) zijn meerdere materieel relevante events plaatsgevonden die NIET in onze data zijn.

### C1. EU Hydrogen Bank 2nd auction results (Apr 2025)
- 2e auction closed dec 2024 voor electrolytic hydrogen, results announced apr 2025
- ~1.5 GW capacity awarded, totaal EUR 992M support
- **Impact**: nieuwe treated group voor IF-analyse
- **Te zoeken**: DG CLIMA persbericht + officiële winners-lijst

### C2. EU Innovation Fund 5th call (verwacht Q4 2025)
- 5th call opent verwacht december 2025
- Hydrogen-specific window mogelijk
- **Impact**: 14 → 20-30 funded EU projecten
- **Te zoeken**: EU Commission documenten

### C3. Trump 45V revision status (jan-mei 2025)
- Trump administration onder review 45V three-pillars
- Mogelijk relaxation: incrementality reduction, grandfathering provisions
- **Impact**: 45V effect identification kan radically wijzigen
- **Te zoeken**: Treasury Department persberichten

### C4. EU Affordable Energy Action Plan (feb 2025)
- Major EU package incl. hydrogen acceleration measures
- **Impact**: nieuwe carrot mechanismen mogelijk
- **Te zoeken**: Clean Industrial Deal documenten

### C5. ETS Phase 5 consultation (2026-2027 verwacht)
- EU ETS Phase 5 reform discussions starten
- EUA prijs-floor discussions
- **Impact**: future-state regulatory environment
- **Te zoeken**: DG CLIMA consultation papers

### C6. UK Hydrogen Allocation Round 2 (HAR2) results (Q4 2025)
- HAR1 funded 11 projects (~125 MW), HAR2 verwacht groter
- **Impact**: UK treated group voor B2 analyse

### C7. China provinciale H2 subsidies update (2024-2025)
- Shandong, Hebei, Inner Mongolia subsidies verder
- **Impact**: China-analyse voor B1

---

## D. THEORETISCHE FRAMEWORK INTEGRATIE

### D1. Real Options theory voor decommissioning asymmetry

**Status**: niet expliciet gemodelleerd ondanks Pijler 16 finding HR_decomm=0.23

**Referenties om te lezen**:
- Pindyck (1991), "Irreversibility, Uncertainty, and Investment", JEL
- Dixit & Pindyck (1994), "Investment Under Uncertainty" (boek)
- Roberts & Weitzman (1981), "Funding Criteria for Research, Development, and Exploration Projects", Econometrica

**Concreet werk**:
- Schrijf section 2.3 van thesis: "Asymmetric Irreversibility in Technology Choice"
- Formaliseer Blue als sequential-exercise option: cancel pre-FID (cheap exit) → commit FID (irreversible commit) → operational (locked-in)
- Vergelijk met Green: gradual abandonment optie post-commission (HR_decomm hoger)

**Geschatte tijd**: 4-6 uur literatuur + 8 uur formele model

### D2. Carbon-conditional asset pricing literature

**Status**: methodologisch nuttig voor Chapter 7 maar niet expliciet geïntegreerd

**Referenties**:
- Bolton & Kacperczyk (2021), "Do investors care about carbon risk?", JFE
- Mercure et al (2018), "Macroeconomic impact of stranded fossil fuel assets", Nature Climate Change
- Edenhofer et al (2020), "Climate policies after Paris", Nature Climate Change

**Concreet werk**:
- Verbind onze TVP β_int(t) finding aan asset-pricing literatuur
- Frame Blue hydrogen als "stranded asset risk" met carbon-price hedge

**Geschatte tijd**: 3-4 uur

### D3. Implementation science / policy compliance literature

**Status**: onze "carrots vs sticks" framing is intuïtief maar niet formal-theorisch

**Referenties**:
- Tinbergen rule (1952): N instrumenten voor N doelen
- Lindblom & Smith literature op policy design
- Engel-Hewitt-Kaiser (2010+) op behavioral compliance

**Concreet werk**:
- Section 2.4: "Mechanism design for low-carbon technology adoption"
- Vergelijk 45V/45Q als "carrots + sticks" combination

**Geschatte tijd**: 3-4 uur

### D4. Sample-dependent magnitude in survival analysis

**Status**: empirisch belangrijk maar methodologisch literatuur niet geïntegreerd

**Referenties**:
- Cox & Oakes (1984), "Analysis of Survival Data"
- Therneau-Grambsch (2000), "Modeling Survival Data: Extending the Cox Model"
- Wynant & Abrahamowicz (2017), "Comparison of estimation methods for hazard ratio in low-event-rate settings"

**Concreet werk**:
- Methods chapter sub-section over sample-dependent hazard inference
- Best practices document voor implementation-effect studies

**Geschatte tijd**: 3-4 uur

---

## E. STAKEHOLDER-SPECIFIEKE DATA UITBREIDING

### E1. IEA Hydrogen Projects Database (cross-validation)
- IEA heeft eigen database, deels overlappend met S&P
- **Doel**: cross-validate S&P findings, identify discrepancies
- **Toegang**: IEA Hydrogen Projects Database (publiek bestand 2024)

### E2. DOE Clean Hydrogen Hubs documents
- 7 hubs aangekondigd onder IRA, $7B funding totaal
- **Doel**: specifieke US Hub-projecten identificeren in S&P
- **Toegang**: DOE Hydrogen Hubs portal

### E3. EU Innovation Fund explicit project lists
- Per-call funded projects officieel gepubliceerd
- **Doel**: validate dat S&P's 14 IF-projecten matchen met DG CLIMA lijst
- **Toegang**: DG CLIMA Innovation Fund webpages

---

## F. EXTERNAL RESEARCH OM TE BESTUDEREN

### F1. Recente PhD theses (2023-2025) op hydrogen project economics

Te zoeken via ProQuest / Google Scholar:
- "hydrogen project cancellation" OR "hydrogen project survival"
- "blue hydrogen risk" OR "green hydrogen failure"
- "45V tax credit empirical"
- "CBAM impact assessment empirical"
- Recent PhDs from MIT, Stanford, ETH Zurich, Imperial College, TU Delft

### F2. Working papers (NBER, SSRN, REPEC) 2024-2026

Specifiek zoeken naar:
- NBER working papers op IRA effects (2023-2025)
- SSRN papers op CBAM impact assessment
- REPEC papers op hydrogen project finance

### F3. Industry reports (commercial)

- BloombergNEF "H2 Economy Outlook 2026"
- IEA "Global Hydrogen Review 2025" (te verschijnen)
- Wood Mackenzie hydrogen reports
- S&P Commodity Insights special reports
- Hydrogen Council "Hydrogen Insights 2025/2026"

### F4. Conferences (presentations + slides)

- World Hydrogen Summit (Rotterdam, mei 2026 — laatst)
- Hydrogen Americas (Washington DC, oktober 2025)
- European Hydrogen Week (Brussels, november 2025)
- IEA Bioenergy task force meetings

---

## G. PRIORITEITS-MATRIX VOOR VOLGENDE FASE

| Prioriteit | Onderwerp | Tijdsbudget | PhD-impact |
|---|---|---|---|
| **Prio 1** | A1: PyMC convergence Pijler 24 herstel | 2-3u | Chapter 7 publication-grade |
| **Prio 1** | C3: Trump 45V revision tracking | 1-2u/maand | Policy paper actualiteit |
| **Prio 1** | C1, C6: HB 2nd auction + HAR2 data | 3-4u | Innovation Fund schaal-finding |
| **Prio 2** | B2: UK Track-1/2 effect analyse | 3-4u | 3e publishable finding kandidaat |
| **Prio 2** | A2: Meta-analyse sample-dependent HR | 4-6u | Methodologische defense |
| **Prio 2** | D1: Real-options framework | 12-14u | Chapter 5-6 theoretical grounding |
| **Prio 3** | B1: China 14th FYP effect | 4-6u | Asia-Pacific narrative |
| **Prio 3** | B5, B6: US sector + state heterogeniteit | 5-7u | Mechanism analyse 45V |
| **Prio 3** | D2: Carbon-conditional asset pricing | 3-4u | Chapter 7 framing |
| **Prio 4** | B3, B4: Australia + Japan | 5u | Completeness, lager nut |
| **Prio 4** | A5: Cross-country specification | 3-4u | Pijler 23 narrative integrity |

---

## H. GETALLEN OM TE TRACKEN — actualisatie checklist

| Variabele | Laatste bekend | Te updaten via |
|---|---|---|
| EU Innovation Fund cumulative awarded | €4B (eind 2024) | DG CLIMA persbericht 4th call results |
| Hydrogen Bank cumulative awarded | €720M (2024) + €992M (2025) | DG CLIMA persbericht 2nd auction |
| US 45V Final Rule status | Issued jan 2025 | Treasury Dept review process |
| Trump 45V revision proposal | Under review (mid-2025) | Federal Register, Treasury news |
| EUA spot price | €74 (2025 avg) | ICE/EEX daily |
| EU ETS Phase 5 reform | Consultation 2026-2027 | DG CLIMA roadmap |
| UK ETS price | €58 (2024 avg) | UK ETS auction reports |
| China ETS price | $11/tCO2 (2024) | CNETS data |
| New S&P data snapshot | 24 maart 2024 (huidig) | S&P refresh 2027 of nieuwere |
| IEA Hydrogen Review | 2024 versie | 2025 versie verwacht okt-nov 2025 |

---

## I. MIJN AANBEVELING VOOR DE PHD-TIMELINE

### Maand 1 (juni 2026): consolidatie + acute updates
- Implementeer A1 (PyMC convergence fix Pijler 24a)
- Update C1 + C6 met HB 2nd auction + HAR2 data
- Schrijf Chapter 7 outline based on Pijler 24/24a

### Maand 2-3 (juli-aug 2026): empirische uitbreiding
- B2: UK Track-1/2 analyse (Pijler 27)
- D1: Real-options framework integratie
- Concept policy paper voor *Energy Policy* (45Q finding)

### Maand 4-6 (sep-nov 2026): thesis-schrijven
- Chapters 1-4 schrijven (introductie + theorie + data + baseline)
- Chapter 5-6 herzien met dual-pathway en regime-conditional findings
- Concept Chapter 7 TVP-state-space

### Maand 7-9 (dec 2026-feb 2027): finalize + submit
- Chapter 8 multi-policy comparative
- Chapter 9-10 Dutch context + conclusions
- External feedback rondes
- Submit policy paper

### Maand 10-12 (mar-mei 2027): defense
- Defense preparation
- Final revisions
- Submit policy paper revisions

---

*Einde GAP_ANALYSIS — voor concrete onderzoeksbevindingen: zie FINAL_SYNTHESIS_v3.md*
*Voor stakeholder-vertalingen: zie POLICY_BRIEFINGS.md*
