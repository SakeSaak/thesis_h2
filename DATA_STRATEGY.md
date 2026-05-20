# Data Strategy voor thesis_h2
## Hoofd-data keuze en herhaalplan (20 mei 2026)

## 1. Audit-bevindingen

### Sample comparison

| Aspect | v7 paper data | S&P Global data | Implicatie |
|---|---|---|---|
| **N projecten** | 714 | **3 249** | S&P 4.5× groter |
| **N cancellations** | 31 | **103** | S&P 3.3× meer power |
| **N on-hold events** | 12 | **905** | **S&P 75× meer power** |
| **N decommissions** | 0 | 103 | Alleen S&P beschikbaar |
| **Total events** | 43 | **1 111** | S&P 25.8× meer events |
| **Blue projecten classifiable** | 244 | 273 | Vergelijkbaar |
| **Green projecten classifiable** | 470 | 1 081 | S&P 2.3× meer |
| **Aantal kolommen** | 11 | **122** | S&P heeft 11× meer features |
| **Cancellation timing** | Exact (duration) | Proxy (midpoint) | v7 beter voor exact timing |
| **Geografische coverage** | Europa-zwaar | Global comprehensive | S&P beter voor cross-region |
| **Snapshot datum** | 2024 | **24 maart 2026** | S&P actueler |

### Rijke S&P features die v7 niet heeft

- **Output capacity per year** (100% complete) — exacte productie-capaciteit
- **Total renewables capacity (MWac)** (100% complete) — voor 45V analyses
- **Ammonia capacity (t/y)** (21%) — voor end-use analyses
- **Project phase** (Phase 1-6) (20%) — voor lifecycle stage tests
- **End use, Off-taker, Subsidies/grants, CO2 capture rate** — voor mechanism analyses

## 2. Strategische keuze: S&P als hoofd-data

### Beslissing
**S&P Global wordt vanaf nu de primaire hoofd-data** voor alle nieuwe pijlers (≥ Pijler 18). v7 wordt **legacy-data** voor:
- Vergelijking met de oorspronkelijke paper findings
- Tests waar exact event timing essentieel is (klassieke Cox PH met `duration`)
- Replicatie-doeleinden

### Drie redenen voor S&P als hoofd-data

1. **Statistical power**: 25.8× meer events maakt detection van kleine effecten mogelijk
2. **Multistate completeness**: alleen S&P heeft alle 13 project_status niveaus inclusief decommissioning
3. **Feature richness**: 122 kolommen versus 11 — meer mechanism analyses mogelijk

### Belangrijke caveat
- Cancellation timing in S&P is proxy (`midpoint(announce, est_online)` of `announce + 3`). Voor analyses die exact event-timing vereisen (klassieke Cox PH), moeten we expliciet de proxy-noise rapporteren of v7 als secondary check gebruiken.

## 3. Inventarisatie tot nu toe: welke pijler gebruikt welke data?

| Pijler | Topic | Data gebruikt | Aanbeveling |
|---|---|---|---|
| 1 | Basic Cox PH + covariates | v7 | **🔄 Herhalen op S&P** (Pijler 19) |
| 2-4 | Schoenfeld, Fine-Gray competing risks | v7 | OK — v7 is voor klassieke survival analyse |
| 5 | Synthetic DiD (single t*) | v7 project-level | **🔄 Herhalen op S&P** (Pijler 20) |
| 6-7 | Sensitivity tests | v7 | OK voor v7 — replicate als nodig |
| 8 | Honest DiD bounds | v7 | OK — methodologisch robuust |
| 9-11 | Lasso, instrument variabelen | v7 | Niet kritiek |
| 12 | **Causal Forests** | v7 | **🔄 PRIORITEIT — herhalen op S&P** (Pijler 21) |
| 13 | Multistate v7 | v7 | ✓ Reeds vervangen door Pijler 16 (S&P) |
| 14 | Deaner-Ku v7 | v7 | ✓ Reeds vervangen door Pijler 15 (S&P) |
| 15 | Deaner-Ku S&P dual t* | **S&P** | ✓ S&P primary |
| 16 | Multistate Lifecycle | **S&P** (1354) | ✓ S&P primary |
| 17 | Sequential SDID | **S&P regional** | ✓ S&P regional |

## 4. Aanbevolen herhaal-tests op S&P data

### 🔥 Prioriteit 1: Pijler 12 — Causal Forests
- **Reden**: CBAM-feature-importance ranking (0.009) was op v7 (43 events). Met S&P (1111 events) zou de ranking 25× meer power hebben. Dit is CRUCIAAL voor de "informative null" claim.
- **Output**: nieuwe variable importance ranking + heterogeneous treatment effects per project subgroup
- **Estimated impact op thesis**: zou kunnen leiden tot revised feature ranking — als CBAM ranking op S&P consistent laag blijft, is de informative null nog sterker

### 🔥 Prioriteit 2: Pijler 1 — Master Cox PH met covariates
- **Reden**: hoofdregressie van de paper. Heeft nu impliciete versie in Pijler 16 (cause-specific) maar geen formele covariate sweep.
- **Output**: full Cox PH model op cancellation hazard met log_capacity, year_announced, region, sponsor_type, end_use (S&P only)
- **Compare**: v7 HR_Blue = 11.93 vs verwachte S&P HR ~2.30

### 🔥 Prioriteit 3: Pijler 5 — Synthetic DiD project-level
- **Reden**: regional aggregation (Pijler 17) verlies project-niveau heterogeneity. Een project-level SDID op S&P zou de matching scherper maken.
- **Output**: SDID ATT met project-level controls

### ⚠️ Lage prioriteit
- Pijler 6-11: niet kritiek, kunnen als robustness in chapter appendix
- Pijler 2-4: v7-specific classical survival is OK

## 5. Voor de huidige Test 8 (45V three-pillars)

Test 8 gaat over US-IRA 45V tax credit announcement. De relevante data is:
- Geografische split: US (North America) versus non-US
- Tijdstippen: NPRM december 2023, Final rule 3 januari 2025
- Sample: S&P 3249 (NA = 381, non-NA = 2868)

→ **S&P is hier de juiste keuze**. v7 zou met N_NA = 162 te klein zijn voor robuuste US-only inference.

## 6. Roadmap voor remaining sessies

1. **Vandaag**: Test 8 (45V three-pillars) op S&P → Pijler 18
2. **Vervolg**: Pijler 19 = Causal Forests op S&P (vervangt Pijler 12)
3. **Daarna**: Pijler 20 = Master Cox PH op S&P (vervangt Pijler 1)
4. **Daarna**: Pijler 21 = Synthetic DiD project-level op S&P (vervangt Pijler 5)
5. **Tot slot**: Bijgewerkte FINAL_SYNTHESIS_v3 die alle pijlers consolideert

## 7. Methodologische transparantie voor de thesis

In Chapter 3 (Data en Methods) moet expliciet worden gesteld:
> "We employ two complementary datasets. The v7 dataset (N=714, 43 events) underlies the original paper's classical survival analysis with exact event timing. The S&P Global hydrogen projects database (N=3249, 1111 events, snapshot 24 March 2026) serves as the primary data for all robustness extensions in this thesis, providing 25.8× more events and 122 features versus v7's 11. Where exact event timing is essential, we use v7 as the secondary check; where statistical power is critical, we use S&P as the primary source."

Dit voorkomt dat de tegenstrijdige resultaten tussen v7 en S&P als methodologische zwakte worden gezien — ze zijn juist **methodologisch correcte triangulatie** met expliciete sample-dependent reporting.
