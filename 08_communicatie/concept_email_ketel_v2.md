# Concept email naar dr. N. Ketel — versie 2 (bijgewerkt met advanced robustness)

**Onderwerp:** Concept hoofdstuk causale identificatie via CBAM — verzoek om gerichte feedback

**Aan:** n.ketel@vu.nl

**CC:** s.j.koopman@vu.nl

**Bijlagen:**
- `chapter8_cbam_full.pdf` (27 pp, 9.2k woorden) — concept Chapter 8 (volledige CBAM analyse + advanced robustness suite)
- `chapter7_v2.pdf` (12 pp) — concept Chapter 7 (hazard model + TVP state-space + model validation diagnostics)
- `chapter8_cbam_design.tex` → optioneel: oorspronkelijk research design memo (2.5k woorden)

---

Beste Nadine,

Bedankt nogmaals voor je bereidheid om mee te denken over mijn MSc-scriptie. Bij dezen zoals afgesproken het concept van het hoofdstuk waar ik je gerichte feedback over zou willen vragen. Het bouwt voort op de eerdere associationale bevindingen uit mijn scriptie (Blue × EUA interactie $\beta_{\text{int}}$ in het bereik $[-1.17, -1.88]$ over diverse specificaties), en exploiteert de CBAM definitieve fase-launch van 1 januari 2026 als sudden-shock voor causale identificatie. Het werk is begeleid door Siem Jan Koopman; ik zou hem graag CC houden in deze correspondentie.

**Wat het hoofdstuk doet.** Vier pre-registered identification strategies op drie onafhankelijke data sources:

- v7 sample (714 projecten, 43 cancellation events, manueel gecureerd uit eerdere S&P versie)
- S&P Global Hydrogen Master Data Table (3.343 projecten, dagelijks ververst, definitie B = 206 events na transparante exclusion van 84% On-hold-assumed)
- IEA Hydrogen Production Projects Database (2.625 projecten, jaarlijks, multi-checkbox end-use)

De vier strategies zijn (i) equity event study DiD met placebo-correctie, (ii) project-level vintage cohort DiD, (iii) EU-gerestricteerde placebo-rich DiD met vijf placebo treatment dates, en (iv) triple-difference EU × CBAM-end × Post. Alle vier geven informative nulls. Het centrale resultaat: een robust associationaal patroon (+17pp tot +20pp hogere cancellation in EU-CBAM-exposed projecten, gerepliceerd in zowel S&P als IEA), maar placebo-dates binnen de EU produceren coefficient estimates van gelijke of grotere magnitude dan de echte CBAM-dates (ratio 0.72), en de triple-difference levert $\beta_7 = +1.15$ met 95% CrI $[-1.48, +3.78]$.

**Methodologische uitbreidingen sinds vorige correspondentie.** Op aandringen van de zelfevaluatie tegen top-tier MSc/PhD standaarden heb ik vier additionele robustness lagen toegevoegd, allemaal nu in Sectie 10.5 van Chapter 8:

1. **Honest DiD bounds (Rambachan-Roth 2023).** Op de focal ATT van het EU event-study (LPM, event-time $\hat\gamma_0 = +0.42$, naive 95\% CI $[-0.12, +0.95]$): de **breakdown $\bar{M} = 0.00$**. Dat wil zeggen: zelfs onder de strikste relaxatie van parallel trends ($\bar{M} = 0$, geen post-period violations) bevat de Honest CI nul. Dit geeft mathematisch wat onze placebo-rich grid alleen suggereerde: het EU patroon is formeel niet causaal identificeerbaar. Dit raakt naar mijn idee direct jouw eigen werk.

2. **Wild Cluster Bootstrap (Cameron-Gelbach-Miller 2008; Roodman-MacKinnon-Nielsen-Webb 2019).** Met $G=17$ vintage-cohort clusters is asymptotic cluster-robust inference suspect. Onder WCB-T met Rademacher weights ($B=999$): de EU 2x2 DiD asymptotic $p=0.04$ wordt WCB $p=0.12$ (year-cluster) of zelfs $p=0.52$ (sponsor-cluster, $G=26$). De triple-difference null blijft een null onder alle WCB specificaties.

3. **Fisher randomization inference.** Cluster-level permutation (vintage cohort = treatment-assignment unit): EU 2x2 DiD $p_{\text{perm}} = 0.24$. Triple-difference $p_{\text{perm}} = 0.09$ (unit-level) — beide null onder de naar onze mening juiste cluster-level inference.

4. **Bayesian DiD met moderne Vehtari et al (2021) diagnostiek.** Posterior $\hat\beta_{\text{cbam}\times \text{post}} = +1.56$, 95\% HDI $[-0.08, +3.27]$. $P(\beta > 0 \mid \text{data}) = 96.9\%$ — sterke maar niet conclusieve evidence. Bulk-ESS $[2416, 3367]$, Tail-ESS $[2069, 3145]$, $\hat{R} \in [1.000, 1.000]$, PPC $p = 0.49$. Alle modernste convergence criteria gepasseerd.

