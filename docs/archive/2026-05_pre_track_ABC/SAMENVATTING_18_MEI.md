# Thesis stand van zaken — 18 mei 2026

**Sake Saakstra | MSc EOR Financial Track VU Amsterdam | Reviewer: the external reviewer**

---

## 1. Wat we hebben gedaan

Vier maanden bouwen aan thesis-fundament, met als hoofddoel: van een toegepaste case-study naar een PhD-georiënteerd methodologisch werkstuk. Het werk valt in vijf "sporen" + één methodologische hoofdbijdrage.

### Spoor 1: Bayesiaanse methodologie (Cox PH)
Static Bayesian Cox proportional-hazards model op v7 sample (714 projecten, 43 cancellation events). Vier prior-sensitivity grids: vague, weakly informative, skeptical, en informative_v7. Bayesian schattingen systematisch lager dan frequentist (HR 4-6 vs 11.9), omdat priors regularizeren tegen perfect-separation in MLE.

**Output:** `06_thesis_extensions/01_bayesian_methodology/` met 9-pagina design document + PyMC implementatie. Stan/cmdstanr installatie faalde op macOS 26.5 vanwege Apple Silicon header issues; gepivot naar PyMC.

### Spoor 2: Nederlandse beleidsfocus
15-pagina chapter outline voor Hoofdstuk 9 (Dutch Policy Context). Vijf secties: EU-beleid (ETS1/ETS2/CBAM), Nederlandse overlays (CO2-heffing, SDE++, HyNetwork Nederland), PBL beprijzingstekort-framework, mapping naar paper findings, en forward-looking vragen.

**Output:** `06_thesis_extensions/02_nl_policy_chapter/` met outline + open vragen.

### Spoor 3: Publieke-data robustness
98 H2-CCUS projecten uit publieke IEA CCUS database (CC BY 4.0 licensie). Drie Cox PH modellen: brede CCUS (HR=2.02, p=0.014, **significant**), industriële CCUS (HR=1.63, p=0.15), en within-H2. Inclusief 10 post-maart-2024 cancellations (BP H2Teesside, HyDEMO, Hydrogen 2 Magnum, H2M Eemshaven) — directe Gasunie-relevantie.

**Output:** `06_thesis_extensions/03_public_data_robustness/` — fungeert als hedge tegen S&P data-licensing risico.

### Spoor 4: Carbon-conditional replicatie
Frequentist replicatie v7 paper: Blue×EUA interactie coefficient = -2.28 (paper rapporteert -2.51); HR bij z=+1 exact 4.67 (perfect match met paper). Bayesiaanse sensitivity grid met informative prior op v7 estimate: alle vier priors geven negatieve β_int met 95% CrI exclusief 0.

**Output:** `06_thesis_extensions/04_carbon_conditional/`

### Methodologische hoofdbijdrage (Spoor 5): Time-varying carbon-conditional hazard
Drie nested specificaties getest op een year-by-technology aggregate (17 jaar × 2 technologieën = 34 Binomial observaties):

1. **Static**: β_int constant
2. **Parameter-driven TVP**: β_int volgt Gaussian random walk over economische regimes (3, 4, of 5 blocks)
3. **Observation-driven TVP (GAS)**: β_int(t+1) = ω(1-φ) + φ·β_int(t) + α·s_t volgens Creal-Koopman-Lucas 2008, met scaling d ∈ {0, ½, 1}

Bayesiaanse inferentie via Hamiltonian Monte Carlo (PyMC), 7 model varianten gefit, LOO/WAIC formal comparison.

**Output:** `06_thesis_extensions/05_state_space_tvp/` met 5 Python scripts, resultaatfolders, en complete LaTeX Chapter 7 draft in `07_thesis_drafts/chapter7/chapter7.tex` (336 regels, 4192 woorden, alle 7 secties uitgewerkt).

---

## 2. Wat de bevindingen zijn

### A. Structureel robuust effect (alle drie specificaties)
β_int is consistent negatief over alle modellen:

| Specificatie | β_int schatting | 95% CrI |
|---|---|---|
| Static (aggregaat) | -1.37 | [-2.20, -0.49] |
| GAS long-run mean (ω) | -1.61 | [-2.50, -0.69] |
| 4-block: drie blocks | -1.50 / -1.73 / -2.06 | alle CrI exclusief 0 |

