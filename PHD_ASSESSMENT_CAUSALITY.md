# PhD-Worthiness Assessment + Causal Identification Strategy
**Sake Saakstra | MSc EOR Financial Track | 18 mei 2026**

---

## 1. PhD-Worthiness: Eerlijke Self-Assessment

Acht criteria die typisch gebruikt worden voor PhD-waardige econometric onderzoek:

| Criterium | Status | Score | Toelichting |
|---|---|---|---|
| **1. Originele bijdrage** | ✓ Sterk | 8/10 | Eerste TVP-state-space hazard model toegepast op hydrogen project cancellation. Carbon-conditional finding nieuw in deze context. |
| **2. Methodologische rigor** | ✓ Sterk | 8/10 | Drie nested specificaties, Bayesian HMC, formal LOO/WAIC vergelijking, robustness checks. Gebruik van Koopman's eigen framework. |
| **3. Theoretische grounding** | ⚠️ Matig | 5/10 | Real-options theorie genoemd maar niet uitgewerkt tot een formeel model dat onze empirische voorspellingen genereert. Mist een rigorous theoretical chapter. |
| **4. Empirische validatie** | ⚠️ Matig-Sterk | 6/10 | Robust over data sources (v7 + IEA) en inferentie-methoden. Maar identificatie-strategie is associational, niet causal (zie sectie 2). |
| **5. Publishability** | ✓ Sterk | 7/10 | Chapter 7 (methodologische bijdrage) is op zichzelf publishable in Journal of Applied Econometrics. Substantieve vinding past bij Energy Economics of Resource & Energy Economics. |
| **6. Onafhankelijkheid researcher** | ✓ Sterk | 8/10 | Eigen onderzoeksprogramma, eigen data-acquisitie, eigen methodologische keuzes, in staat tot rigoureuze zelfkritiek. |
| **7. Reproduceerbaarheid** | ✓ Zeer sterk | 9/10 | Alle code op disk, scripts gedocumenteerd, runnable in Python omgeving, outputs versioned. |
| **8. Externe relevantie** | ✓ Sterk | 8/10 | Direct relevant voor EU ETS beleidsontwerp, SDE++ herontwerp, Gasunie portfolio risk. PBL beprijzingstekort framework kan parametriseerd worden met onze schattingen. |

**Aggregate: ~7/10.** Sterk MSc-thesis, met duidelijke PhD-richting. **Hoofdpunt voor verbetering: causale identificatie.**

---

## 2. Eerlijk Over Causaliteit: Wat We Hebben Is Associationeel

### Wat ons huidige model aantoont
> "Wanneer EUA prijzen laag zijn, zien we hogere Blue/PEM cancellation hazard ratios."

### Wat het NIET aantoont
> "Lage EUA prijzen veroorzaken hogere Blue cancellation rates."

### Vier alternatieve verklaringen voor onze waargenomen patroon

| Verklaring | Mechanisme | Toetsbaar? |
|---|---|---|
| **A. Direct causaal effect** | Lage EUA → blue projecten minder rendabel → meer cancellations | Klassieke causale claim, vereist exogene EUA-variatie |
| **B. Selectie / sortering** | Hoge EUA periodes trekken meer commited blue sponsors aan → minder cancellations | Vereist project-vintage controls + entry-bias correctie |
| **C. Confounding via macro** | Macro-omstandigheden (recessie, gas-prijs, kapitaalkosten) bepalen zowel EUA als blue project survival | Vereist macro controls + sectorale fixed effects |
| **D. Reverse causation** | Cancellation-verwachtingen drijven sponsors om EUA-allocaties te dumpen → kunstmatig lagere EUA tijdens periodes van veel cancellations | Onwaarschijnlijk gegeven EUA marktomvang, maar formeel uit te sluiten |

Onze huidige analyses ondersteunen vooral **(A) als consistent met data**, maar sluiten **(B), (C), (D) niet uit**.

### Waarom dit op MSc-niveau acceptabel is, maar op PhD-niveau onvoldoende

Voor een **MSc thesis** is een rigoureus uitgewerkte associationele analyse met expliciete acknowledgment van causale limitaties **prima**. Bolton-Kacperczyk (2021, JFE) doet dit ook deels: hun hoofdvinding ("emission stocks earn premium") is grotendeels associationeel.

