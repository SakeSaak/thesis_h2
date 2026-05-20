# Pijler 16: Multistate Lifecycle Analysis op S&P Data
## Test 4 (20 mei 2026)

**Doel**: identificeer in welke specifieke lifecycle-transitie de Blue-vs-Green fragiliteit zit, met de juiste Blue/Green-classificatie op de volledige S&P data (1 354 projecten, 273 Blue + 1 081 Green).

**Script**: `20_multistate_sp.py`
**Resultaten**: `results/multistate_*.csv`
**Figuren**: `figures/multistate_*.png`

---

## 1. Correcte Blue/Green classificatie

In v7 was Blue gedefinieerd via een vereenvoudigde regel. Voor S&P moeten we de **Technology2** kolom gebruiken:

- **Blue (CCS-based)**: Technology2 == "Fossil with CCS" → n = 273
  Bevat SMR+CCS, ATR+CCS, Coal gasification+CCS, Unknown fossil to H2 + CCS, Oil+CCS

- **Green (electrolysis)**: H2 Technology in {PEM, Alkaline, SOEC, AEM, Alkaline & PEM} → n = 1 081
  Bevat alle elektrolyse-types

Relevant sample: 1 354 projecten (vs 714 in v7) — **1.9x meer**.

---

## 2. KERN-bevindingen — drie consistente patronen

### 2.1 Cause-specific Cox PH (S&P, 1 354 projects)

| Cause | n events | HR Blue vs Green | 95% CI | p |
|---|---|---|---|---|
| **Plans cancelled** | 49 | **2.94** | [1.59, 5.46] | 0.0006 |
| **On-hold** (assumed + confirmed) | 227 | **2.89** | [2.14, 3.91] | < 0.0001 |
| **Decommissioned** | 91 | **0.25** | [0.10, 0.64] | 0.0037 |

### 2.2 Multinomial logit op huidige status (basis = still_active)

| Outcome vs Active | β (Blue) | Relative Risk Ratio | p |
|---|---|---|---|
| Cancelled | +1.337 | **3.81** | 0.0001 |
| On-hold | +1.255 | **3.51** | < 0.0001 |
| Decommissioned | +0.475 | 1.61 | 0.406 |

### 2.3 Stage waar de cancellation plaatsvindt

| Stage | Blue cancellations | Green cancellations |
|---|---|---|
| **Pre-FID (1-4)** | **100% (24/24)** | 88% (22/25) |
| Permitted | 0% (0/24) | 0% (0/25) |
| Financed | 0% | 0% |
| Construction | 0% (0/24) | 12% (3/25) |

χ² test van independence: **p = 0.25** — niet significant verschillend in *stage* van cancellation. Beide groepen cancelen voornamelijk pre-FID, maar Blue zelfs nog uniformer (100% pre-FID).

---

## 3. ⚡ Belangrijke NUANCE t.o.v. v7 paper

### 3.1 De v7 framing "they terminate, they don't pause" moet worden gekwalificeerd

| Metric | v7 paper (n=714) | S&P data (n=1 354) | Verschil |
|---|---|---|---|
| HR_cancel | **13.19** [5.28, 32.91] | **2.94** [1.59, 5.46] | 4.5× kleiner |
| HR_on-hold | **1.20** [0.34, 4.26] NS | **2.89** [2.14, 3.91] | Wel significant! |

**Twee belangrijke nuances**:

1. **HR_cancel is 4.5× lager in S&P**. De v7 sample heeft selectie-effecten die de cancellation hazard inflateren. De S&P estimate (HR = 2.94) is methodologisch geprefereerd vanwege grotere sample en breder universum.

2. **On-hold IS WEL significant verhoogd voor Blue in S&P** (HR = 2.89, p < 0.0001), waar v7 het als NS rapporteert (HR = 1.20, p = 0.78). Dit verandert het narratieve verhaal.

### 3.2 De juiste samenvatting van het Blue-failure-mechanisme

**Niet** (oude framing op basis van v7 alleen):
> *"Blue projects don't pause; they terminate."*

**Wel** (gecorrigeerde framing op basis van v7 + S&P):
> *"Blue projects experience BOTH elevated terminal cancellation AND elevated on-hold transition rates relative to Green. In the v7 preferred sample, the on-hold differential is not statistically detectable (HR=1.20, p=0.78), but in the broader S&P sample with 5x more on-hold events, it is highly significant (HR=2.89, p<0.0001). Both failure modes occur predominantly pre-FID — 100% of Blue cancellations and 88% of Green cancellations occur before financial close."*