De carbon-conditional cancellation mechanisme is robuust: een 1-SD daling in EUA-prijs vergroot de Blue/PEM hazard ratio ongeveer **factor exp(1.5) ≈ 4.5×**.

### B. Block 2 (2023-2024) wijde CrI is een identificatie-artefact
Robuust over alle block specificaties (3, 4, 5):

| Spec | Block 2023-2024 | Vergelijking met andere blocks |
|---|---|---|
| 3-block | -0.57 [-1.70, +0.50] (bevat 0) | Andere blocks -1.60 / -2.00 |
| 4-block | -0.70 [-1.90, +0.41] (bevat 0) | Andere blocks rond -1.5 tot -2.1 |
| 5-block | -0.73 [-1.80, +0.39] (bevat 0) | Andere blocks variërend |

**Maar:** ruwe data in deze periode bevestigt theorie. Toen EUA daalde van €82.60 (2023) naar €65.34 (2024), steeg implied HR Blue/PEM van 1.87 naar 4.70 — precies wat de carbon-conditional theorie voorspelt. Direct estimate uit deze 2-jaar shift geeft β_int ≈ -1.28, in lijn met static en GAS schattingen.

De wijdere CrI in block-modellen is een **gevolg van slechts 2 tijdspunten in het block + Gaussian random walk prior die alleen lichte smoothing tussen blocks doet**. GAS lost dit op via structured persistence (φ = 0.78): in elk jaar borrowt de trajectorie strength van eerdere jaren.

### C. GAS observation-driven specificatie vindt geen tijdsvariatie
α_gas = 0.045 [0.003, 0.13] — bijna nul. De drie scaling-varianten (d=0, ½, 1) geven identieke posterior trajectories. Dit is een **direct test** dat de data geen continue tijdsvariatie ondersteunt; de scaling parameter wordt irrelevant wanneer score-driven updating verwaarloosbaar is. GAS reduceert effectief tot AR(1) richting ω = -1.61.

### D. Formele LOO/WAIC comparison

| Rank | Model | elpd_loo | Δ vs best | dse |
|---|---|---|---|---|
| 1 | 5-block | -31.74 ± 8.34 | 0 | 0 |
| 2 | 3-block | -32.13 ± 8.52 | 0.39 | 0.90 |
| 3 | 4-block | -32.75 ± 8.81 | 1.01 | 0.82 |
| 4 | Static | -37.06 ± 9.97 | **5.32** | 2.80 |
| 5-7 | GAS d=0/½/1 | -38.10 ± 10.55 | 6.36 | 4.20 |

- Block specificaties zijn equivalent onderling (binnen 1 elpd unit)
- Blocks geven matig voordeel boven static (~1.9 SE)
- GAS presteert iets slechter dan static
- **Alle comparisons hebben warning: True** (Pareto k > 0.7) — met 17 observaties is LOO maar matig betrouwbaar

### E. Conclusie van de drie lagen
De carbon-conditional cancellation mechanisme is **structureel time-stable** rond β_int ≈ -1.5 over 2010-2026. Block specificaties suggereren licht tijdsvariatie maar formele model comparison geeft niet decisief bewijs. GAS biedt sharper inference via persistence maar wordt door LOO niet beloond vanwege extra parameters. **De combinatie van bevindingen verdient een eerlijke "stable mechanism" interpretatie eerder dan regime-change-claims.**

---

## 3. Wat we nog moeten onderzoeken

### Op korte termijn (volgende 2 weken)

**1. Koopman supervisor-meeting voorbereiden** (week 21-22)
- Mail met PDF van Chapter 7 draft + bondige update
- Concrete vraag: 30 min in week 22-23 om methodologische opzet vast te leggen
- Drafted mail-tekst staat in eerdere sessie-output

**2. 27 mei meeting Gasunie**
- S&P attributie definitief vastleggen (Commodity Insights vs Platts vs Energy Transition Tracker)
- Externe publicatieprocedure
- Mate van Gasunie support voor PhD-ambitie

**3. Chapter 7 fine-tuning**
- Lees `chapter7.tex` grondig — eindredactie van jouw kant op secties 7.1 (Introduction) en 7.6 (Discussion)
- Compileer naar PDF: `pdflatex chapter7.tex` twee keer (voor bibliography)
- Markeer waar je eigen stem niet wordt weergegeven
- Open punten: hoe diep wil je het PBL beprijzingstekort framework integreren?

