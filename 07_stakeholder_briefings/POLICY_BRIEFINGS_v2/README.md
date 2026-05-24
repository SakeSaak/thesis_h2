# Policy Briefings v2 — Stakeholder Deliverables

**Datum**: 20 mei 2026
**Onderzoek**: *Implementation-Risk Differentials in Hydrogen Technology Pathways*
**Auteur**: Sake Saakstra (MSc EOR Financial Track, VU Amsterdam)
**Supervisor**: prof. the external reviewer | **Second reader**: the second reviewer

---

## Inhoud van deze map

| Bestand | Voor wie | Pagina's | Doel |
|---|---|---|---|
| `01_EU_DG_CLIMA_briefing.md` | EU beleidsmakers (DG CLIMA, DG ENER) | 2-3 | Beleidsadvies obv counterfactual scenarios |
| `02_Gasunie_BL_Waterstof_briefing.md` | Gasunie BL Waterstof NL, HyNetwork team | 2-3 | Strategische lessen voor Backbone business case |
| `03_Sponsors_thesis_briefing.md` | Supervisor + sponsors + thesis-committee | 3 | Voortgangs- en bevindingen-overzicht |

Plus deze README voor navigatie en context.

---

## Onderbouwende analyses (in main repo)

Alle briefings refereren naar gecommitte pijlers in de thesis-repo:

| Pijler | Wat | Locatie |
|---|---|---|
| **Pijlers 25-28** | Hoofd-DiD: US 45Q, EU IF, UK Track, China FYP | `06_thesis_extensions/10_carrot_taxonomy/` |
| **Pijler 24c** | TVP-DiD structural break τ*=2020 | `06_thesis_extensions/09_dynamic_did/` |
| **Pijler 30** | Causal Forest HTE | `06_thesis_extensions/12_advanced_robustness/39_causal_forest_HTE_carrots.py` |
| **Pijler 32** | Modern DiD robustness (TWFE+BJS+Sun-Abraham) | `06_thesis_extensions/12_advanced_robustness/42_modern_did_robustness.py` |
| **Pijler 34** | Offtake-effect (multi-method identification) | `06_thesis_extensions/12_advanced_robustness/43_offtake_effect_identification.py` |
| **Pijler 39** | Honest DiD bounds (Rambachan-Roth 2023) | `06_thesis_extensions/12_advanced_robustness/44_honest_did_bounds.py` |
| **Pijler 40** | Real-options × mechanism design theory | `06_thesis_extensions/13_theoretical/PIJLER40_REAL_OPTIONS_MECHANISM_DESIGN.md` |
| **Pijler 36** | Counterfactual policy scenarios | `06_thesis_extensions/14_counterfactual/46_counterfactual_scenarios.py` |

---

## Hoe de briefings te gebruiken

Elk briefing-document is **standalone leesbaar** — bedoeld om uit te printen of als PDF te versturen. Geen academische referenties in de hoofdtekst (die staan in de thesis), wel een korte bron-sectie onderaan voor wie dieper wil graven.

**Voor presentatie/discussie**: gebruik de getallen-tabellen direct. Voor academische review: verwijs naar de onderliggende pijlers.

---

## Belangrijke methodologische context

Onze counterfactual-getallen zijn **upper-bound point estimates met bootstrap-CI's**. Ze veronderstellen dat de ATE (gemeten in onze sample) extrapolable is naar de target-population. Aannamen waar dit niet kan kloppen:

- **Heterogene project-kwaliteit**: nieuwe projecten in counterfactual scenarios zouden lagere kwaliteit kunnen hebben (gemiddeld)
- **Schaalbaarheid**: ATE zou kunnen verzwakken bij large-scale implementatie
- **Concurrence-effecten**: één land's 45Q-equivalent zou rivaal-projecten kunnen cancelleren

Voor briefings hanteren we **conservatieve interpretaties** en rapporteren altijd 95% CI's. Voor publieksgerichte uitspraken: alleen punten waar onderlijning consistent is across methoden (zie `08_synthesis/FINAL_SYNTHESIS_v4_2026-05-20.md` voor de waterdicht/gequalificeerd scorecard).
