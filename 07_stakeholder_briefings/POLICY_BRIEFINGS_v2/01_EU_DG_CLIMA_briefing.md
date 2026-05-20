# Policy Briefing — European Commission DG CLIMA / DG ENER

**Subject**: Mechanism-design implications for the EU's clean hydrogen support architecture

**Date**: 20 May 2026
**Prepared by**: Sake Saakstra, MSc Econometrics & Operations Research, VU Amsterdam
**For internal use**: policy advisors, Innovation Fund team, EU Hydrogen Bank team
**Length**: 2 pages

---

## Executive Summary

A causal evaluation of 1,354 announced low-carbon hydrogen projects (2010–2024) finds that **the Innovation Fund's capex-grant architecture has no detectable effect on project-survival outcomes**, while pre-FID offtake commitments reduce project-failure probability by 11–13 percentage points across five independent identification strategies. We estimate that linking Innovation Fund eligibility to demonstrable offtake commitments could yield **+83 additional Final Investment Decisions** within the existing EU green hydrogen project pipeline over a 3-year horizon, corresponding to **+858 kt/year of additional H₂ production capacity** (95% CI: 355–1,459 kt/y). A sector-optimal hybrid policy package combining capex relief for chemical/refinery sectors with offtake-coordination for power & heat / transport sectors could deliver **+113 FIDs and +7.8 Mt/y additional CO₂ capture**.

These findings are corroborated by the wave of 2024–2026 cancellations: ArcelorMittal walked away from its Bremen and Eisenhüttenstadt projects despite €1.3B in committed Innovation Fund subsidies, and seven Hydrogen Bank auction winners (1.88 GW combined) withdrew from grant negotiations in September 2025. The empirical signal is clear: **subsidies without offtake-commitment fail**.

---

## 1. The diagnostic finding: capex-grants alone do not move the needle

| Policy mechanism | Estimated effect on annual hazard | Significance | Honest DiD robustness |
|---|---|---|---|
| US Section 45Q (output-credit) | −0.045 | p<0.001 | M*=0.20 (sensitivity-bounded) |
| EU Innovation Fund (capex-grant) | +0.009 | ns | M*=0.00 |
| UK Track-1 (cluster-tender) | +0.036 | ns / mixed | M*=0.00 |
| China 14th FYP (state-mandate) | −0.045 | p<0.001 | **M*=1.50 (robust)** |
| **Offtake commitment (pre-FID)** | **−0.111 to −0.131** | **p<0.001** | **Oster δ_null=20.23** |

Convergence across TWFE, Sun-Abraham (2021), and Borusyak-Jaravel-Spiess (2024) imputation estimators yields the central estimates. Rambachan-Roth (2023) honest sensitivity bounds reveal that **only China's state-coordinated approach and the offtake-effect survive the strictest robustness checks**. The Innovation Fund's null effect is consistent across all six methods — this is an informative, not noisy, null.

## 2. The structural break: why the policy mix needs rethinking

A time-varying parameter analysis (state-space + threshold + random-walk; all converge) identifies a sign-shift in the carrot-policy coefficient around **τ\* = 2020**. Before 2020, subsidy-eligible projects were more likely to survive; after 2020, they are *not* — controlling for sector, capacity, and sponsor. The mechanism is straightforward: the post-2020 announcement boom (300%+ increase in pipeline) attracted speculative entrants chasing subsidies without genuine commercial backing. This pattern is fully consistent with Odenweller & Ueckerdt (Nature Energy 2025), who document that only ~7% of announced 2023 capacity reached scheduled FID.

## 3. Counterfactual scenarios — quantified policy alternatives

Bootstrap-validated estimates (500 reps, 95% CI's):

| Scenario | Target population | Extra FIDs (3y) | Additional capacity |
|---|---|---|---|
| **EU adopts 45Q-equivalent (Blue)** | 26 EU Blue projects | +4 [2, 5] | +3.40 Mt/y CO₂ capture |
| **IF eligibility → offtake mandate** | 250 EU Green projects sans offtake | **+83 [39, 128]** | **+858 kt/y H₂** |
| **OECD adopts China-FYP-style mandate** | 729 OECD Green projects | +98 [32, 160] | +976 kt/y H₂ |
| **EU sector-optimal hybrid mix** | 337 EU projects post-2017 | **+113 [82, 141]** | **+7.83 Mt/y CO₂ + 1.76 Mt/y H₂** |

Methodological note: ATEs sourced from BJS-imputation (Pijler 32) for policy effects, PSM 1:3 for offtake (Pijler 34, Oster sensitivity δ_null=20.23). 3-year cumulative horizon reflects typical post-FID stabilization window.

## 4. Theoretical foundation

A Dixit-Pindyck (1994) real-options framework distinguishes two channels:

- **V/I-boost mechanisms** (output credits, capex grants) raise the value-to-investment ratio. Effective in low-volatility sectors (chemical, refinery) where revenue uncertainty is already manageable.
- **σ-attack mechanisms** (offtake mandates, cluster-tender) reduce revenue volatility directly. Effective in high-volatility sectors (power & heat, transport) where uncertainty is the binding constraint.

Empirical heterogeneity (Pijler 34) confirms this: offtake-effect reaches **−22.8 pp in power & heat** and **−25.7 pp in refinery**, but is non-significant in chemical (where baseline failure rate is already low).

## 5. Concrete policy recommendations

1. **Hard-link Innovation Fund eligibility to demonstrable offtake commitments**: a binding pre-FID LOI from a named industrial offtaker, with minimum 5-year commitment.
2. **Differentiate subsidy intensity by sector**: lighter capex-grants for chemical/refinery, heavier σ-coordination instruments for power & heat / transport.
3. **Maintain output-credit option** (Carbon Contracts for Difference): functionally equivalent to a 45Q-style mechanism; effective for capital-intensive Blue infrastructure.
4. **Avoid undifferentiated cluster-tender approaches**: UK Track-1's mixed performance (positive headline effect masking selection-funnel artifact) suggests that sub-tier project pre-selection matters more than tender architecture.

## 6. Limitations honestly stated

- Effects are average-treatment estimates; sector-level heterogeneity is substantial.
- US 45Q effect, EU IF null, and UK Track-1 estimates have varying robustness profiles (see Pijler 39).
- Counterfactual impact figures assume ATE-extrapolation to non-treated population; concurrence effects not modeled.

---

### Sources

- S&P Global Hydrogen Production Assets database (snapshot 24 March 2024)
- Pijlers 25–34, 36, 39, 40 of underlying thesis research (GitHub: SakeSaak/thesis_h2)
- Rambachan & Roth (2023), Borusyak-Jaravel-Spiess (2024), Sun & Abraham (2021), Oster (2019)
- Odenweller & Ueckerdt (2025), *Nature Energy*: "The green hydrogen ambition and implementation gap"
- Industry signal: BP HyGreen Teesside cancellation (Oct 2025), ArcelorMittal Bremen withdrawal (2025), EU Hydrogen Bank seven-project withdrawal (Sept 2025)

**Contact**: Sake Saakstra | sake.saakstra@student.vu.nl | Github: SakeSaak/thesis_h2