### Op middellange termijn (juni-juli)

**4. Robustness uitbreidingen voor Chapter 7**
- Non-centered parameterisatie voor block model (lost 8 divergences op)
- 4 chains in plaats van 2 (huidige LOO recommendation)
- Pareto k diagnostic checken per model
- Sensitiviteit op prior keuze sigma_int (Half-Normal(0.3) vs HalfStudentT)
- Eventueel GAS met informative prior op α_gas ~ HalfNormal(0.5) om te zien of dat anders convergeert

**5. Chapter 1-2-3 schrijven**
- Chapter 1 (Introduction): research question, stylized facts, contribution claims
- Chapter 2 (Literature Review): drie strands — survival, TVP state-space, hydrogen+carbon pricing
- Chapter 3 (Theoretical Framework): real-options model voor blue vs green onder carbon-uncertainty

**6. Verdiepende econometrische literatuur lezen**
- Koopman (2000) JRSSB — methodologische anker
- Durbin-Koopman (2012) Hoofdstuk 9-11 — non-Gaussian state-space
- Creal-Koopman-Lucas (2008, 2013) — GAS framework
- Koopman-Lit-Lucas (2016) REStat — parameter-driven vs observation-driven
- Lancaster (1990) — duration models econometric foundations
- Van den Berg (2001) — duration in econometrics

### Op langere termijn (augustus-oktober)

**7. Chapters 8-10 schrijven**
- Chapter 8: Public CCUS Robustness (Spoor 3 al klaar als basis)
- Chapter 9: Dutch Policy Context (Spoor 2 outline klaar)
- Chapter 10: Discussion + Conclusion

**8. Optionele methodologische verfijningen**
- Monthly-frequency GAS (wanneer voldoende observatievenster geaccumuleerd)
- Hierarchical TVP across regions of sectoren
- Multi-event TVP (verschillende cancellation oorzaken apart modelleren)
- Semi-parametric TVP (Bayesian splines voor β_int(t))

**9. PhD-pad strategie**
- Na verdediging: refactor Chapter 7 tot standalone working paper
- Submit naar Journal of Applied Econometrics (Koopman editorial connection) of Econometrics Journal
- Op basis van paper-feedback: PhD proposal schrijven met Bos + Koopman als beoogd supervisors
- Apply ENTER PhD positie of NWO PhD grant

### Open methodologische vragen (voor Koopman-meeting)

1. **Identification limits in sparse data:** Met slechts 17 jaarlijkse observaties is LOO maar matig betrouwbaar. Wat zijn de juiste discriminatiecriteria tussen specificaties in deze setting?

2. **GAS vs parameter-driven trade-off:** Wanneer de data geen observation-driven dynamiek ondersteunt (α_gas ≈ 0), is GAS dan nog steeds methodologisch waardevol als specification, of moet de keuze tussen parameter-driven en observation-driven anders worden gemotiveerd?

3. **Non-centered parameterisatie voor block models:** Welke priors op sigma en delta zijn aangewezen voor random walks over economische blocks bij sparse event data?

4. **Aggregatie keuze:** Year × technology aggregaat verliest individuele covariates (year_since_start, log_capacity). Hoe rechtvaardigen we deze keuze versus volledige individual-level analysis?

5. **Block boundary motivatie:** Zijn onze 4 economische regimes (pre-crisis, pandemic+early, peak, normalisation) wetenschappelijk verantwoord, of is een data-driven changepoint detection eleganter?

---

## 4. Concrete prioriteiten deze week

**Vandaag/morgen:**
- Lees `chapter7.tex` — eindredactie
- Bekijk `gas_vs_blocks.pdf` en `gas_scaling_robustness.pdf` figuren
- Lees deze samenvatting nog eens met heldere ogen

**Vóór 27 mei:**
- Compileer chapter7.tex naar PDF
- S&P attributie research voor Gasunie meeting

**Week 21-22 (24-30 mei):**
- Mail Koopman met Chapter 7 draft als bijlage
- Begin Chapter 1-2 outline
- Start Koopman 2000 JRSSB paper lezen

**Goede 27 mei meeting.**
