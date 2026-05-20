# MSc Thesis Master Plan — Koopman supervised
## "Time-Varying Hazard Intensity for Hydrogen Project Cancellation: A State-Space Approach"

**Author:** Sake Saakstra  
**Supervisor:** Siem Jan Koopman (VU Amsterdam, Department of Econometrics)  
**Target:** MSc EOR Financial Track thesis (18 EC), grade target 8.5+, PhD-aspirational  
**Defense window:** September-November 2026

---

## 1. METHODOLOGISCHE KERNBIJDRAGE

The thesis bridges **survival analysis** with **time-varying parameter (TVP) state-space econometrics** (Koopman 2000, 2016) applied to **hydrogen project cancellation events** in the energy transition.

The novel methodological contribution:

> A non-Gaussian state-space hazard model in which the carbon-conditional interaction coefficient β_int(t) follows a stochastic process, jointly estimated with sparse event data using Bayesian inference.

This sits at the intersection of three literatures:
1. **Survival/duration models** in econometrics (Lancaster 1990, Heckman-Singer 1984)
2. **State-space methods with non-Gaussian observations** (Durbin-Koopman 2012, Koopman 2000)
3. **Energy transition empirics** (Bolton-Kacperczyk, Odenweller, IEA reports)

**Publishable potential:** Journal of Applied Econometrics (Koopman editorial connection) or Energy Economics (substantive). The methodological chapter could be a standalone working paper.

---

## 2. WAT WE AL HEBBEN (basisfundament)

| Spoor | Folder | Wat | Klaar voor schrijven? |
|---|---|---|---|
| 1: Bayesian methodologie | `01_bayesian_methodology/` | 9-pag design doc + 4-prior sensitivity grid op static Cox PH | ✅ |
| 2: NL policy chapter | `02_nl_policy_chapter/` | 15-pag outline + 5 secties + 5 open Q's voor Bos | Outline klaar |
| 3: Public CCUS robustness | `03_public_data_robustness/` | 98 H2-CCUS projecten + 3 Cox PH modellen | ✅ |
| 4: Carbon-conditional | `04_carbon_conditional/` | Frequentist v7 replicatie (HR=4.67 exact match) + Bayesian 4-prior grid | ✅ |
| 5: TVP state-space | `05_state_space_tvp/` | **Pilot in progress** — random walk op β_int(t) | Pending |

---

## 3. CHAPTER STRUCTURE — 16 WEKEN

### Chapter 1: Introduction (Week 1)
- Research question: "Is the carbon-conditional cancellation risk of blue hydrogen projects stable over time, or does it evolve as the carbon market matures?"
- Stylized facts: 80% van events in 2023-2024, EUA prijsstructuur 2010-2026
- Contribution claims (methodologisch + empirisch + beleidsmatig)

### Chapter 2: Literature Review (Week 2-3)
Drie strands gesynthetiseerd:
1. **Survival in econometrics** (Lancaster 1990, Van den Berg 2001, Bonhomme-Jolivet 2009)
2. **TVP state-space** (Durbin-Koopman 2012, Koopman 2000 JRSSB, 2016 REStat, Creal-Koopman-Lucas 2008)
3. **Hydrogen + carbon pricing** (Odenweller 2022, Bolton-Kacperczyk 2021, Pindyck 1991 real options)

### Chapter 3: Theoretical Framework (Week 4)
- **Real options model** voor blue vs green technology choice under carbon-price uncertainty
- Genereert testbare predictie: hazard ratio Blue/Green dependent on (μ_EUA, σ_EUA)
- Connects econometric specification to economic mechanism

### Chapter 4: Data (Week 5)
- v7 sample (S&P Global): 244 Blue_CCS + 470 PEM = 714 projecten
- Public IEA CCUS (98 H2 projecten)
- Macro panel: EUA, TTF, VIX, EPU (master_panel_monthly)
- Event coding rationale + censoring scheme

### Chapter 5: Static Hazard Baseline (Week 6) — schrijf-werk
- Cox PH model (frequentist) op v7 sample
- Discrete-time hazard GLM (logit) met cluster SE  
- Carbon-conditional interaction (replicate v7)
- **Geleverd door bestaande Spoor 4 frequentist**

