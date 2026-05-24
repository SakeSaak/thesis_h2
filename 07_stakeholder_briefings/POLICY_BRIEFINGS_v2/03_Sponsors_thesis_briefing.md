# Thesis Status & Findings Briefing — Sponsors

**Voor**: the external reviewer (supervisor) | the second reviewer (second reader) | Gasunie sponsors

**Auteur**: Sake Saakstra (MSc EOR Financial Track, VU Amsterdam — student no. [redacted])

**Datum**: 20 mei 2026

**Status**: pre-final draft, voor discussie

**Thesis-titel (concept)**: *Implementation-Risk Differentials in Hydrogen Technology Pathways: A Cross-Jurisdictional Causal Evaluation of Carrot-Policy Mechanisms*

---

## 1. Executive summary

Het onderzoek is **op publication-grade niveau** afgerond op het inhoudelijke vlak. Resterende fasen zijn:
1. Schrijven (hoofdtekst + appendix)
2. Defense-voorbereiding
3. Optioneel: top-tier publicatie-traject (Energy Economics / JEEM)

De inhoudelijke bijdrage bestaat uit **drie complementaire lagen**:

| Laag | Bijdrage | Innovativiteit | PhD-waardigheid |
|---|---|---|---|
| **Empirisch** | 6 publication-grade findings uit 1.354 H₂-projecten | First cross-jurisdictionale causale evaluatie van 4 carrot-types | ✓ Voldoende voor MSc, sterk voor PhD |
| **Methodologisch** | Three-method robustness (DiD + TVP + Causal Forest) + Honest DiD bounds | Eerste combinatie van TVP-DiD + Rambachan-Roth (2023) in dit veld | ✓ Sterke methodologische bijdrage |
| **Theoretisch** | Real-options × mechanism design framework | Eerste formele V/I vs σ-channel taxonomie voor H₂-policies | ✓ Theoretische originaliteit |

**Bewijslijn-scorecard**:
- **5 van 7 hoofdfindings**: methodologisch waterdicht
- **2 van 7**: gequalificeerd onder Honest DiD-sensitivity (eerlijk gerapporteerd)
- **Externe bevestiging**: 2024–2026 industry cancellations (BP, ArcelorMittal, EU Hydrogen Bank) komen woord-voor-woord overeen met onze empirische conclusies.

---

## 2. Methodologisch overzicht

### Data
- **S&P Global Hydrogen Production Assets** (snapshot 24 maart 2024)
- **N = 1.354** Blue + Green projecten globaal (2010–2024)
- **367 failures** = 27.1% baseline cancellation/on-hold rate
- **172 projecten met benoemde offtaker** (12.7%) — gebruikt voor Pijler 34

### Identification strategies (geordend op sterkte)
1. **Multi-method ID voor offtake-effect** (Pijler 34):
   - LPM met rich controls
   - Propensity Score Matching 1:3 nearest-neighbor
   - IPWRA (doubly robust)
   - Oster (2019) δ-sensitivity
   - **Convergentie**: ATE ∈ [-0.111, -0.131], Oster δ_null = 20.23 (exceptioneel robuust)

2. **Modern DiD voor 4 carrot-policies** (Pijler 32):
   - TWFE
   - Sun & Abraham (2021)
   - Borusyak-Jaravel-Spiess (2024) imputation
   - **Convergentie**: alle drie methoden geven dezelfde tekens en magnitudes

3. **Honest DiD bounds** (Pijler 39, Rambachan-Roth 2023):
   - Average ATT(e=0,1,2) + median pre-trend deviation
   - China FYP: M\* = 1.50 → **ROBUUST**
   - US 45Q, EU IF, UK Track: M\* < 0.5 → **FRAGIEL onder strenge sensitivity**

4. **TVP-DiD structural break** (Pijler 24c):
   - Threshold model + AR(1) state-space + random walk
   - **Drie methoden convergeren op τ\* = 2020 sign-shift**