Voor een **PhD thesis onder Koopman** moeten we hoger mikken. Koopman zelf publiceert weliswaar veel methodologische papers waar identificatie via tijds-structuur loopt (Granger causality, state-space), maar de PhD-standaard in financial econometrics (waar wij zitten) eist een **expliciete identification strategy**.

---

## 3. Waarom Onze Associationele Bevindingen Toch Waardevol Zijn

Voordat ik causale strategieën voorstel: laten we niet onderwaarderen wat we hebben.

1. **Robuustheid is bewijs.** Onze finding overleeft alternatieve data (v7 → IEA), alternatieve inferentie (frequentist → Bayesian), alternatieve specificaties (static → blocks → GAS). Dat is moeilijk te verklaren door één confounding mechanisme — het zou meerdere confounders moeten zijn die elk de robustheid overleven.

2. **Quantitative consistency met theorie.** Real-options theorie voorspelt **specifiek** dat blue projects (hoge fixed costs, lage variable cost gevoeligheid voor carbon prices) een carbon-conditional hazard hebben met negatieve β_int. We zien precies dat. De magnitude (β_int ≈ -1.5) is plausibel.

3. **Time-invariantie is informatief.** Als het effect zou worden gedreven door tijdelijke confounders (zoals de IRA in 2022 of de pandemic), zou je tijds-variatie zien. We zien geen tijds-variatie. Dit suggereert dat het mechanisme **structureel** is, niet conjunctureel.

4. **Within-block coherentie.** In de Block 2 (2023-2024) analyse zagen we direct dat HR toenam van 1.87 (bij EUA €82) naar 4.70 (bij EUA €65). Dit is binnen een 2-jaar window — minder vatbaar voor langzaam-veranderende confounders.

---

## 4. Concrete Causale Identificatie-Strategieën

Vijf strategieën, gerangschikt op feasibility met onze huidige data. Hoe verder naar beneden, hoe meer data-acquisitie nodig.

### Strategie 1: Difference-in-Differences rond IRA (Aug 2022) — HOOG FEASIBLE

**Idee:** De Inflation Reduction Act (16 augustus 2022) introduceerde de 45V tax credit voor green hydrogen ($3/kg voor < 0.45 kg CO2eq/kg H2). Dit is een **exogene shock** die green hydrogen projecten in de VS differentieel raakte ten opzichte van Europese projecten.

**Design:**
- **Treated group:** US-based hydrogen projects
- **Control group:** EU-based hydrogen projects  
- **Pre-periode:** Aug 2021 - Aug 2022
- **Post-periode:** Aug 2022 - Aug 2024
- **Outcome:** Project cancellation hazard, gesplitst per tech (Blue vs PEM)
- **DiD interactie:** US × Post × Blue (testen of IRA differentieel green redde en/of blue ondermijnde in de VS)

**Identification assumption:** Parallel trends voor US vs EU hydrogen projecten in afwezigheid van IRA. Testbaar via pre-trends in de jaren 2019-2022.

**Implementatie:**
- Aggregeer project data naar (regio, tech, periode) cellen
- Estimate triple-DiD: hazard ~ US + Post + Blue + US×Post + US×Blue + Post×Blue + US×Post×Blue
- De β voor de driewegsinteractie test de causale claim

**Wat dit zou toevoegen:** een claim dat IRA een **causaal** effect had op blue vs green relatieve cancellation, wat indirect onze EUA-finding versterkt (twee verschillende carbon-price-achtige shocks, gelijksoortige effecten).

### Strategie 2: Event Study rond EUA shocks — MEDIUM FEASIBLE

**Idee:** Identificeer **plotselinge EUA prijs-bewegingen** die niet voorspeld werden door fundamentals. Bijvoorbeeld:
- Brexit referendum uitkomst (Jun 2016): EUA -10% in een week
- Russia-Ukraine oorlog start (Feb 2022): EUA +25% in twee weken
- ETS Market Stability Reserve aankondiging (Jul 2018): EUA +15% in een maand
- Free allocation phase-out details (Apr 2023): variabele response

**Design:**
- Event windows: [-3, +3] maanden rondom elke shock
- Cancellation hazard pre- versus post-event, voor blue en green afzonderlijk
- Difference: heeft Blue-PEM cancellation differential zich significant veranderd binnen het event window?