### Chapter 6: Static Bayesian Analysis (Week 7) — schrijf-werk
- Bayesian Cox PH met 4-prior sensitivity grid
- Carbon-conditional Bayesian met informative_v7 prior
- Discussion of identification + prior elicitation
- **Geleverd door bestaande Sporen 1 + 4 Bayesian**

### Chapter 7: METHODOLOGISCHE HOOFDBIJDRAGE — Time-Varying Hazard (Week 8-11)
- Non-Gaussian state-space framework (Koopman 2000)
- Parameter-driven specification: β(t) random walk
- Observation-driven (GAS) alternatief (Creal-Koopman-Lucas 2008)
- Importance sampling vs MCMC trade-offs
- Empirisch: posterior trajectory β_int(t) — toont structurele verschuiving 2022-2024
- Model comparison via LOO/WAIC

### Chapter 8: Public Data Robustness (Week 12) — schrijf-werk
- Drie modellen op publieke IEA CCUS data
- "When restricted to public data the qualitative findings hold"
- **Geleverd door bestaande Spoor 3**

### Chapter 9: Dutch Policy Context (Week 13-14) — schrijf-werk
- EU ETS framework (ETS1, ETS2, CBAM, free-allocation phase-out)
- Dutch overlays (CO2-heffing, SDE++, HyNetwork)
- PBL beprijzingstekort framework
- Mapping naar paper findings
- **Geleverd door bestaande Spoor 2 outline**

### Chapter 10: Discussion + Conclusion (Week 15-16)
- Methodologische implicaties voor TVP survival
- Empirische implicaties voor energy transition policy
- Limitations: sample size, identification, external validity
- Future research

---

## 4. DRIE KOOPMAN-TOUCHPOINTS GEDURENDE 16 WEKEN

| Week | Doel meeting | Wat te leveren |
|---|---|---|
| 4-5 | Theory + Data check-in | Chapter 3 draft + data summary |
| 9-10 | Methodologische review | Chapter 7 first draft (state-space specifcatie + initial results) |
| 13-14 | Pre-defense review | Volledige draft, alle chapters |

---

## 5. PHD-PAD STRATEGIE

Als de thesis goed gaat (8.5+), pad naar PhD:

**Stap 1 (na thesis verdediging):** Refactor Chapter 7 (methodologische hoofdbijdrage) tot standalone working paper.

**Stap 2:** Submit naar Journal of Applied Econometrics (Koopman editorial connection) of Econometrics Journal. 

**Stap 3:** Op basis van editor feedback + paper draft, schrijf PhD proposal met:
- Drie potentiele thesis chapters (TVP survival was chapter 1)
- Mogelijke extensions: multi-event TVP, hierarchical TVP across sectoren, semi-parametric TVP
- Bos + Koopman als beoogde supervisors (Bos voor de GAS-extensies, Koopman voor state-space)

**Stap 4:** Apply for ENTER PhD positie of NWO PhD grant.

---

## 6. RISICO'S + MITIGATIE

| Risico | Impact | Mitigatie |
|---|---|---|
| TVP model converteert niet door sparse events | Hoog — Chapter 7 staat of valt erbij | Switch naar time-blok TVP (4 blokken) of GAS-driven |
| S&P data licensing voor publication | Medium | Public CCUS robustness chapter werkt als hedge |
| Bos zegt nee → alleen Koopman als supervisor | Laag | Koopman heeft al ja gezegd |
| Tijd druk: 32u/week werk Gasunie | Hoog | Plan met buffers, deadlines per chapter, weekly check-ins |
| Methodologisch te complex voor MSc niveau | Laag | Static analyses (Ch 5-6) zijn al thesis-niveau; TVP is de extra bijdrage |

---

## 7. ONMIDDELLIJKE VERVOLGSTAPPEN

1. **Wacht TVP pilot output af** — als convergence OK is, schrijf Chapter 7 outline
2. **Read Koopman 2000 JRSSB paper** in detail — methodologische anker
3. **Read Durbin-Koopman 2012 book Hoofdstuk 9-11** — non-Gaussian state-space
4. **Lees Creal-Koopman-Lucas 2008** voor GAS framework
5. **Start Chapter 1 + 2 outline** — kan parallel met TVP debugging
6. **27 mei meeting Gasunie** — bevestig S&P data + thesis directie