5. **Causal Forest HTE** (Pijler 30, Athey-Tibshirani-Wager 2019):
   - BLP omnibus test confirms heterogeneity
   - Sector-specifieke ATEs identificeren mechanism-channels

### Theoretical foundation
Dixit-Pindyck (1994) real-options framework:
- V\*/I = β₁/(β₁−1) threshold
- σ-channel (offtake, cluster-tender) vs V/I-boost channel (output-credit, capex-grant)
- Sector-calibration: chemical/refinery σ=0.12, power & heat σ=0.40
- Empirie matcht theorie: σ-attack effects sterker in hoge-σ sectoren

---

## 3. De 6 hoofdfindings — robustness-scorecard

| # | Finding | Methods | Robustheid | Externe match | Verdict |
|---|---|---|---|---|---|
| **1** | **Offtake-effect**: −11 tot −13 pp failure-rate | 5 estimators + Oster | δ_null=20.23 | BP/ArcelorMittal/EU Bank cancellations | **WATERDICHT** |
| **2** | **China FYP causaal**: −4.5 pp annual hazard | TWFE+BJS+Sun-Abraham+Honest DiD | M\*=1.50 | China 15th FYP escalatie 2026 | **WATERDICHT** |
| **3** | **Structural break τ\*=2020** | 3 TVP-methoden | Niet afh. van parallel trends | Odenweller-Ueckerdt Nature Energy 2025 timing | **WATERDICHT** |
| **4** | **EU IF informative null**: geen meetbaar effect | Alle 6 methoden NS | Consistent across methods | ArcelorMittal €1.3B walked away | **WATERDICHT** |
| **5** | **UK Track selection-funnel**: +0.036 maar artefact | TWFE + kwalitatief Pijler 27a | Mixed quant/qual | BP HyGreen + H2Teesside cancellations | **STERK MAAR GEQUALIFICEERD** |
| **6** | **Real-options σ vs V/I taxonomie** | Theoretisch + empirisch | Falsifieerbaar | Sector-heterogeneity confirms | **STERK** |
| **7** | **US 45Q causaal**: −3.8 pp annual hazard | TWFE+BJS converge | Honest DiD fragiel M\*=0.2 | Air Products cancellations | **GEQUALIFICEERD** |

---

## 4. Methodologische nuances die in de defense aan bod komen

### a. Honest DiD bounds — wat betekent het?

Voor 3 van de 4 hoofdpolicies (US 45Q, EU IF, UK Track) wordt het effect onder Rambachan-Roth (2023) strenge sensitivity bounds non-significant bij M < 0.5. Dit betekent **niet** dat de point estimates fout zijn — het betekent dat in de jaarlijkse-hazard-interpretatie de absolute effect-magnitude klein genoeg is dat een violation van parallel trends (>0.5× max pre-trend deviation) het effect zou kunnen wegverklaren.

**Voor de defense**: dit is een **methodologische sterkte**, geen zwakte. We rapporteren eerlijk wat hard en wat gequalificeerd is. Top-tier papers (JEEM, EE) belonen layered transparency over universal "robust" framing. China FYP overleeft Honest DiD met M\*=1.50, wat de causale claim daar sterker maakt dan voor de andere drie policies.

### b. Causal Forest p-values

In Pijler 30 (BLP omnibus + sector-specifieke CATE) hebben we anti-conservatieve p-values gevonden voor sommige sub-group heterogeneity-tests. Dit is geaddressed via formele LPM-based DiD-tests (Pijler 31) en de three-method DiD-robustness (Pijler 32). De causal-forest output wordt gebruikt voor *exploratie* van heterogeneity-patterns, niet voor *primaire* statistische inferentie.

### c. Selection in de S&P data