---

## 4. Decommissioned: HR = 0.25 (Blue 4× MINDER decommissioned)

Dit is een **selectie-artefact**, geen substantieve bevinding:
- Slechts 13% van Blue projecten bereikt operational status (vs 34% Green)
- Decommissioning vereist eerst operationeel zijn
- Conclusie: Blue projecten "ontsnappen" decommissioning omdat ze nooit ver genoeg komen om gedecommissioneerd te worden

Dit is een **overlijdens-bias**: Blue projecten die de cancellation-storm overleven en operationeel worden, zijn de elite-subset die specifiek robuust is.

---

## 5. Regionaal patroon (uit multinomial logit)

Naast `is_blue_ccs` zijn ook regionale dummies informatief:

| Region | Cancelled | On-hold | Decommissioned |
|---|---|---|---|
| EU-27 | β=−0.85 (p=0.04) | β=−0.46 (p=0.04) | **β=+1.31 (p=0.002)** |
| Asia | β=−1.90 (p<0.001) | β=−0.62 (p=0.004) | β=−0.38 (NS) |
| North America | β=−0.23 (NS) | β=−0.39 (NS) | β=+0.13 (NS) |

**EU-paradox**: EU projecten worden minder vaak gecanceld én minder vaak on-hold, MAAR vaker decommissioned. Mogelijke verklaring:
- EU projecten hebben hogere financiële commitments (RFNBO subsidies) → minder cancellation pre-FID
- EU projecten worden eerder operational
- Daarna onderhevig aan strengere economische pressure → meer decommissioning

**Asia-paradox**: Asia projecten worden NOOIT decommissioned (mogelijk omdat ze recenter zijn, niet lang genoeg operationeel om gedecommissioneerd te worden).

---

## 6. Implicaties voor de scriptie

### 6.1 Chapter 5-6 (v7 hoofdresultaten) moet worden GEUPDATE

**Twee toevoegingen** in de paper Discussion of Robustness sectie:

1. **Acknowledge sample dependence**: HR_cancel varieert van 13.19 (v7) naar 2.94 (S&P) afhankelijk van sample-inclusie criteria. Beide significant maar magnitude is sample-dependent. Onze preferred sample (v7) heeft mogelijk selectie op observable characteristics die we niet volledig kunnen aboveeren.

2. **Acknowledge on-hold finding in larger sample**: in v7 is HR_on-hold = 1.20 (NS), maar in de bredere S&P data met meer power is HR_on-hold = 2.89 (p<0.0001). De Fine-Gray decompositie suggereert dat Blue projecten ZOWEL meer cancelling ALS meer on-hold transitions vertonen.

### 6.2 Het policy paper kan stronger worden gemaakt

Het verhaal wordt nu **complete fragility narrative**:
- Blue projecten falen op MEERDERE manieren (cancel + on-hold)
- Beide failure modes zijn 3-4× verhoogd t.o.v. Green
- Beide gebeuren predominantly pre-FID
- Decommissioning-statistieken zijn een selectie-artefact en niet substantief

---

## 7. Limitaties

1. **Geen exacte transition dates**: we hebben alleen huidige status + datums voor specifieke milestones (Date construction, Date online). We kunnen geen Aalen-Johansen multistate-estimator met full transition probabilities draaien.

2. **Lifecycle completion fractie failed**: de meeste cancelled projecten hebben geen Estimated year online beschikbaar — fallback waarde 0.5 maakt deze analyse oninformatief.

3. **Selection in v7**: het verschil tussen v7 HR=13.19 en S&P HR=2.94 suggereert dat de v7 sample-restrictie selectie introduceert. Voor de paper is het belangrijk om beide te rapporteren en beperking te erkennen.

---

## 8. Voor de PhD-roadmap

Dit onderzoek opent twee concrete extensions:

1. **Full Andersen-Keiding multistate framework**: vereist verzameling van transition-dates per project. Mogelijk via Wood Mackenzie, Bloomberg NEF, of LCP Delta databases (commerciële subscriptions). Tijdslijn 6-9 maanden voor data collection.

2. **Heterogeniteit in failure modes**: gegeven dat on-hold significant is in S&P, kunnen we onderzoeken WELKE Blue projecten meer kans hebben on-hold (reversibel) vs cancelled (terminaal) — bv. sponsor type, regio, capaciteit. Dit verdiept het real-options model.