**Identification assumption:** EUA shocks zijn exogeen aan project-specifieke factoren die cancellation drijven. Plausibel voor geopolitieke shocks; minder voor beleidsaankondigingen die anticipeerbaar zijn.

**Implementatie:**
- Event-time normalization in person-month panel
- Difference-in-differences in event time
- Bayesian state-space met intervention dummy

**Wat dit zou toevoegen:** identificatie van het mechanisme via short-run shocks waar confounding minder waarschijnlijk is.

### Strategie 3: Instrumental Variable via beleids-timing — MEDIUM FEASIBLE

**Idee:** Een **instrumental variable** moet (a) EUA prijzen beïnvloeden en (b) cancellation NIET direct beïnvloeden behalve via EUA.

Kandidaten:
- **Phase IV cap-trajectorie aankondigingen** (eerst in 2014, opgenieuw in 2018, 2020). Deze beïnvloeden EUA forward expectations maar zijn niet direct gerelateerd aan specifieke hydrogen project cancellations.
- **Energy intensity benchmark revisies** (industrial sector regelmatig herzien). Beïnvloeden EUA marginal cost maar niet hydrogen sector.
- **Brexit als instrument** voor EUA (UK uit ETS in Jan 2020): structurele breuk in marktvraag.

**Design:** 
- Eerste fase: regress EUA_t op instrument(en) + controls
- Tweede fase: cancellation hazard op gepredicteerde EUA_t

**Probleem:** Hydrogen sector is **niet** geheel exogeen aan EU ETS beleid. Hydrogen heeft eigen beleidsregimes (RED III, Hydrogen Bank) die kunnen correlleren met EUA-beleidsaankondigingen.

**Wat dit zou toevoegen:** Klassiek IV-causal claim. Zwakker dan DiD vanwege instrument validity zorgen.

### Strategie 4: Synthetic Control Method — HOOG FEASIBLE maar interpretatie subtiel

**Idee:** Voor elke gecancelde blue project, construeer een "synthetic twin" van non-cancelled projects met vergelijkbare baseline characteristics. Vergelijk EUA-exposure van actual vs synthetic.

**Design:**
- Matching op project size, region, vintage, sponsor type
- Outcome: realized EUA prices over project lifecycle for cancelled vs synthetic
- Test: had cancelled projects systematic lower EUA exposure?

**Probleem:** EUA is een marktprijs gemeenschappelijk voor alle projecten — verschillen ontstaan alleen door verschillende project-tijdvensters.

### Strategie 5: Regression Discontinuity rond SDE++ thresholds — DATA-INTENSIEF

**Idee:** SDE++ Nederland heeft project-size thresholds en EUA-correctie mechanismen. Projects net boven/onder een drempel krijgen kwalitatief verschillende behandeling.

**Probleem:** Vereist gedetailleerde SDE++ uitkering-data per project. Niet beschikbaar in v7 of IEA databases.

---

## 5. Geadviseerde Volgorde Voor PhD-Trajectorie

### Prioriteit 1: DiD rond IRA (Strategie 1)
**Waarom eerst:** Hoogst feasible met huidige data. Directe causale interpretatie. Beleidsrelevantie (IRA effect is een actuele beleidsdebat). Past binnen 6 weken werk.

**Implementatie:** 
- Filter project-data op US vs EU registration
- Build pre/post Aug 2022 panel
- Schat triple-DiD met Bayesian inferentie
- Robustness via pre-trend tests + placebo periodes

**Plek in thesis:** Nieuw Chapter 7b ("Causal Evidence from the IRA Shock") of integratie in Chapter 7 als robustness sectie.

### Prioriteit 2: Event Study rond Feb 2022 (Russia-Ukraine)
**Waarom tweede:** Tweede meest plausibele identification. EUA spike was duidelijk exogen aan hydrogen sector. Korte tijdvenster minimaliseert confounding.

**Implementatie:**
- Event windows in maandelijkse data
- Bayesian state-space met intervention break
- Compare hazard rates pre/post in 6-month windows

### Prioriteit 3: Theoretisch hoofdstuk (Real-Options Model)
**Waarom derde:** Op zichzelf geen empirische identificatie, maar **verbetert de causale interpretatie van bestaande resultaten** door expliciet mechanisme te formaliseren.

