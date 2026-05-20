# GAP ANALYSIS v3 — STAKEHOLDER PERSPECTIEF
## Wat ontbreekt om een sterke, beleidsimpactvolle PhD te schrijven?

**Auteur**: Sake Saakstra
**Datum**: 20 mei 2026
**Doel**: identificeren wat een sterke PhD impactvol maakt voor beleidsmakers, sponsors, en infrastructuur-bedrijven (Gasunie)

---

## EXECUTIVE SUMMARY

Na grondige inventaris van wat we **wel** en **niet** in onze data hebben, plus stakeholder-specifieke vragen, zijn er **drie categorieën gaps** die je defense impactvol maken:

### Kritieke gaps voor stakeholder-waarde (MUST-DO)
1. **Offtake-effect analyse** — 172/1354 projecten hebben offtakers, nooit gebruikt voor survival
2. **Counterfactual scenario-simulatie** — "wat als EU 45Q-equivalent had?"
3. **NL deep-dive met Aramis/Porthos** — specifiek voor KGG + Gasunie
4. **Spatial/cluster analyse** — HyNet, East Coast Cluster, Aramis-network

### Belangrijke gaps voor academische impact
5. **CO2-capture cost-effectiveness** — 100% data coverage, beleidsmpact metric
6. **Game-theoretic real options** — strategic firm interaction (Chapter 5-6)
7. **Honest DiD bounds (Roth 2024)** — sensitivity analyse
8. **Synthetic control** — alternative identification

### Nice-to-have gaps
9. Output product typering (ammonia/methanol effects)
10. EPC contractor / electrolyzer supplier effects
11. Demand-side analyse
12. Updated 2024-2026 data (need new S&P snapshot)

---

## DATA-INVENTARIS — WAT HEBBEN WE GEMIST?

### Onderbenutte velden in S&P data (1354 projecten)

| Veld | Coverage | Gebruikt? | Waarde |
|---|---|---|---|
| **Co2 capture (t/y)** | **100%** | ❌ Niet | Climate impact metric (408 Mt/y total!) |
| **Will export** | 100% | ❌ Niet | Export-positioned projecten anders dan binnenlands? |
| **Output product** | 100% | ❌ Niet | Hydrogen-only vs Ammonia vs Methanol |
| **Latitude/Longitude** | 99% | ❌ Niet | Spatial cluster effects mogelijk |
| **Developer** | 99.8% | ❌ Niet | We gebruikten Primary owner (38% coverage!) |
| **State/province** | 55% | ❌ Niet | Sub-national variation (US states, Chinese provincies) |
| **EPC contractor** | 32% | ❌ Niet | Implementation capability proxy |
| **Electrolyzer supplier** | 48% | ❌ Niet | Green tech-supplier effects |
| **Offtake name** | 13% | ❌ Niet | **Crucial: pre-FID commercial commitment** |
| **Offtaker** | 12% | ❌ Niet | Identity van offtaker |
| **Total renewables capacity** | 100% | ❌ Niet | Green-renewables coupling |
| **Investment value** | 1% | ❌ Te leeg | Cost-effectiveness niet mogelijk uit S&P |
| **Funding value** | 0% | ❌ Te leeg | Subsidie-magnitude niet mogelijk uit S&P |

### Wat ontbreekt fundamenteel (data-gaps)
- **Investment/funding values**: bijna geen coverage → geen cost-effectiveness uit S&P
- **Updated post-March 2024 data**: snapshot is 24-3-2024, missing 14 maanden
- **Real costs vs announced**: alleen aankondigingen, geen post-FID kostenrealisatie
- **Carbon prijzen forecast/hedging contracts**: niet beschikbaar
- **Demand-side data**: offtake markets, end-user contracts

---

## PER STAKEHOLDER — WAT WIL HIJ WETEN?

### 🇪🇺 EU DG CLIMA + DG ENER

