# Concept email naar dr. N. Ketel — versie 3 (waterdicht — Plan G complete)

**Onderwerp:** Concept hoofdstuk causale identificatie via CBAM — verzoek om gerichte feedback

**Aan:** n.ketel@vu.nl

**CC:** s.j.koopman@vu.nl

**Bijlagen:**
- `chapter8_cbam_full.pdf` (30 pp, ~10k woorden) — concept Chapter 8 (volledige CBAM-analyse + complete robustness-suite)
- `chapter7_v2.pdf` (13 pp) — concept Chapter 7 (hazard model + TVP state-space + model-validation-diagnostics)
- `chapter8_cbam_design.tex` → optioneel: oorspronkelijk research design memo (2.5k woorden)

---

Beste Nadine,

Bedankt nogmaals voor je bereidheid om mee te denken over mijn MSc-scriptie. Bij dezen zoals afgesproken het concept van het hoofdstuk waar ik je gerichte feedback over zou willen vragen. Het bouwt voort op de eerdere associationele bevindingen uit mijn scriptie (Blue × EUA interactie $\beta_{\text{int}}$ in het bereik $[-1.17, -1.88]$ over diverse specificaties), en exploiteert de CBAM definitieve fase-launch van 1 januari 2026 als sudden-shock voor causale identificatie. Het werk is begeleid door Siem Jan Koopman; ik zou hem graag CC houden in deze correspondentie.

**Wat het hoofdstuk doet.** Vier pre-registered identification strategies op drie onafhankelijke data sources:

- v7 sample (714 projecten, 43 cancellation events, manueel gecureerd uit eerdere S&P versie)
- **S&P Global Hydrogen Master Data Table** (3.343 projecten, dagelijks ververst, definitie B = 206 events na transparante exclusion van 84% On-hold-assumed) — primaire bron voor causale DiD
- IEA Hydrogen Production Projects Database (2.625 projecten, jaarlijks, multi-checkbox end-use) — cross-validation

De vier strategies zijn (i) equity event study DiD met placebo-correctie, (ii) project-level vintage cohort DiD, (iii) EU-gerestricteerde placebo-rich DiD met vijf placebo treatment dates, en (iv) triple-difference EU × CBAM-end × Post. Alle vier geven informative nulls. Het centrale resultaat: een robust associationaal patroon (+17pp tot +20pp hogere cancellation in EU-CBAM-exposed projecten, gerepliceerd in zowel S&P als IEA), maar **een formele event-study pre-trends test wijst uit dat dit patroon al pre-CBAM bestaat** ($\hat\beta_{t=-3} = +0.82$, $p < 0.001$; joint $F(6, 152) = 20.18$, $p < 0.0001$). De associatie is dus geen CBAM-causaal effect maar een pre-existing regularity.

**Robustness suite — negen onafhankelijke pijlers.** Op aandringen van de zelfevaluatie tegen top-tier MSc/PhD standaarden heb ik een complete robustness-suite opgebouwd, nu volledig geïntegreerd in Sectie 10.5 van Chapter 8:

1. **Honest DiD bounds (Rambachan-Roth 2023).** Op de focal ATT van het EU event-study (LPM, event-time $\hat\gamma_0 = +0.42$, naive 95\% CI $[-0.12, +0.95]$): de **breakdown $\bar{M} = 0.00$**. Zelfs onder strikte parallel trends bevat de Honest CI nul. Dit is mathematisch wat de placebo-rich grid alleen suggereerde.

2. **Wild Cluster Bootstrap (Cameron-Gelbach-Miller 2008; Roodman-MacKinnon-Nielsen-Webb 2019).** Met $G=17$ vintage-cohort clusters: asymp $p=0.04 \to$ WCB-T (Rademacher) $p=0.12$ (year-cluster) of $p=0.52$ (sponsor-cluster, $G=26$).

3. **Fisher randomization inference.** Cluster-level permutation (vintage cohort = treatment-assignment unit): EU 2x2 DiD $p_{\text{perm}} = 0.24$; triple-difference $p_{\text{perm}} = 0.09$.

4. **Bayesian DiD met moderne Vehtari et al (2021) diagnostiek.** Posterior $\hat\beta_{\text{cbam}\times \text{post}} = +1.56$, 95\% HDI $[-0.08, +3.27]$. $P(\beta > 0 \mid \text{data}) = 96.9\%$. Bulk-ESS $\in [2416, 3367]$, $\hat{R} \in [1.000, 1.000]$, PPC $p = 0.49$. Alle Vehtari criteria gepasseerd.

5. **Roth-Sant'Anna (2022) functional-form sensitivity.** LPM/logit/probit AMEs allemaal binnen $[+0.30, +0.35]$pp. Sign-agreement over alle 3 specs; 2/3 marginally significant.

