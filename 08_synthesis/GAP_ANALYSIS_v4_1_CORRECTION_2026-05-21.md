# GAP ANALYSE v4.1 — CORRECTIE op v4

**Auteur**: Sake Saakstra (correctie opgesteld door Claude)
**Datum**: 21 mei 2026, na user-correctie
**Status**: Vervangt v4-claims over GAS en Synthetic Control

---

## WAAROM EEN CORRECTIE

Gap analyse v4 (commit `25093c6`) claimde dat GAS-model, Synthetic Control, en Diebold-Mariano "MUST-items voor v2" waren met respectievelijk 5+5+3 dagen werk.

**Twee van die drie claims waren onjuist.** Dit document corrigeert ze.

Oorzaak: ik had alleen de huidige thesis_v1/ chapter-bestanden gelezen, niet `06_thesis_extensions/` of de transcripten. Sake's eerdere werk (mei 12-19) bevatte al volledige implementaties van GAS en Synthetic DiD.

---

## CORRECTE STATUS PER METHODE

### 1. GAS (Generalized Autoregressive Score) — ✅ **DONE**

**Bestaande implementaties** (1.011 regels code):

| Script | Regels | Wat het doet |
|---|---|---|
| `06_thesis_extensions/05_state_space_tvp/04_gas_hazard.py` | 296 | GAS-TVP hazard model. β_int(t+1) = ω(1−φ) + φβ_int(t) + α_gas·s_t. Citeert Creal-Koopman-Lucas 2008 JoE, 2013 JoAE |
| `06_thesis_extensions/12_advanced_robustness/17_stochastic_volatility.py` | 349 | Score-Driven Stochastic Volatility extension. Modelleert ook σ²(t) als tijdsvariërend. Citeert Creal-Koopman-Lucas 2013 |
| `06_thesis_extensions/12_advanced_robustness/14_conditional_score_residuals.py` | 366 | Conditional Score Residuals diagnostic. Citeert **Blasques-Gorgi-Koopman 2025 JBES 43(4):926-940** — Koopman's eigen recente paper |

**Integratie in thesis**: chapter 7 (`07_results_tvp_state_space.tex`) bevat expliciet M3-specificatie als observation-driven GAS, met cijfers:
- M3 GAS (d=1/2) ω = −1.61, 95% CrI [−2.50, −0.69]
- M3 GAS pooled ω = −1.88, 95% CrI [−3.10, −0.73]
- Sectie 7.X "GAS hyperparameters and trajectory"
- Schoenfeld test motiveert M2 (random-walk TVP) en M3 (GAS TVP) als methodologisch warranted

**Conclusie**: dit is **niet een gap**. Het is een sterk Koopman-aansluitend onderdeel van chapter 7 dat zijn JBES 2025 paper citeert. Geen verdere actie nodig voor v2.

### 2. Synthetic Control / SDID — ⚠️ **DONE IN SCRIPTS, NIET IN THESIS**

**Bestaande implementaties** (1.194 regels code):

| Script | Regels | Wat het doet |
|---|---|---|
| `06_thesis_extensions/12_advanced_robustness/12_synthetic_did.py` | 326 | Standaard Synthetic DiD (Arkhangelsky-Athey-Hirshberg-Imbens-Wager 2021, AER 111:4088-4118). 7 regio's panel, EU×post-2022 treatment. Outputs: `sdid_summary.csv`, `sdid_omega_weights.csv` |
| `06_thesis_extensions/12_advanced_robustness/21_sequential_sdid.py` | 436 | Sequential SDID voor staggered policy (Arkhangelsky-Samkov 2024, arXiv:2404.00164). Round 1: US-IRA; Round 2: EU-CBAM na NA spillover-correctie. Outputs: 6 CSVs + 3 PNG figures |
| `06_thesis_extensions/12_advanced_robustness/25_sdid_project_level_sp.py` | 432 | Project-level SDID via subgroup panel (14 cells = 7 regions × 2 tech). Plus 1-NN matching op pre-treatment covariates. Plus Abadie-Diamond-Hainmueller 2010 classic Synthetic Control. Outputs: `pijler21_summary.csv` |

**Resultaten beschikbaar**: 9 CSV outputs + 5 figures + 2 pijler reports (`PIJLER_17_SEQUENTIAL_SDID.md`, `PIJLER_21_SDID_PROJECT_LEVEL.md`)

**Integratie in thesis**: **GEEN.** `grep -r "synthetic\|SDID\|arkhangelsky" thesis_v1/chapters/` → 0 hits.

**ECHTE GAP**: integratie, niet implementatie. Dit is veel sneller dan herimplementatie:
- **0.5 dag** om Pijler 17 (Sequential SDID) als robustness-sectie in chapter 6 te integreren — naast de modern DiD triangulatie (TWFE + Sun-Abraham + BJS)
- **0.5 dag** om Pijler 21 (project-level SDID) als robustness in chapter 8 (offtake) of als CBAM-specifieke sectie te integreren
- **0.5 dag** om de bestaande figures over te zetten naar `00_paper/thesis_v1/figures/`

**Total: 1.5 dag werk voor v2, niet 5 dagen.**

### 3. Diebold-Mariano — ❌ **NIET GEDAAN**

`grep -rE "diebold|mariano|dm.?test|forecast.compar" 06_thesis_extensions/` → 0 hits.