**Hun beslissings-vragen**:
1. Welk mechanism design werkt het beste voor EU-context?
2. Wat zou het effect zijn van een EU-45Q-equivalent?
3. Hoe schaalvergroot je Innovation Fund voor max impact?
4. Welke sectoren prioriteren?
5. Cost-effectiveness: € per Mt CO2 sequestered?

**Wat we hebben**:
- ✅ US 45Q werkt (-3.8% annual hazard, p<0.01)
- ✅ EU IF direction OK maar NS
- ✅ UK selection-tender werkt als FID-funnel
- ✅ Real-options framework als verklaring

**Wat we MISSEN voor EU-impact**:
- ❌ Counterfactual: "wat als EU 45Q had?" simulatie
- ❌ EU-specifieke sectoral targeting analyse
- ❌ Innovation Fund optimal scale calculation
- ❌ CO2-capture potential per €-invested

**Concreet wat ontbreekt**:

> *"Beste EU beleidsmaker, ons onderzoek toont dat US 45Q empirisch protectief is voor Blue projecten. Maar wat zou dit BETEKENEN voor EU? Hoeveel extra projecten zouden FID bereiken? Hoeveel Mt CO2 zou je vermijden? Welke sectoren krijgen de meeste impact?"*

Deze vragen kunnen we **niet beantwoorden** met onze huidige outputs.

### 🇳🇱 KGG (Klimaat & Groene Groei) + Ministerie EZ

**Hun beslissings-vragen**:
1. Is SDE++ CCS-component effectief? Hoe vergelijken NL projecten?
2. Hoe positioneren we in EU (lead vs follow)?
3. Welke sectoren NL specifiek prioriteren?
4. Wat is het effect van NL Hydrogen Backbone (Gasunie)?
5. NL-specifieke risks: Aramis/Porthos timing?

**Wat we hebben**:
- ✅ NL = 39 projecten (9 Blue, 30 Green) — 31% failure rate
- ✅ NL sponsors: mix van industrial gas (Air Liquide), oil-majors (Equinor, Shell, Uniper)
- ✅ Carrot-taxonomie waar SDE++ in past

**Wat we MISSEN voor NL-impact**:
- ❌ **NL-specifieke deep-dive** (zoals UK qualitative Pijler 27a)
- ❌ Aramis/Porthos case study met cluster-effect
- ❌ SDE++ CCS-component DiD (specifiek voor NL)
- ❌ NL vs Germany vs Norway benchmark
- ❌ Port-of-Rotterdam/Eemshaven cluster analyse

### ⚡ Gasunie BL Waterstof NL + KGG (infrastructuur)

**Hun beslissings-vragen**:
1. Wanneer pipeline-FID nemen voor HyNetwork?
2. Welke productie-bronnen kunnen we vertrouwen voor capaciteit?
3. Cross-border integration (NL-DE-BE-UK)?
4. Hub-effect: waar moet je capaciteit concentreren?
5. Stranded asset risk?

**Wat we hebben**:
- ✅ Failure rates per geography (NL=31%, UK=42%, DE=29%)
- ✅ FID-rate vs announcement-rate concept
- ✅ Mega-project vs non-mega failure differential

**Wat we MISSEN voor Gasunie**:
- ❌ **Spatial cluster analyse** (HyNet, East Coast, Aramis network) — coordinates beschikbaar!
- ❌ Time-to-FID forecasting (Bayesian decision framework)
- ❌ Cross-border pipeline integration analysis
- ❌ Hub-network topology (welke clusters cluster zich rond pipelines?)
- ❌ Sponsor screening framework voor import-zekerheid

### 💼 Sponsors (project ontwikkelaars, oil-majors, industrial gas)

**Hun beslissings-vragen**:
1. Welke factoren voorspellen FID-success?
2. Mega vs phased approach: welke beter?
3. Welke partner-coalities werken?
4. Welke geographic locations zijn optimaal?
5. Hoe risk-adjust IRR?

**Wat we hebben**:
- ✅ Sponsor type × failure rate (oil-major 67%, SOE 0%)
- ✅ Mega vs non-mega differential
- ✅ Cross-jurisdiction policy effects

