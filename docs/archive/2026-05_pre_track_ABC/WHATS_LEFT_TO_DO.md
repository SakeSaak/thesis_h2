# Wat Is Er Nog Te Doen Voor De Thesis?
**Sake Saakstra | 18 mei 2026 | Verdediging Sep-Nov 2026**

---

## TL;DR

| Categorie | Status | Geschatte tijd |
|---|---|---|
| **Analytisch werk klaar** | ~75% klaar | — |
| **Analytisch werk nog te doen** | 4 essential items + 5 nice-to-have | 80-140 uur |
| **Schrijfwerk** | ~25% klaar (Chapter 7 draft) | 250-350 uur |
| **Defensievoorbereiding** | 0% | 30-40 uur |
| **Totaal nog te doen** | — | **~360-530 uur** |

Beschikbaar in 10-14 weken vóór August deadline: ~200-280 uur (bij 20-25 u/week thesis-tijd naast 32u Gasunie). **Dat is krap maar haalbaar als we strict prioriteiten stellen.**

---

## 1. Wat Analytisch Al Klaar Is ✓

| Analyse | Folder | Status |
|---|---|---|
| v7 Cox PH + Fine-Gray | `01_data/intermediate/` | Volledig ✓ |
| Bayesian Cox PH (4-prior sensitivity) | `06_thesis_extensions/01_bayesian_methodology/` | Volledig ✓ |
| Public IEA CCUS robustness (3 Cox modellen) | `06_thesis_extensions/03_public_data_robustness/` | Volledig ✓ |
| Frequentist v7 carbon-conditional replicatie | `06_thesis_extensions/04_carbon_conditional/` | Volledig ✓ |
| Bayesian carbon-conditional sensitivity | `06_thesis_extensions/04_carbon_conditional/` | Volledig ✓ |
| Static aggregaat model | `06_thesis_extensions/05_state_space_tvp/results_robustness/` | Volledig ✓ |
| 4-block TVP | `results_blocks/` | Volledig ✓ |
| GAS TVP (d=0, ½, 1) | `results_gas/` + `results_robustness/` | Volledig ✓ |
| LOO/WAIC model comparison | `results_robustness/` | Volledig ✓ |
| 3/5-block sensitivity | `results_robustness/` | Volledig ✓ |
| Block 2 diagnostic | `results_blocks/` | Volledig ✓ |

**Analytisch fundament is sterk.** De methodologische hoofdbijdrage (Chapter 7) staat.

---

## 2. Analytisch Werk Nog Te Doen

### Tier A: ESSENTIAL voor PhD-aspirational MSc thesis

**A1. Methodologische refinements voor Chapter 7** (~15-20 uur)
- Non-centered parameterisatie voor block models (lost 4-8 residuele divergences op)
- 4 chains in plaats van 2 (ArviZ recommended voor LOO betrouwbaarheid)
- Pareto k diagnostic per observatie (welke jaren zijn LOO-outliers?)
- Eventueel: GAS met informative prior op α_gas

**Waarom essential:** Koopman zal divergences en LOO warnings noteren. Nu fixen voorkomt deze als kritiek bij verdediging.

**A2. Theoretisch hoofdstuk (Chapter 3): real-options model** (~50-70 uur)
- Pindyck-stijl real-options model voor blue vs green project value
- EUA als state variable (geometric Brownian motion)
- Closed-form of numeric solution voor optimal investment timing
- Genereer voorspellingen: β_int < 0, magnitude functie van CAPEX-ratio
- Calibratie op realistische blue vs green project parameters

**Waarom essential:** Onze grootste zwakte in PhD-assessment is theoretische grounding (score 5/10). Een formal theoretical model brengt dat naar 8/10. Het verbetert ook causal interpretation van bestaande empirische resultaten.

**A3. EÉN causale identification-strategie (DiD rond IRA)** (~60-80 uur)
- Data prep: US vs EU project filtering, pre/post Aug 2022 panel
- Bayesian triple-DiD specification: hazard ~ US × Post × Blue
- Parallel-trends pre-test (2019-2022)
- Robustness: verschillende control groups (EU, UK, Asia)
- Schrijfwerk (Chapter 7b)

**Waarom essential:** Verandert thesis-narratief van "associationeel patroon" naar "causaal mechanisme via beleids-shock identification." Past direct in Koopman's intervention-analysis framework. Verhoogt empirische validatie van 6/10 naar 9/10.

**A4. Pre-registration document** (~5-8 uur)
- 2-3 pagina formal analysis plan voor causale strategieën
- Hypotheses, voorspellingen, robustness checks, reporting standards
- Verzekering tegen unconscious p-hacking
- Wetenschappelijk maturiteit-signaal voor Koopman + commissie