**Implementatie:** 
- Pindyck-stijl real-options model voor blue vs green project value
- EUA als state variable
- Genereer voorspellingen die we empirisch testen
- Onze static β_int ≈ -1.5 wordt expliciete model-implicatie

---

## 6. Wat Dit Doet Voor PhD-Worthiness

Na implementatie van Strategie 1+2+3 verhogen we score:

| Criterium | Voor | Na |
|---|---|---|
| 1. Originele bijdrage | 8 | 9 (causaal mechanisme nieuw in literatuur) |
| 2. Methodologische rigor | 8 | 9 (formele identification + observation-driven TVP) |
| 3. Theoretische grounding | 5 | **8** (formal real-options model) |
| 4. Empirische validatie | 6 | **9** (causale identification toegevoegd) |
| 5. Publishability | 7 | 9 (publishable in top-tier journals) |

**Aggregate: ~7/10 → ~8.5/10**. Dat is geconverteerde PhD-richting.

---

## 7. Risico's

### Risico 1: IRA-DiD geeft geen significante interactie
**Wat gebeurt:** Als treatment effect te klein is gegeven sample size (~150 US projects, slechts ~25 EU + 30 US events post-IRA), kan de DiD te wijde CrI hebben.

**Mitigatie:** 
- Pre-registreer de hypothese vóór data-analyse (open science practice)
- Multiple specifications (different control groups: EU vs UK vs Asia)
- Bayesian power analysis vooraf

### Risico 2: Event study confounders
**Wat gebeurt:** Russia-Ukraine veroorzaakte ook gas-prijs shock, kapitaalkosten verandering, supply chain disruption. EUA effect kan niet geïsoleerd worden.

**Mitigatie:**
- Triple-interaction met natural gas prijs als macro-control
- Compare met andere EUA shocks zonder gas-correlatie

### Risico 3: Theoretical model te idiosyncratic
**Wat gebeurt:** Pindyck real-options model moet voldoende algemeen zijn maar specifiek genoeg om voorspellingen te genereren.

**Mitigatie:** 
- Begin met simpel stochastic DCF model
- EUA als geometric Brownian motion
- Calibreer parameters op realistic blue vs green project specs

---

## 8. Aanbeveling Voor Koopman-Meeting

In week 22-23, presenteer aan Koopman:

1. **Status:** Current findings zijn robust associationeel. Chapter 7 draft staat.
2. **Erkenning:** PhD-niveau vereist causale identification.
3. **Voorstel:** DiD rond IRA als primaire causal identification strategy (Chapter 7b).
4. **Vraag:** Past dit binnen Koopman's interest area (state-space causality / intervention analysis)?

Koopman heeft gewerkt aan intervention analysis in state-space modellen (zie zijn 2008 paper met Lit & Lucas over forecasting interventions, en zijn 2014 Statistica Sinica paper over breakpoint state-space). De DiD rond IRA past hier elegant in als state-space intervention test.

---

## 9. Samenvattend

**Vraag:** Zitten we al in de goede richting voor PhD-niveau?

**Antwoord:** Ja, **substantieel** maar **niet volledig**. We hebben:
- ✓ Originaliteit (TVP hazard model in hydrogen sector)
- ✓ Rigor (drie nested specificaties, Bayesian HMC, LOO/WAIC)
- ✓ Robustheid (data sources, inferentie methoden, specificaties)
- ⚠️ Theoretische framework (begint, niet voltooid)
- ⚠️ **Causale identificatie (nog niet toegevoegd)**

**Vraag:** Is causaal verband zichtbaar?

**Antwoord:** Wat we zien is **consistent met causaliteit** maar niet **identificerend causal**. Vier alternatieve verklaringen (direct, selectie, confounding, reverse) zijn niet uitgesloten. Onze huidige robustness sluit sommige (zoals data-source artefact, methode-keuze artefact) wel uit, maar niet de fundamentele endogeneity.

**Concrete actie:** Implementeer DiD rond IRA-shock (Strategie 1) als volgende stap. Dit is 4-6 weken werk en transformeert het thesis-verhaal van "associationeel patroon" naar "causaal mechanisme."

**Maar belangrijk:** Begin niet met causale strategie tot je Koopman gesproken hebt. Hij kan voorkeur hebben voor een ander identification design (bijv. zijn eigen state-space intervention framework). Geef hem de eerste keuze.

---

**Einde assessment.**