**Wat we MISSEN voor sponsors**:
- ❌ **Predictive FID-success model** (ML classifier)
- ❌ Phased vs mega decision support
- ❌ Coalition / consortium effect analyse
- ❌ Offtake-effect quantificatie

---

## CONCRETE PIJLERS DIE NOG MOETEN — RANKED BY IMPACT

### Tier 1: MUST-DO voor stakeholder-waarde (10-15 uur totaal)

**Pijler 34: Offtake-effect analyse** (3-4 uur)
- 172 projecten hebben offtakers — dit is een **directe commerciële commitment indicator**
- Hypothese: offtake = lager failure rate (real-options σ-reduction)
- DiD: projecten met vs zonder offtake
- **Waardevol voor**: alle stakeholders (sponsors, Gasunie, beleidsmakers)
- Beleidsmpact: "subsidies werken beter ALS combinatie met offtake-mandates"

**Pijler 35: NL deep-dive + Aramis/Porthos case study** (3-4 uur)
- 39 NL projecten gedetailleerde decompositie
- Aramis (NorthSea CCS), Porthos (Rotterdam CCS), H-vision (Refinery cluster)
- Cross-EU benchmark (NL vs Germany vs Norway)
- SDE++ CCS-component effectiviteit
- **Waardevol voor**: KGG, Gasunie, Ministerie EZ

**Pijler 36: Counterfactual scenario simulatie** (4-6 uur)
- "Wat als EU 45Q-equivalent had?" — gebruik onze CATE estimates
- "Wat als UK Track was vervangen door output-credit?"
- Project-level scenarios met confidence intervals
- **Waardevol voor**: EU DG CLIMA — directe beleidsmpact
- Concrete getallen: ~X extra FIDs, ~Y Mt CO2

### Tier 2: BELANGRIJK voor sterke PhD (10-15 uur)

**Pijler 37: Spatial cluster analyse** (3-4 uur)
- Lat/Long beschikbaar voor 99% projecten
- K-means clustering om hubs te identificeren
- Within-cluster vs between-cluster failure rates
- Network topology: welke projecten cluster zich rond CCS-infrastructuur
- **Waardevol voor**: Gasunie (pipeline routing) + EU (cluster-policy)

**Pijler 38: CO2-capture cost-effectiveness** (3-4 uur)
- 408 Mt/y CO2 capture potential in totaal
- € per Mt CO2 vermeden per policy
- Combineren met onze DiD effects (extra FIDs × CO2 per project)
- **Waardevol voor**: EU climate policy, NL klimaatdoelen
- *Caveat*: gebruiken IEA/Hydrogen Council subsidie cijfers (niet S&P data)

**Pijler 39: Honest DiD bounds (Roth 2024)** (2-3 uur)
- Partial identification onder violating parallel trends
- Sensitivity bounds voor alle 4 main DiD effects
- We hebben deels al code (honest_did_*.csv files)
- **Waardevol voor**: academic rigor + defense

### Tier 3: ACADEMIC EXCELLENCE (15-25 uur)

**Pijler 40: Game-theoretic real options** (8-10 uur)
- Strategic firm interaction (Cournot model voor cluster-tender)
- Oil-major coordination problem
- Theoretical extension van Pijler 29
- **Waardevol voor**: Chapter 5-6 + theoretical contribution

**Pijler 41: Synthetic control alternative** (3-4 uur)
- Cross-country synthetic control voor 45Q, UK Track, China FYP
- Alternative identification strategy
- **Waardevol voor**: methodologische rigor

**Pijler 42: Sponsor ecosystem network** (3-4 uur)
- Use Developer (99.8% coverage!) ipv Primary owner
- EPC contractor effects
- Electrolyzer supplier × Green survival
- Consortium analysis

**Pijler 43: Output product typering** (2-3 uur)
- Ammonia vs Hydrogen vs Methanol survival
- Different downstream markets matter
- 100 projecten produceren Ammonia (export-georiënteerd)