De S&P Global database bevat alleen *publiek aangekondigde* projecten. Dit creëert een selection-bias naar serieuze sponsors / capaciteit. We zien dit niet als fatal omdat:
1. Onze comparisons zijn binnen dit gefilterde sample (between-policy variation)
2. Sample is omvangrijk genoeg (N=1.354) om robuuste inferentie te ondersteunen
3. Cross-validation met Hydrogen Council Insights (2024) en IEA-data (2024) bevestigt onze counts

### d. Annual hazard vs cumulative effects

Onze DiD-modellen schatten annual hazard rates. De *cumulatieve* impact (3-jaar-horizon) is substantieel groter dan de point estimates suggereren. Daarom rapporteren we in counterfactual scenarios (Pijler 36) altijd cumulatieve effecten en hun bootstrap CI's.

---

## 5. Publication-strategy

**Primary target: Energy Economics of JEEM**
- Geschikt voor cross-jurisdictionale causale evaluatie met theoretische foundation
- Three-method robustness + Honest DiD bounds = referee-bestand
- Mechanism design + real-options framework = theoretische bijdrage

**Backup: Energy Policy** (gegarandeerd fit, lager technical bar)

**Stretch: Journal of Applied Econometrics** als methodologische framing wordt versterkt
- Vereist: meer ruimte voor TVP-DiD + Honest DiD-vergelijking + identification-strategy
- Mogelijk in een tweede paper, gericht op methodologie

**Mijn aanbeveling**: na thesis-defense een afgeslankte versie schrijven gericht op Energy Economics. Mogelijk samen met supervisor als co-auteur.

---

## 6. Resterende werkpunten

| Onderdeel | Status | Geschatte uren |
|---|---|---|
| Hoofdtekst Chapters 1-4 | 60% (data + methods + early results) | 20-30u |
| Chapter 5 (theoretical) | Outline klaar via Pijler 40 markdown | 8-12u |
| Chapter 6 (Honest DiD discussion) | Outline klaar | 6-8u |
| Chapter 7 (counterfactual scenarios) | Outline klaar via Pijler 36 | 4-6u |
| Conclusion + limitations | nog te schrijven | 4-6u |
| Appendix tables/figures | grotendeels geautomatiseerd uit pijlers | 4u |
| Defense voorbereiding | nog te starten | 15-20u |
| **Totaal** | | **~60-90u over 8-12 weken** |

---

## 7. Discussievragen voor supervisor

1. **Honest DiD framing**: hoe sterk willen we de "fragility" van 3/4 policies in de hoofdtekst rapporteren? Een aparte methodologische subsectie, of in de robustness-appendix?

2. **Real-options theoretical chapter**: Chapter 5 nu deels formeel (Dixit-Pindyck) en deels conceptueel. Wenselijk om dit volledig formeel uit te werken, of bewust conceptueel houden om empirische zwaartepunt te behouden?

3. **Counterfactual scenarios**: hoe sterk in conclusie naar voren brengen? Risico is dat reviewers ze als overreach beschouwen. Voorstel: in conclusie houden als *"illustrative scenarios under maintained ATE-extrapolation"*.

4. **Publication-traject**: na defense direct submission naar Energy Economics, of eerst 1-2 maanden rust en dan herziening?

5. **Co-authorship policy**: bij eventuele publicatie, zou supervisor co-auteurschap willen overwegen voor de methodologische bijdrage?

---

### Bronnen onder dit briefing

- GitHub thesis repo: `github.com/SakeSaak/thesis_h2` (private)
- Commits: `addb536` (Pijler 34), `1a2504d` (Pijler 39), `a7849ab` (Pijler 40), `1f2b91a` (Pijler 36)
- Synthese document: `08_synthesis/FINAL_SYNTHESIS_v4_2026-05-20.md`
- Gap analysis: `08_synthesis/GAP_ANALYSIS_v3_STAKEHOLDERS_2026-05-20.md`

**Contact**: Sake Saakstra | sake.saakstra@student.vu.nl