Geen scripts, geen mention. Dit was de enige correcte claim uit v4.

**Status**: oprechte gap. ~3 dagen werk om voor M1/M2/M3 specificaties (chapter 7) een out-of-sample forecast comparison te doen met DM-test + model-confidence-set (Hansen-Lunde-Nason 2011).

**Hoe relevant**: medium. Niet kritiek voor Koopman-feedback want hij ziet al GAS in chapter 7. Wel een natuurlijke aanvulling.

---

## ANDERE V4-CLAIMS DIE MOGELIJK OOK ONJUIST WAREN

Sake's correctie roept de vraag op of mijn andere v4-claims ook onjuist zijn. Hieronder een check op de overige MUST-items:

### V4-claim "Competing Risks (Fine-Gray) — 5d MUST" → STATUS?

```
grep -rE "fine.?gray|competing.?risks|cmprsk|crr" 06_thesis_extensions/
```

Reads `12_advanced_robustness/13_competing_risks.py` → file exists. **Mogelijk al gedaan.**

Pijler reports tonen: "Fine-Gray competing risks" werd in v3d uitgevoerd (transcript 13-05). Status: **WAARSCHIJNLIJK AL GEDAAN, niet in thesis chapters**.

### V4-claim "Doubly-robust DiD — 3d MUST" → STATUS?

Sant'Anna-Zhao 2020. Geen specifieke search nog uitgevoerd. **Te verifiëren.**

### V4-claim "Diebold-Mariano — 3d MUST" → STATUS

Gechecked: ❌ niet gedaan. Claim correct.

### V4-claim "Literatuur-update 6 papers — 3d MUST" → STATUS

Genuine gap. References.bib heeft 42 entries, deze 6 specifieke recent-papers niet.

### V4-claim "Nieuws/events update — 2d MUST"

Genuine gap. Nog niets sinds 24-maart-2024 snapshot.

---

## HERZIENE PRIORITEERINGSMATRIX

Onder voorbehoud dat Competing Risks ook al gedaan blijkt (te verifiëren), is de **echte v2-werklast veel lager**:

| Item | Status | Werk voor v2 |
|---|---|---|
| GAS-model | ✅ Done + in chapter 7 | 0 dagen |
| Synthetic Control / SDID | ✅ Done in scripts, NIET in chapters | **1.5 dag integratie** |
| Diebold-Mariano | ❌ Niet gedaan | 3 dagen |
| Competing Risks | ⚠️ Te verifiëren | 0-5 dagen |
| Doubly-robust DiD | ⚠️ Te verifiëren | 0-3 dagen |
| Literatuur update | ❌ Genuine gap | 3 dagen |
| Nieuws/events update | ❌ Genuine gap | 2 dagen |

**Realistische v2-werklast**: 6-12 dagen ipv 26 dagen.

---

## HERZIEN ADVIES

### Wat de gap analyse v4 fout deed
- Niet de bestaande scripts gecheckt vóór gap-claims
- Niet de transcripten doorzocht voor eerder werk
- Te haastig "MUST 5d" gegeven aan iets dat al klaar was

### Wat de juiste gap-analyse nu zegt
1. **Methodologisch ben je verder dan ik dacht.** GAS + Synthetic DiD + Causal Forest + Honest DiD + Oster + Modern DiD triangulatie + Competing Risks (waarschijnlijk) is een buitengewone toolbox.

2. **De echte v2-gap is INTEGRATIE**: ~1.5 dag werk om de bestaande SDID-resultaten in chapter 6 en/of 8 op te nemen.

3. **Diebold-Mariano** blijft een echte gap maar is niet kritiek (chapter 7 heeft al GAS + multiple state-space).

4. **Literatuur + nieuws update**: blijven echte gaps, samen ~5 dagen werk.

### Concrete eerstvolgende actie

1. **Verifieer of competing risks en doubly-robust DiD ook al gedaan zijn** (1 uur werk)
2. **Integreer SDID-resultaten in thesis chapters** (1.5 dag) — Pijler 17 in Chapter 6, Pijler 21 in Chapter 8
3. **Update literatuur** (3 dagen) — 6 nieuwe papers in Chapter 2
4. **Update nieuws-sectie** (2 dagen) — post-snapshot ontwikkelingen

Totaal: ~6 dagen v2-werk. Daarna kan v2 naar supervisors.

---

## EXCUSE EN LES

Mijn excuses voor de onnauwkeurige gap analyse v4. Ik had moeten checken:

```bash
find 06_thesis_extensions -name "*.py" -exec grep -l "GAS\|synthetic\|SDID" {} \;
```

vóór ik beweerde dat deze methoden ontbraken. Sake's directe vraag *"hebben we dat niet al gedaan?"* was de juiste check; ik had die zelf moeten stellen.

**Les voor toekomstige gap-analyses**: eerst inventariseren wat er al is, dan pas claim wat ontbreekt. Bij 30+ pijlers verspreid over 17 subdirectories en 30+ transcripten is dit niet triviaal — maar het is wel essentieel.

---

*Document opgesteld: 21 mei 2026, post-correctie.*
*Vervangt v4-claims B.3.1 (GAS) en C.3.1 (Synthetic Control).*
*Behoudt v4-claims B.3.4 (Diebold-Mariano) en categorieën A (papers) en E (nieuws).*