**Waarom essential:** Maakt onderzoek pre-registeerbaar (OSF) en immuniseert tegen "you fitted post-hoc" kritiek.

**Subtotaal Tier A: ~130-180 uur**

### Tier B: STRONGLY RECOMMENDED (als tijd toelaat)

**B1. Heterogeneous treatment effects** (~30-40 uur)
- Carbon-conditional effect per project-subgroep (capital-intensity, sponsor type, region)
- Voorspellingen uit real-options theorie testen
- Bouwt mechanism story los van causale identificatie

**B2. Tweede causale strategie: within-sponsor comparison** (~30-40 uur)
- Filter projecten met sponsors die zowel Blue als Green hebben
- Hazard model met sponsor fixed effects
- Triangulatie met DiD-IRA: convergeren bevindingen?

**B3. Oster (2019) sensitivity analysis** (~10-15 uur)
- Robust check tegen unobserved confounding
- "Hoeveel ongeobserveerde confounding zou er moeten zijn om effect te nullify?"
- Quick implementatie via standard packages

**Subtotaal Tier B: ~70-95 uur**

### Tier C: NICE TO HAVE (post-MSc / PhD trajectory)

**C1. Negatieve controls** (hydro/wind project survival) — vereist additionele data, ~20-30 uur
**C2. Mediation analysis** — vereist mediator data niet beschikbaar
**C3. Event study rond Russia-Ukraine (Feb 2022)** — additional triangulation, ~25-30 uur
**C4. Bounds analysis (Manski-style)** — partial identification, ~20 uur
**C5. Monte Carlo robustness van model selection** — power analysis voor LOO, ~15 uur

**Niet doen voor MSc-deadline.** Bewaar als potentiële PhD-extensions.

---

## 3. Schrijfwerk

| Hoofdstuk | Status | Werk | Tijdsraming |
|---|---|---|---|
| 1. Introduction | ❌ Niet begonnen | Research question, contribution claims, structure | 25-35 u |
| 2. Literature Review | ❌ Niet begonnen | 3 strands: survival, TVP, hydrogen+carbon | 40-50 u |
| 3. Theoretical Framework | ❌ Niet begonnen | **Real-options model (zie A2)** | Bovenop A2: 15-20 u schrijven |
| 4. Data | ❌ Niet begonnen | v7 + IEA, panel construction, descriptives | 20-30 u |
| 5. Static Baseline | ❌ Niet begonnen | Replicate v7 + Bayesian (Spoor 4) | 30-40 u |
| 6. Bayesian Methodology | ❌ Niet begonnen | Spoor 1 uitwerken | 25-35 u |
| **7. TVP State-Space** | ✓ Draft (75%) | Eindredactie + integratie A1 refinements | 15-25 u |
| **7b. Causal Identification** | ❌ Niet begonnen | DiD-IRA writeup (na A3) | 25-35 u |
| 8. Public CCUS Robustness | ❌ Niet begonnen | Spoor 3 uitwerken | 25-30 u |
| 9. Dutch Policy Context | ❌ Niet begonnen | Spoor 2 outline uitwerken | 30-40 u |
| 10. Discussion + Conclusion | ❌ Niet begonnen | Synthesis | 20-30 u |

**Subtotaal schrijfwerk: ~270-370 uur**

---

## 4. Defensievoorbereiding

- Slidedeck maken: ~10-15 u
- Mock defense met collega's: ~5-8 u
- Q&A voorbereiding: ~10-15 u
- Eventuele revisies na committee feedback: ~5-10 u

**Subtotaal: ~30-50 uur**

---

## 5. Tijdsbudget Realiteits-Check

### Beschikbare tijd
- Vanaf 18 mei tot eind augustus = **~15 weken** voor submission
- 20-25 uur/week thesis (naast 32u Gasunie) = **300-375 uur beschikbaar**

### Benodigde tijd voor PhD-aspirational kwaliteit
- Tier A analytisch: 130-180 u
- Schrijfwerk: 270-370 u
- Defense prep: 30-50 u
- **Totaal: 430-600 uur**

### Conclusie van rekensom

**Het PhD-aspirational pad is krap.** Beschikbaar 300-375 u, benodigd 430-600 u. Tekort van ~100-225 uur.

**Drie scenario's:**

**Scenario A: Volledig PhD-aspirational** (alle Tier A)
- Vereist 5-7 u/week extra (richting 30-32 u/week thesis)
- Realistisch alleen als Gasunie tijdelijk minder claim heeft of vakantie inzet
- Risico: burnout

**Scenario B: Pragmatisch MSc-niveau met één extra** (Tier A1 + A2 + A4, GEEN A3)
- Geen causale identificatie, wel theoretisch model + refinements
- 80-100 u Tier A + 270-370 u writing + 40 u defense = 390-510 u
- Past beter binnen budget
- Thesis is **stevig MSc met PhD-direction signal** maar zonder causal identification

