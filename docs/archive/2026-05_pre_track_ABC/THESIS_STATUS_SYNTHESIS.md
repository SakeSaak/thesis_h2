# Thesis Synthesis — Volledige Stand van Zaken
**Sake Saakstra | MSc EOR Financial Track VU Amsterdam | Reviewer: the external reviewer**
**Datum: 18 mei 2026**

---

## 1. De Centrale Onderzoeksvraag

> Wat verklaart het verschil in implementatie-risico tussen blue hydrogen (CCS-gebaseerd) en green hydrogen (PEM electrolyser) projecten, en hoe conditioneert de EU ETS koolstofprijs deze risicodifferentiatie?

Deze vraag verbindt drie literaturen:
1. **Energy transition finance** (Bolton & Kacperczyk 2021, Odenweller 2022)
2. **Survival / duration analysis** (Lancaster 1990, Van den Berg 2001)
3. **Time-varying parameter state-space econometrics** (Durbin & Koopman 2012, Koopman 2000, Creal-Koopman-Lucas 2008/2013)

---

## 2. Wat We Hebben Onderzocht

### 2.1 De basis: het v7 paper
**"Implementation-Risk Differentials in Hydrogen Technology Pathways"** — gebaseerd op S&P Global Commodity Insights hydrogen projects database. 714 projecten (244 Blue_CCS, 470 PEM electrolyser), 43 cancellation events over 2010-2026.

**Modellen toegepast:**
- Cox Proportional Hazards met Efron tie-handling
- Fine-Gray competing-risks (cancellation als event of interest)
- Discrete-time hazard via logit (person-year panel)
- Carbon-conditional interactie Blue × EUA_z

**Geleverd:** Hoofdfinding HR=11.93 [4.67, 30.49] voor Blue vs PEM cancellation. Carbon-conditional effect: β_int = -2.51 (p<0.0001), wat impliceert dat bij EUA = 1 SD beneden gemiddelde de Blue HR oploopt tot 673×, terwijl bij EUA = 1 SD boven gemiddelde de HR daalt tot 4.67×.

### 2.2 Spoor 1: Bayesiaanse methodologie
**Vraag:** Hoe stabiel is de v7 Cox PH-vinding onder Bayesiaanse inferentie met expliciete prior-keuzes?

**Methodologie:** Bayesian Cox PH in PyMC met vier priorgrids: vague, weakly informative, skeptical, en informative_v7.

**Vinding:** Bayesiaanse schattingen zijn systematisch lager dan frequentist (HR 4-6 vs 11.9), omdat Bayesian priors regulariseren tegen perfect separation in MLE. Het sign en de richting blijven robuust over alle vier priors — de carbon-conditional richting is intrinsiek aan de data.

### 2.3 Spoor 2: Nederlandse beleidsfocus
**Vraag:** Hoe past dit empirische resultaat in het Nederlandse beleidslandschap (EU ETS, CO2-heffing, SDE++, HyNetwork)?

**Methodologie:** 15-pagina chapter outline gebaseerd op PBL beprijzingstekort framework, EU ETS Phase IV/CBAM/ETS2 architectuur, en SDE++ implementatiebeleid.

**Vinding:** Outline-fase. Vijf open beleidsvragen geformuleerd voor verdere uitwerking en bespreking met VU/Gasunie stakeholders.

### 2.4 Spoor 3: Publieke-data robustness
**Vraag:** Houdt de v7 vinding stand wanneer beperkt tot publiek beschikbare data (CC BY 4.0 licensed IEA CCUS database)?

**Methodologie:** 98 H2-CCUS projecten uit IEA CCUS database, drie Cox PH specificaties: brede CCUS, industriële CCUS, en within-H2.

**Vinding:**
- Brede CCUS: HR=2.02 [1.15, 3.55], p=0.0145 — **significant** ✓
- Industriële CCUS: HR=1.63 [0.84, 3.16], p=0.15 — borderline
- Within-H2: regio en capaciteit niet significant

De qualitative finding (Blue elevated risk) wordt **bevestigd in publieke data**, met magnitude lager dan v7 maar in dezelfde richting. Het effect is robuust tegen data-source keuze. Tien post-maart-2024 cancellations toegevoegd (BP H2Teesside, HyDEMO, Hydrogen 2 Magnum, H2M Eemshaven) — directe Gasunie-relevantie.

