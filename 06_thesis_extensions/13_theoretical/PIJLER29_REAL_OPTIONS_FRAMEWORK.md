# Pijler 29: Real Options Framework voor Hydrogen Project Survival
## Theoretical Foundation voor PhD Chapter 5-6

**Auteur**: Sake Saakstra
**Datum**: 20 mei 2026
**Doel**: theoretische verklaring voor onze empirische findings (Blue dual-pathway failure + asymmetric decomm-hazard HR=0.235)

---

## 1. Motivatie

Onze empirische analyses leveren een puzzel die statische investment-finance theorieën niet kunnen verklaren:

| Pijler 16 finding | HR_Blue | Status |
|---|---|---|
| Cancel pre-FID | **2.30** (CI [1.20, 4.42]) | 2.3× hoger dan Green |
| On-hold (paused) | **2.57** (CI [1.88, 3.52]) | 2.6× hoger dan Green |
| **Decommission (post-operational)** | **0.235** (CI [0.09, 0.61]) | **76% LAGER dan Green** |

**Vraag**: hoe kan Blue tegelijkertijd MEER fragile zijn in pre-FID maar MINDER fragile post-operational?

**Antwoord**: real-options theory voorspelt dit exact via **asymmetric irreversibility**. Dit document ontwikkelt het formele framework.

---

## 2. Literatuur

### Foundational papers

**Pindyck (1991)**, "Irreversibility, Uncertainty, and Investment", *Journal of Economic Literature*:
- Investment decision is een **call option** op de onderliggende projecten-cashflow
- Sleutel: irreversibility creëert option-value-of-waiting
- Optimal threshold: investeer pas wanneer V_t > x* > I (waar x* > I door option value)

**Dixit & Pindyck (1994)**, "Investment Under Uncertainty" (textbook):
- Formaliseert sequential investment-decisions
- Multiple-stage exercise: scoping → planning → FID → construction → operations
- Each stage = mini-option op next stage

**Roberts & Weitzman (1981)**, "Funding Criteria for Research, Development, and Exploration Projects", *Econometrica*:
- Sequential R&D funding met informatie-arrival
- Optimal abandonment threshold daalt over project-lifecycle

**McDonald & Siegel (1986)**, "The Value of Waiting to Invest", *QJE*:
- Closed-form solution voor option value
- Hysteresis in investment-decisions

### Voor hydrogen specifically

**Mercure et al. (2018)**, "Macroeconomic impact of stranded fossil fuel assets", *Nature Climate Change*:
- Stranded asset risico → real-options framing voor low-carbon transition
- Carbon-price uncertainty → option value-of-waiting voor decarbonisation tech

**Bolton & Kacperczyk (2021)**, "Do investors care about carbon risk?", *Journal of Financial Economics*:
- Asset pricing under carbon-price uncertainty
- Real-options voor carbon-related investments

---

## 3. Formele model

### 3.1 Setup

**State variable**: Project's net present value $V_t$ volgt een Geometric Brownian Motion:
$$dV_t = \mu V_t \, dt + \sigma V_t \, dW_t$$

waar:
- $\mu$ = drift (verwachte groei van project value, e.g. EUA prijs stijging)
- $\sigma$ = volatility (carbon-price uncertainty, technology uncertainty)
- $dW_t$ = Wiener process

**Investment cost** $I$ is irreversible (sunk cost).

**Risk-free rate** $r > \mu$ (anders zou optimaal nooit investeren).

### 3.2 Drie sequentiële exercise-stadia voor hydrogen projecten

Onze data identificeert drie discrete beslismomenten:

**Stadium 1: Pre-FID announcement → cancel**
- Cost van cancel: lage informationele costs (papers, feasibility studies)
- Option: $\max\{V_t - I_{\text{FID}}, 0\}$ waar $I_{\text{FID}}$ = FID commitment cost
- Optimal cancel als $V_t < V_1^*$ waar $V_1^* < I_{\text{FID}}$

**Stadium 2: Post-FID, pre-operational → on-hold**
- Cost van pause: medium (delays, partial sunk costs)
- Option: $\max\{V_t - I_{\text{operational}}, 0\}$ minus pause-costs
- Optimal pause als $V_t$ zakt onder dynamische threshold $V_2^*$