### Tier 4: NICE-TO-HAVE (10-20 uur)

**Pijler 44**: Demand-side analyse (4-6 uur)
**Pijler 45**: Predictive FID-success ML model (4-6 uur)
**Pijler 46**: Power calculations a priori (2-3 uur)
**Pijler 47**: Updated data integration (afhankelijk van data access)

---

## EERLIJKE BEOORDELING — WAT IS NU DEFENSE-READY?

### Sterk genoeg voor defense (huidige 30+ pijlers)
- ✅ 5 publication-grade findings empirisch
- ✅ Three-method TVP convergence
- ✅ Three-method DiD robustness (TWFE + Sun-Abraham + Borusyak)
- ✅ Causal forest HTE (Pijler 30) + LPM crosscheck
- ✅ Real-options theoretical framework

### Zwakke punten zonder Tier 1 pijlers
- ⚠ **EU concrete beleidsadvies** is generiek ("schaal IF op") — geen counterfactual cijfers
- ⚠ **NL concrete beleidsadvies** is missing — geen NL-specifieke deep-dive
- ⚠ **Gasunie concrete strategie** is generiek — geen spatial analyse
- ⚠ **Sponsors concrete framework** is missing — geen predictive model
- ⚠ **Offtake mechanism** niet getoetst (172 projecten data ongebruikt!)

### Wat dit betekent praktisch
**Voor PhD-thesis verdediging**: defendable, focus ligt op empirische causale identificatie

**Voor publication track** (Energy Policy, J. Cleaner Production): 5 findings + carrot-taxonomie is sufficient

**Voor stakeholder-waarde**: hier zit de echte gap. Onze huidige output is **academisch sterk** maar **operationeel zwak**

---

## AANBEVOLEN ROUTE — DRIE PRIORITEITS-PADEN

### Pad A: Academic Defense Focus (8-10 uur, 1 sessie)
- Pijler 39 (Honest DiD bounds)
- Naadloos verhaal schrijven
- Chapter outlines
- **Outcome**: defense-ready met huidige material

### Pad B: Stakeholder-impact Pad (15-20 uur, 3-4 sessies)
- Pijler 34 (Offtake-effect) → directe sponsor + Gasunie waarde
- Pijler 35 (NL deep-dive) → KGG + Gasunie waarde
- Pijler 36 (Counterfactual scenarios) → EU waarde
- **Outcome**: PhD + concrete beleidsadvies voor 3 stakeholders

### Pad C: Academic Excellence Pad (25-35 uur, 5-6 sessies)
- Pad B + Pijler 37 (spatial) + Pijler 40 (game theory) + Pijler 41 (synthetic control)
- **Outcome**: top-tier publication-ready research

---

## MIJN PERSOONLIJKE AANBEVELING

**Voor Sake's situatie** (32u/week Gasunie + PhD-thesis + carrière):

Doe **Pad B (stakeholder-impact)** maar in **slimme volgorde**:
1. **Pijler 34 (Offtake)** eerst — quick win + alle 3 stakeholders waardevol
2. **Pijler 35 (NL deep-dive)** tweede — direct Gasunie/KGG waarde + carrière-impact
3. **Pijler 36 (Counterfactual)** derde — EU beleidsmpact
4. **Daarna**: naadloos verhaal schrijven met deze drie nieuwe pijlers

**Reden**:
- Pijler 34 (Offtake) is een ENTIRELY NEW mechanism dat de literatuur niet heeft
- Pijler 35 (NL) maakt je werk DIRECT relevant voor je werkgever
- Pijler 36 (Counterfactual) is wat EU beleidsmakers willen ZIEN
- Samen leveren ze concrete getallen die het verhaal van "abstract" naar "actionable" maken

**Tijdsbudget**: ~10-14 uur verdeeld over 3 sessies = ~5-6 weken bij avond-werk

**Wat er NIET moet**: alle 14 extra pijlers. Dat verdunt focus en levert geen extra impact.