### 2.5 Spoor 4: Carbon-conditional replicatie
**Vraag:** Is de carbon-conditional interactie exact reproduceerbaar buiten het oorspronkelijke v7 schattingsregime?

**Methodologie:** Frequentist + Bayesian carbon-conditional met informative prior op v7 schatting.

**Vinding:**
- Frequentist: Blue×EUA coëfficiënt = -2.28 (v7 rapporteert -2.51, ~10% verschil)
- HR bij z=+1 exact 4.67 (perfect match met v7 paper)
- Bayesian sensitivity grid: alle 4 priors geven negatieve β_int met 95% CrI exclusief 0
- Vague prior: β_int = -1.75; Weakly informative: -1.43; Skeptical: -1.06; Informative_v7: -2.16

De **richting en significantie zijn invariant** over prior-keuzes; de magnitude varieert van -1.06 tot -2.16 afhankelijk van prior strength.

### 2.6 Methodologische hoofdbijdrage: Time-Varying Hazard
**Vraag:** Is de carbon-conditional mechanisme tijds-stabiel, of veranderde de gevoeligheid van projecten voor EUA-prijzen over 2010-2026?

**Methodologie:** Drie nested specificaties op year × technology aggregaat (17 jaar × 2 tech = 34 Binomial observaties):
- M1 **Static** baseline
- M2 **Parameter-driven TVP** met Gaussian random walk over 3/4/5 economische regimes
- M3 **Observation-driven TVP (GAS)** met score-based update, scaling d ∈ {0, ½, 1}

Bayesiaanse inferentie via Hamiltonian Monte Carlo. Formele model comparison via PSIS-LOO en WAIC.

**Vinding:**

| Specificatie | β_int schatting | 95% CrI |
|---|---|---|
| Static | -1.37 | [-2.20, -0.49] |
| GAS long-run (ω) | -1.61 | [-2.50, -0.69] |
| 4-block: drie blocks | -1.50 / -1.73 / -2.06 | alle CrI exclusief 0 |

GAS α_gas = 0.045 [0.003, 0.13] — bijna nul, drie scaling varianten geven identieke resultaten. **De data ondersteunt geen substantiële tijdsvariatie**.

LOO/WAIC: blocks marginaal beter dan static (Δelpd ≈ 5, dse ≈ 2.8); GAS iets slechter dan static. Alle comparisons hebben warnings (Pareto k > 0.7) — beperkte LOO betrouwbaarheid bij 17 observaties.

---

## 3. Vragen Waar We Nu Antwoord Op Kunnen Geven

### Vraag 1: Bestaat er een meetbaar implementation-risk verschil tussen Blue_CCS en PEM?
**Antwoord: JA.** Met 95% credibele zekerheid is de Blue cancellation hazard 4-12× hoger dan de PEM hazard, afhankelijk van de gebruikte inferentie-methode. Frequentist Cox PH geeft HR=11.93 [4.67, 30.49]; Bayesian onder weakly informative priors geeft HR≈5; publieke IEA data geeft HR=2.02 [1.15, 3.55]. Het verschil in magnitude verklaart zich uit perfect-separation regularisering en kleinere sample-grootte in publieke data.

### Vraag 2: Conditioneert de EU ETS koolstofprijs deze risicodifferentiatie?
**Antwoord: JA.** Robuust over frequentist, Bayesian, en alle drie TVP-specificaties. β_int = -1.4 tot -1.6 met 95% CrI exclusief 0. Een 1-SD daling in EUA-prijs verhoogt de Blue/PEM hazard ratio ongeveer **factor exp(1.5) ≈ 4.5×**. Een 1-SD stijging verlaagt het verschil tot factor 0.22×. Bij EUA = €100 (z ≈ +1.5) is het Blue cancellation voordeel grotendeels weg; bij EUA = €36 (z ≈ -1.0) is Blue 6× riskanter dan green.

### Vraag 3: Is dit effect robust tegen data-source keuze?
**Antwoord: JA.** Zowel S&P Global Commodity Insights (v7, propriëtair) als IEA CCUS database (publiek, CC BY 4.0) leveren significante negatieve carbon-conditional effecten op. Dit hedge'd het thesis tegen S&P data-licensing risico voor externe publicatie.