**Stadium 3: Post-operational → decommission**
- Cost van decomm: zeer hoog (write-off van investments minus salvage)
- Option: $\max\{V_t \cdot \text{remaining lifetime} - \text{salvage}, 0\}$
- Optimal decomm alleen als $V_t \ll \text{salvage value}$

### 3.3 Threshold characterization

Voor elk stadium $s$, de optimal exercise threshold is:

$$V_s^* = \frac{\beta_s}{\beta_s - 1} \cdot I_s$$

waar $\beta_s$ is de positieve root van:
$$\frac{1}{2}\sigma^2 \beta(\beta-1) + \mu \beta - r = 0$$

$$\beta_s = \frac{1}{2} - \frac{\mu}{\sigma^2} + \sqrt{\left(\frac{1}{2} - \frac{\mu}{\sigma^2}\right)^2 + \frac{2r}{\sigma^2}}$$

**Key insight**: $\beta > 1$ → option value-of-waiting is positief → $V_s^* > I_s$

### 3.4 Asymmetric irreversibility voor Blue vs Green

**Blue projecten** kenmerken:
- Hogere $I$ (capital intensity: CCS infrastructure, gas-conversie)
- Hogere $\sigma$ (CCS technology uncertainty, EUA price uncertainty)
- Lager $\mu$ (CCS economics conditional on hoge EUA - regime-conditional uit Pijler 24b)

**Green projecten** kenmerken:
- Lagere $I$ (modular electrolyzer technology)
- Lagere $\sigma$ (mature electrolysis, renewables price uncertainty)
- Hoger $\mu$ (declining electrolyzer costs)

**Predictions** uit het model:

1. **Pre-FID cancellation hazard**:
   - Blue: hoog (hoge $\sigma$ → meer waarde van wachten + cancellation als bad news arrives)
   - Green: lager (lagere $\sigma$ + lagere $I$ → minder option value-of-waiting, sneller FID)

2. **Post-operational decommission hazard**:
   - Blue: zeer laag (hoge $I$ sunk → decomm alleen bij catastrofale value collapse)
   - Green: hoger (lagere $I$ → decomm relatief minder duur als economy slecht is)

**Empirische predictions matchen onze findings**:

| Predicate | Real-options model | Onze data (Pijler 16) |
|---|---|---|
| HR_Blue,cancel > 1 | ✓ Blue hogere $\sigma$ → hogere pre-FID cancel | HR = 2.30 *** |
| HR_Blue,on-hold > 1 | ✓ Optimal pause bij negatieve signal | HR = 2.57 *** |
| HR_Blue,decomm < 1 | ✓ Hoge sunk → hoge threshold voor decomm | HR = 0.235 *** |

Het real-options framework verklaart **alle drie de bevindingen tegelijk**.

---

## 4. Carbon-conditional extensie (link met Pijler 24b)

Pijler 24b vond sign-shift in β_int rond τ* = 2020. Real-options interpretation:

**Pre-2020 (lage EUA)**:
- Verwachte $\mu$ voor Blue is laag (CCS niet economisch zonder hoog carbon prijs)
- $V_t$ ligt onder threshold $V^*$
- → hoge cancellation hazard voor Blue

**Post-2020 (hoge EUA)**:
- $\mu$ stijgt (EUA prijs verhoogt verwachte cashflow voor Blue projecten met CCS)
- $V_t$ ligt boven threshold
- → hoge probability van FID + completion

**Threshold model en real-options model converge**:
- Pijler 24b's empirische sign-shift bij τ*=2020 is EXACT wat real-options voorspelt
- Methodologisch independent bevestiging via twee verschillende kaders

---

## 5. Empirical test specifications

We testen vier predictions:

**P1: Capital intensity → option value → cancellation timing**
- Hypothese: log_capacity is sterker negatief gecorreleerd met cancellation hazard voor Blue dan Green
- Cox PH met interaction: $h(t) = h_0(t) \exp(\beta_1 \cdot \text{Blue} + \beta_2 \cdot \text{log\_cap} + \beta_3 \cdot \text{Blue} \times \text{log\_cap})$
- Prediction: $\beta_3 < 0$ (groter Blue heeft lager hazard)

**P2: Volatility regime → exercise timing**
- Hypothese: hoge-EUA-volatility periodes hebben hogere cancellation hazards voor Blue
- Test: time-varying covariate $\sigma_{\text{EUA},t}$ in Cox-extended model