**Scenario C: Sober MSc-niveau** (Geen Tier A extras)
- Alleen A1 refinements en A4 pre-registration
- 20-30 u Tier A + 270-370 u writing + 40 u defense = 330-440 u
- Past comfortabel
- Thesis is **rigoreus MSc** maar zonder methodologisch hoofdstuk-upgrade

---

## 6. Mijn Geadviseerde Volgorde

Ik adviseer **Scenario B met optionele A3 voor de zomer**:

### Mei 18 - Juni 7 (3 weken, ~60-75 uur)
1. **Lees Koopman 2000 JRSSB + Durbin-Koopman Ch 9-11** (~20 uur)
2. **27 mei Gasunie meeting** (S&P attributie, PhD support)
3. **Email Koopman met Chapter 7 draft + 30-min meeting aanvraag** (week 22-23)
4. **A1: Methodologische refinements Chapter 7** (non-centered, 4 chains, Pareto k) (~15-20 uur)
5. **A4: Pre-registration document** (~5-8 uur)

### Juni 8 - Juli 5 (4 weken, ~80-100 uur)
6. **A2: Theoretisch hoofdstuk (real-options model)** (~50-70 uur)
7. **Chapter 1 schrijven** (Introduction) (~25-35 uur)

### Juli 6 - Augustus 2 (4 weken, ~80-100 uur)
8. **Chapter 2 schrijven** (Literature Review) (~40-50 uur)
9. **Chapter 4 schrijven** (Data) (~20-30 uur)
10. **Chapter 5 + 6 schrijven** (Static + Bayesian) (~50-70 uur)

### Augustus 3 - Augustus 30 (4 weken, ~80-100 uur)
11. **Chapter 7 eindredactie** met A1 refinements (~15-25 uur)
12. **Chapter 8 + 9 schrijven** (Public CCUS + NL Policy) (~55-70 uur)
13. **Chapter 10 schrijven** (Discussion + Conclusion) (~20-30 uur)

### September 1-15 (2 weken, ~40-50 uur)
14. **Submission** ~mid-September
15. **Defense prep** start

### **Optioneel: A3 (DiD-IRA causale identification)** als tussentijd toelaat
- Past best in **eind juni/begin juli** als Theoretical Chapter sneller dan verwacht klaar is
- Of: doe het pas **na MSc verdediging** als PhD-paper materiaal

### **Optionele schoot-richting:** Defense in **November** ipv September
Geeft 2 extra maanden = ~200 extra uur. Dan kan A3 (causale identificatie) WEL binnen MSc scope. Bespreek dit met Koopman en VU.

---

## 7. Het Eerlijke Antwoord Op Je Vraag

**"Zijn alle bevindingen voor de thesis klaar en is het alleen nog schrijfwerk?"**

**Nee, drie dingen ontbreken nog die wel essential zijn:**

1. **Theoretisch hoofdstuk (real-options model)** — onze grootste structurele zwakte. Zonder formal theory chapter mist het ankerpunt dat empirische findings betekenis geeft.

2. **Methodologische refinements van Chapter 7** — non-centered parameterisatie, 4 chains, Pareto k diagnostics. Quick wins die kritiek bij verdediging voorkomen.

3. **Pre-registration document** — wetenschappelijk maturiteit-signaal, kost weinig tijd.

**Plus één wenselijke maar potentieel skip-bare item:**

4. **Causale identificatie (DiD-IRA)** — verhoogt PhD-waardigheid van 7/10 naar 8.5/10 maar kost 60-80 uur. **Optioneel** afhankelijk van tijdsbudget en Koopman advies.

**Verder is het:**
- Schrijfwerk voor 9 hoofdstukken (~270-370 uur)
- Defense prep (~30-50 uur)

**De vraag is dus niet "is alles af?" maar "welke scenario kies je?":**
- **Scenario A**: full PhD-aspirational, krap, risico burnout
- **Scenario B**: pragmatisch met theoretical + refinements, geen causaliteit
- **Scenario C**: sober MSc, alleen writing + minor refinements

**Mijn advies: Scenario B met optionele A3 als bonus.** Schrijf eerst de essentials (Chapter 7 eindredactie + theoretisch + 9 hoofdstukken). Als tijd toelaat na Juli, voeg DiD-IRA toe. Anders bewaar causaliteit als PhD-paper materiaal na verdediging.

**Critical input nodig:** wat zegt Koopman in week 22-23? Hij kan voorkeur hebben voor specifieke richting die de keuze tussen scenarios B en A bepaalt.

---

**Einde planning document.**