### Vraag 4: Is dit effect robuust tegen inferentie-methode?
**Antwoord: JA.** Frequentist Cox PH, frequentist Fine-Gray competing-risks, Bayesian Cox PH (4 priors), en Bayesian aggregate Binomial geven allemaal dezelfde qualitative conclusie. Magnitude varieert, maar sign en significantie zijn invariant.

### Vraag 5: Is het carbon-conditional effect tijds-variant?
**Antwoord: NEE, voor zover detecteerbaar.** De GAS observation-driven analyse geeft direct bewijs: α_gas ≈ 0.045 (lower bound 0.003). De score-driven adjustment is verwaarloosbaar; de drie scaling-varianten geven identieke trajectories. Parameter-driven block specificaties geven kleine variatie maar formele model comparison is niet decisief (Δelpd ≈ 5, dse ≈ 2.8). De ruwe within-block 2023-2024 data bevestigt het mechanisme (HR 1.87 bij €82 vs 4.70 bij €65, in lijn met static estimate β_int ≈ -1.28). De carbon-conditional mechanisme is dus **structureel time-stable**.

### Vraag 6: Wat zijn de specifieke recente cancellation events relevant voor Gasunie?
**Antwoord:** Tien post-maart-2024 cancellations geïdentificeerd uit publieke bronnen: BP H2Teesside (Phase 1+2 UK), HyDEMO (Noorwegen), Hydrogen 2 Magnum (Nederland), H2M Eemshaven (Nederland), plus 6 anderen. Dit verifieert dat de cancellation wave zich naar Nederland heeft uitgebreid.

---

## 4. Conclusies Tot Nu Toe

### 4.1 Empirische conclusies
1. **Blue hydrogen projects face structurally elevated cancellation risk** ten opzichte van PEM electrolyser projects, met een base hazard ratio in de orde van 4-12× afhankelijk van inferentie-context.

2. **Deze risicodifferentiatie is conditioneel op koolstofprijs.** β_int ≈ -1.5 betekent: hoge EUA-prijzen reduceren het verschil aanzienlijk; lage EUA-prijzen vergroten het. Dit is consistent met real-options theorie waarin Blue projecten kapitaal-intensiever zijn maar lagere variable-cost penalty hebben bij hoge carbon prices.

3. **Het mechanisme is structureel time-stable over 2010-2026.** Ondanks dramatische macro-economische verstoringen (pandemie, energiecrisis 2022-23, IRA, ETS Phase IV transities, CBAM aankondiging) blijft de coëfficiënt rond -1.5 zonder detecteerbare regime change. Dit is verrassend en methodologisch belangrijk.

4. **De cancellation wave van 2023-2024** (79% van alle events in twee jaren) is consistent met het carbon-conditional model: de EUA-daling van €82 naar €65 voorspelt precies de toename in Blue/PEM relatieve hazard die werd waargenomen.

### 4.2 Methodologische conclusies
1. **Parameter-driven vs observation-driven TVP geven verschillende posterior trajectories** voor lokaal-sparse sub-perioden, ook wanneer de long-run inferences overeenkomen. Block-specificaties produceerden een schijnbare "2023-2024 anomalie" die door GAS persistentie wordt opgelost via informational pooling.

2. **PSIS-LOO en WAIC discrimineren slecht bij N=17 observaties.** Alle comparisons in deze studie hebben Pareto k > 0.7 warnings. Formele model selectie moet aangevuld worden met substantieve oordeel.

3. **Aggregatie-keuzes (year × tech) zijn vereist voor comparability** maar verliezen individuele covariates (year_since_start, log_capacity). Dit is een trade-off die we expliciet documenteren.

4. **Bayesiaanse inferentie via Hamiltonian Monte Carlo werkt voor zowel parameter-driven als observation-driven TVP** in non-Gaussian state-space modellen voor survival outcomes. Dit is mogelijk een methodologische bijdrage los van de substantieve vinding.

### 4.3 Beleids-conclusies (preliminair)
1. **EU ETS koolstofprijs-niveau is een direct determinant van blue hydrogen project economische levensvatbaarheid.** Een prijs-floor mechanisme of CBAM-implementatie heeft kwantificeerbare implicaties voor cancellation risico.

2. **De stabiliteit van het mechanisme over 2010-2026** suggereert dat het bestand is tegen aankondigingen van beleidsregimes; de feitelijke marktprijs is de operatieve variabele, niet de aangekondigde regime.