Plus in Chapter 7 een nieuwe **Model Validation Diagnostics sectie** met Hosmer-Lemeshow ($\chi^2 = 7.79$, $p = 0.454$), AUC = 0.805, calibration slope = 0.891, Cox PH cross-check (HR 6.23 vs logit HR 7.81), Schoenfeld residuals (alle covariaten OK behalve **`year_centered` $p = 0.0006$ — PH formeel violated voor tijd**, wat de TVP-specificaties M2/M3 nu mathematisch motiveert), GLMM frailty (sponsor ICC $\approx 0$), en out-of-sample 5-fold CV (mean AUC 0.76 vs in-sample 0.80, ratio 0.95). Tot slot Roth-Sant'Anna functional-form sensitivity (LPM/logit/probit AMEs allemaal binnen $[+0.30, +0.35]$) in Chapter 8 Sectie 10.5.5.

**Wat ik specifiek aan jou wil voorleggen.** Vier concrete punten waar ik je oordeel het meest waardevol zou vinden:

1. **Treatment definitie keuze.** Ik gebruik drie geneste exposure definities (T1 narrow end-use, T2 broad geographic-OR-end-use, T3 strict intersection). T3 levert de cleanste cross-sectional identification op maar trekt het sample te smal voor robust DiD. Is mijn argumentatie hierover (Sectie 3.1) defendable? Zou je een alternative definitie aanbevelen?

2. **De EU-only placebo-rich design (Sectie 7) plus Honest DiD bounds.** Ik volg hier expliciet het sudden-shock framework van jou, Hanemaaijer en Marie (2024). De Rambachan-Roth breakdown $\bar{M} = 0$ kwantificeert nu mathematisch wat de placebo ratio 0.72 alleen suggereerde. Vind je deze combinatie (informele placebo grid + formele Honest DiD bounds) overtuigend als falsification, of zou je nog een aanvullende strategie aanraden?

3. **Power constraint en synthetic controls.** Met 60 EU CBAM-exposed cancelled-projecten en MDE van $\sim 11$pp bij 80\% power, kan ik effecten $<11$pp niet detecteren. Vier maanden post-definitive launch is een fundamentele beperking. Zou je een synthetic-controls aanpak (à la Abadie-Diamond-Hainmueller) aanbevelen voor een eventuele uitbreiding (eventueel post-thesis), of acht je het methodologisch sterker om de informative null te accepteren gezien de formele Honest DiD bounds?

4. **Framing in jouw 2023 (un)importance-paper traditie.** Ik framing het hoofdstuk expliciet in de honest-null methodologie van jullie IZA 16591. Sectie 11.3 stelt dat de bijdrage ligt in het *bounden* van een eventueel causaal effect (Honest DiD: $0$ in CI onder strict PT) en het transparant rapporteren waarom we het niet kunnen identificeren. Vier onafhankelijke inference methods komen tot hetzelfde verhaal (asymp, WCB, permutation, Bayesian). Vind je dit een passende framing, of zou je hier een ander argument zien?

Een vijfde punt zou kunnen zijn (optioneel): de Schoenfeld PH-violation op `year_centered` ($p = 0.0006$) in Chapter 7 motiveert formeel onze TVP state-space specificatie in Chapter 6. Dit was eerder alleen theoretical motivation; we hebben nu een formele test. Vind je dit een goede manier om de overgang van M1 (static) naar M2/M3 (TVP) econometrisch te onderbouwen?

Daarnaast horen we graag van je of er een tweede-lezer rol voor je in zou kunnen zitten — dit is voor de hoofdscriptie 18 EC. Als die rol niet past, ben ik ook al heel dankbaar voor jouw inhoudelijke commentaar op dit ene hoofdstuk.

**Praktisch.** Beide hoofdstukken zijn als PDF bijgevoegd (Chapter 7 12 pp, Chapter 8 27 pp). De LaTeX source en alle achterliggende empirische scripts zijn beschikbaar in een public GitHub repository met volledige reproducibility documentation (README, data dictionary, makefile, requirements.txt) — kan ik op verzoek delen. Ik kan ook voorstellen om in week 21 of 22 een afspraak van 30-45 min te plannen waarin we het kunnen doorlopen, mocht dat handiger zijn dan schriftelijke feedback.

Hartelijk dank alvast voor je tijd.

Met vriendelijke groet,

Sake Saakstra
MSc Econometrics & Operations Research (Financial Track)
Vrije Universiteit Amsterdam
06-XX-XXX-XXXX
sake.saakstra@student.vu.nl