6. **Outlier influence (Cook's D + DFBETA).** Top-5 removal: EU 2x2 DiD coefficient WORDT STERKER ($+0.346 \to +0.514$, $p: 0.04 \to 0.004$); triple-diff wordt MEER null ($+0.195 \to +0.051$). Pattern is dus niet outlier-driven.

7. **Event-study pre-trends test (nieuw).** Leads $t=-7$ t/m $t=-2$ vs baseline $t=-1$: joint $F(6, 152) = 20.18$, $p < 0.0001$. Pre-trends decisief geviolated, gedreven door 2019 ($\hat\beta_{-3} = +0.82$, $p < 0.001$). Dit is mogelijk de **directste** bevestiging dat de EU pattern *niet* CBAM-causaal is.

8. **Monte Carlo power analysis (nieuw).** 10.000 simulaties: power voor true effect $=15$pp is slechts $14\%$; bij $30$pp ook nog maar $38\%$. **MDE bij 80% power is $> 50$pp.** Dit corrigeert mijn eerdere analytische schatting van $\sim 11$pp die te optimistisch was — de werkelijke situatie is dat onze null-vindingen statistisch *moeten* zijn, niet kunnen niet anders.

9. **Oster (2019) bounds voor omitted-variable bias (nieuw).** Adding controls *vergroot* de coefficient (EU 2x2: $+0.287 \to +0.346$, $+21\%$). Standard OVB-zorg (dat unobservables je effect oversturen) gaat dus de verkeerde kant op. Voor de triple-difference $\delta = +2.08$ bij $R^2_{\max} = 1$: zou maximale en in tegenovergestelde richting werkende unobservables nodig hebben.

Plus in Chapter 7 een nieuwe **Model Validation Diagnostics sectie** met Hosmer-Lemeshow ($\chi^2 = 7.79$, $p = 0.454$), AUC = 0.805, calibration slope = 0.891, Cox PH cross-check (HR 6.23 vs logit HR 7.81), Schoenfeld residuals (alle covariaten OK behalve **`year_centered` $p = 0.0006$ — PH formeel violated voor tijd**, wat de TVP-specificaties M2/M3 mathematisch motiveert), GLMM frailty (sponsor ICC $\approx 0$), 5-fold OOS CV (mean AUC 0.76 vs in-sample 0.80, ratio 0.95), en outlier-influence (sign en significantie behouden).

**Wat ik specifiek aan jou wil voorleggen.** Vijf concrete punten:

1. **Treatment definitie keuze.** Ik gebruik drie geneste exposure definities (T1 narrow end-use, T2 broad geographic-OR-end-use, T3 strict intersection). T3 levert de cleanste cross-sectional identification op maar trekt het sample te smal voor robust DiD. Is mijn argumentatie hierover (Sectie 3.1) defendable? Zou je een alternative definitie aanbevelen?

2. **De EU-only placebo-rich design (Sectie 7) plus formal pre-trends violation.** De event-study leads/lags F-test ($p < 0.0001$) lijkt mij nu de directste, sterkste empirische bevestiging van het informative-null verhaal — sterker dan placebo-ratio of Honest DiD bound alleen. Vind je deze samenstelling van inferentie + identificatie checks (negen pijlers) overtuigend, of zie je nog gaten?

3. **Monte Carlo power correctie.** Mijn eerdere analytische MDE-schatting van $\sim 11$pp was te optimistisch; de Monte Carlo wijst uit dat de werkelijke MDE bij 80% power $> 50$pp is. Dit verandert het verhaal niet — onze nulls worden er sterker door (we hadden simpelweg geen power om effecten <30pp te detecteren) — maar het is wel een belangrijke correctie. Vraagt dit nog een additionele verklaring in de discussion, of acht je het voldoende gerapporteerd?

4. **Framing in jouw 2023 (un)importance-paper traditie.** Sectie 11.3 framt de bijdrage als het *bounden* en *transparant rapporteren* van waarom we niet kunnen identificeren. Negen onafhankelijke robustness pijlers, alle wijzend op dezelfde conclusie. Vind je dit een passende framing, of zou je een ander argument zien?

5. **Schoenfeld year-coefficient violatie als TVP-motivatie (Chapter 7).** De PH-violation op `year_centered` ($p = 0.0006$) plus de rolling-window OOS CV collapse op 2020--2021 (AUC = 0.33) motiveren formeel onze TVP state-space specificatie in Chapter 6. Dit was eerder alleen theoretical motivation; we hebben nu twee onafhankelijke formele tests. Vind je dit een goede manier om de overgang van M1 (static) naar M2/M3 (TVP) econometrisch te onderbouwen?

Daarnaast horen we graag van je of er een tweede-lezer rol voor je in zou kunnen zitten — dit is voor de hoofdscriptie 18 EC.

**Praktisch.** Beide hoofdstukken zijn als PDF bijgevoegd. De LaTeX source en alle achterliggende empirische scripts zijn beschikbaar in een GitHub repository met volledige reproducibility documentation (README, data dictionary, makefile, requirements.txt) — kan ik op verzoek delen. Ik kan ook voorstellen om in week 21 of 22 een afspraak van 30-45 min te plannen waarin we het kunnen doorlopen, mocht dat handiger zijn dan schriftelijke feedback.

Hartelijk dank alvast voor je tijd.

Met vriendelijke groet,

Sake Saakstra
MSc Econometrics & Operations Research (Financial Track)
Vrije Universiteit Amsterdam
06-XX-XXX-XXXX
sake.saakstra@student.vu.nl