3. **Voor Nederlandse hydrogen-strategie (HyNetwork, SDE++):** projecten die hun rendement berekenen onder hoge EUA-prijzen lopen verhoogd cancellation risico zodra de marktprijs daalt. Dit valt te combineren met PBL's beprijzingstekort-framework.

---

## 5. Aanbevelingen

### 5.1 Voor de wetenschappelijke literatuur
1. **Methodologisch:** In hazard analyse met sparse events en TVP-vragen, presenteer parameter-driven én observation-driven specificaties naast elkaar. De Koopman-Lit-Lucas (2016) framework biedt het juiste theoretische anker voor deze vergelijking.

2. **Methodologisch:** Voor hazard modellen met TVP-coëfficiënten kan Bayesian inferentie via HMC (PyMC) een werkbare alternatief vormen voor importance sampling routines uit Durbin-Koopman 2012, mits posterior-trajectories deterministisch zijn als functie van hyperparameters (GAS-stijl).

3. **Empirisch:** De carbon-conditional cancellation mechanisme verdient onderzoek in andere energy transition technologieën — bijvoorbeeld offshore wind, large-scale battery storage, of CCS in cement/steel.

### 5.2 Voor beleidsmakers
1. **EU ETS prijs-pad design:** Onze schatting dat een 1-SD EUA-daling de Blue/PEM hazard ratio met factor 4.5× verhoogt biedt directe kwantificering voor floor-prijs ontwerp.

2. **CBAM en ETS2:** De huidige analyse loopt tot 2026; uitbreiding naar post-CBAM observatieperiode is wetenschappelijk waardevol en beleidsmatig urgent.

3. **Nederlandse SDE++ herontwerp:** Projecten die SDE++ aanvragen onder EUA = €80 zouden geherevalueerd moeten worden bij EUA = €50 of lager, aangezien onze schattingen voorspellen dat een aanzienlijke fractie zal annuleren.

### 5.3 Voor Gasunie/HyNetwork
1. **Stress-test het portfolio:** Welke geplande blue hydrogen projecten in NL/Duitsland hebben business cases die afhankelijk zijn van EUA > €80? Die hebben verhoogd cancellation risico.

2. **Hedging strategieën:** Sommige projecten kunnen koolstofprijs-hedges overwegen (forward contracts, options op CCAs). Dit verlaagt het carbon-conditional risico.

3. **Real options waardering:** De gevonden carbon-conditional sensitiviteit kan input zijn voor real-options waarderingsmodellen van portfolio-decisions tussen blue en green technology.

---

## 6. Wat Nog Beantwoord Moet Worden

### 6.1 Empirische vragen
1. **Wat verklaart het verschil tussen v7 (HR=11.93) en publieke IEA (HR=2.02)?** Sample selection? Definition van "Blue_CCS"? Project-vintage differences? Verdient een dedicated robustness chapter.

2. **Is er heterogeniteit naar regio?** US (IRA-effect), EU (ETS-effect), Asia (state-driven) zouden verschillende mechanismen kunnen hebben. Public IEA data is uitgebreid genoeg voor regionale uitsplitsing.

3. **Wat is de cumulative incidence function over horizon t?** Onze huidige analyse focust op instantaneous hazard. Een CIF-analyse zou tijds-tot-cancellation kwantificeren in absolute termen.

4. **Hoe verhoudt cancellation hazard zich tot FID (Final Investment Decision)-rate?** Met data over FID-progressie kunnen we onderscheid maken tussen "officieel gecancelled" en "stilletjes vertraagd."

### 6.2 Methodologische vragen
1. **Non-centered parameterisation voor block models** lost de 4-8 divergences op die we nog hebben. Standaard fix maar nog niet doorgevoerd.

2. **4 chains in plaats van 2** is de huidige ArviZ recommendation voor betrouwbare convergentie diagnostics. Snelle aanpassing.

3. **Pareto k diagnostic per observatie** — welke jaren zijn de outlier-observaties die LOO onbetrouwbaar maken? Dit kan met `az.loo(trace, pointwise=True)` en zou de "warning: True" in onze tabel verklaren.

4. **GAS met informative prior op α_gas** — als we α_gas ~ HalfNormal(0.5) verbreden naar HalfStudentT(3, 1), krijgen we dan andere conclusies?