**P3: Asymmetric decomm**
- Hypothese: HR_Blue,decomm < HR_Green,decomm
- Test: cause-specific Cox PH (al beschikbaar uit Pijler 16)

**P4: Regime-conditional threshold**
- Hypothese: cancellation threshold $V_1^*$ ligt hoger in lage-EUA regime
- Test: Pijler 24b's threshold model (al beschikbaar)

---

## 6. Implications voor PhD Chapter 5-6

### 6.1 Theoretical chapter (Ch. 5-6) outline

**Sectie 5.1**: Standard NPV framework — onvoldoende voor sequential decisions
**Sectie 5.2**: Pindyck (1991) irreversibility + uncertainty
**Sectie 5.3**: Dixit-Pindyck (1994) sequential exercise
**Sectie 5.4**: Hydrogen-specific extensions:
  - Multi-stage exercise (announce → FID → operational → decomm)
  - Carbon-price as $\mu$-shifter
  - Asymmetric irreversibility (cheap pre-FID exit, expensive post-operational decomm)
**Sectie 5.5**: Hazard-function characterization
  - Closed-form thresholds $V_s^*$ per stadium
  - Predictions voor cause-specific HRs
**Sectie 5.6**: Connection to TVP-state-space (Chapter 7):
  - β_int(t) als reflection van regime-shifts in real-options thresholds
  - Sign-shift bij τ*=2020 is endogeen consistent

### 6.2 Empirical chapter (Ch. 8) implications

- Mechanism interpretation van Blue dual-pathway failure
- Forecasting framework: predict cancellation hazard from observable $V_t$ proxies
- Policy implications: directe subsidies verhogen $\mu$ → onmiddellijk effect op survival

### 6.3 Beleidsmpact connection

**Carrots werken via $\mu$-shift mechanism**:
- US 45Q: $85/tCO2 verhoogt verwachte cashflow → $\mu \uparrow$ → $V_s^*$ daalt → meer survival
- EU IF: capex grant verlaagt $I$ → meer projecten over threshold
- China 14th FYP: state-led commitment → verlaagt $\sigma$ → option value-of-waiting valt → snellere FID

**Sticks werken NIET via $\mu$-shift**:
- CBAM: verhoogt prijs van imports, niet inkomsten van EU projecten → geen $\mu$-shift voor EU projecten
- Daarom 8-method null

---

## 7. Conclusie

Real-options theory levert een **unified mechanism** voor:
1. Blue dual-pathway failure (Pijler 16)
2. Asymmetric decomm-hazard (HR=0.235)
3. Carbon-conditional regime-shift (Pijler 24b)
4. Cross-jurisdiction carrot-effectiveness (Pijlers 25, 26, 27, 28)

Dit is het **theoretische sluitstuk** voor de PhD-thesis: niet alleen empirische bevindingen, maar een **geïntegreerd theoretisch framework** dat ze allemaal verklaart.

Voor de defense: Koopman waardeert TVP-state-space (Chapter 7) als methodologische bijdrage. Real-options + TVP samen geven een **two-layer theoretical contribution**:
1. **Substantive**: real-options verklaart asymmetric hazards
2. **Methodologisch**: TVP-state-space onthult regime-shifts in real-options thresholds

---

## Referenties

- Bolton, P., & Kacperczyk, M. (2021). "Do investors care about carbon risk?" *Journal of Financial Economics*, 142(2), 517-549.
- Dixit, A. K., & Pindyck, R. S. (1994). *Investment Under Uncertainty*. Princeton University Press.
- McDonald, R., & Siegel, D. (1986). "The Value of Waiting to Invest." *Quarterly Journal of Economics*, 101(4), 707-727.
- Mercure, J. F., Pollitt, H., Viñuales, J. E., et al. (2018). "Macroeconomic impact of stranded fossil fuel assets." *Nature Climate Change*, 8(7), 588-593.
- Pindyck, R. S. (1991). "Irreversibility, Uncertainty, and Investment." *Journal of Economic Literature*, 29(3), 1110-1148.
- Roberts, K., & Weitzman, M. L. (1981). "Funding Criteria for Research, Development, and Exploration Projects." *Econometrica*, 49(5), 1261-1288.