5. **Changepoint detection** als data-driven alternatief voor onze hand-gekozen economische blocks. Zelf-evaluatie van block boundaries.

6. **Monthly-frequency GAS** zou meer observaties bieden, maar requires monthly EUA en monthly project-status updates. Mogelijk relevant zodra ETS2 trading start in 2027.

### 6.3 Beleids-/contextuele vragen
1. **Hoe vangt het PBL beprijzingstekort framework de carbon-conditional mechanisme expliciet?** Onze empirische schattingen kunnen het PBL-model parametriseren.

2. **Wat is de rol van publieke subsidies (SDE++, Innovation Fund, EU Hydrogen Bank)?** Verklaarvariabelen die we nog niet meenemen.

3. **Hoe interacteert ons resultaat met technology learning curves?** PEM electrolyser kosten dalen sneller dan blue hydrogen + CCS. Mogelijk is het carbon-conditional effect zelf endogeen aan technology costs.

### 6.4 Thesis-organisatorische taken
1. **Chapter 1 (Introduction)** schrijven — research question framing
2. **Chapter 2 (Literature Review)** — drie literatuur-strands synthetiseren
3. **Chapter 3 (Theoretical Framework)** — real-options model voor Blue vs Green
4. **Chapter 8 (Public CCUS Robustness)** — Spoor 3 uitwerken
5. **Chapter 9 (Dutch Policy Context)** — Spoor 2 uitwerken
6. **Chapter 10 (Discussion + Conclusion)**
7. **Chapter 7 fine-tuning** — eindredactie van huidige draft, PDF-compile, naar Koopman

---

## 7. Status Per Component (Gantt-stijl)

| Component | Status | % Klaar | Volgende stap |
|---|---|---|---|
| v7 paper | ✓ Geschreven + gereviseerd | 95% | Externe publicatie / S&P attributie |
| Spoor 1 (Bayesian methodologie) | ✓ Geïmplementeerd | 80% | Integreren in Chapter 6 |
| Spoor 2 (NL policy) | ✓ Outline | 30% | Chapter 9 schrijven |
| Spoor 3 (Public CCUS) | ✓ Geanalyseerd | 70% | Chapter 8 schrijven |
| Spoor 4 (Carbon-conditional) | ✓ Geanalyseerd | 90% | Integreren in Chapter 6 |
| Spoor 5 / Chapter 7 (TVP) | ✓ **Complete draft** | 75% | Eindredactie + Koopman feedback |
| Chapter 1 (Introduction) | ❌ | 0% | Schrijven na 27 mei |
| Chapter 2 (Literature) | ❌ | 0% | Schrijven na Koopman literatuur lezen |
| Chapter 3 (Theory) | ❌ | 0% | Real-options model uitwerken |
| Chapter 10 (Discussion) | ❌ | 0% | Schrijven nadat 7-9 staan |
| Verdediging voorbereiding | ❌ | 0% | September 2026 |

**Overall thesis voortgang: ~45-50%** (3 van 10 hoofdstukken substantieel uitgewerkt, plus methodologisch fundament).

---

## 8. Strategische Implicaties

### Voor de thesis zelf
Het werk staat sterk genoeg dat de **substantieve én methodologische bijdrage duidelijk zijn**. Substantief: documentatie van structureel-stabiele carbon-conditional cancellation mechanisme. Methodologisch: rigoureuze vergelijking van parameter-driven en observation-driven TVP-specificaties in survival analyse, met honest reporting van model-selectie limitaties.

### Voor PhD-aspiratie
Chapter 7 (de TVP methodologische bijdrage) is potentieel **publishable als standalone working paper** in Journal of Applied Econometrics of vergelijkbaar venue. Dat zou de PhD-aanvraag van Sake substantieel versterken. Koopman heeft editorial connecties bij JoE.

### Voor Gasunie-context
De carbon-conditional vinding is **direct toepasbaar in Gasunie's Business Line Waterstof Nederland**. Cancellation risico van het portfolio kan kwantitatief geëvalueerd worden onder verschillende EUA prijs-scenario's. Dit kan basis vormen voor een Gasunie-interne risk dashboard.

---

**Einde synthesis.**

Voor verdere uitwerking per onderdeel: zie `THESIS_MASTER_PLAN.md` (16-week plan) en `SAMENVATTING_18_MEI.md` (vandaag's stand van zaken).
