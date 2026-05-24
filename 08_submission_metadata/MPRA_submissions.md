# MPRA submission packages

Upload-ready metadata for four standalone companion papers from `thesis_h2` ([github.com/SakeSaak/thesis_h2](https://github.com/SakeSaak/thesis_h2)). All four are single-author work by Sake Saakstra, independent researcher, Amsterdam. Concept DOI of underlying research: **10.5281/zenodo.20359771**.

## About MPRA submission

MPRA (Munich Personal RePEc Archive) automatically indexes accepted papers in RePEc, IDEAS, and EconPapers within 24–48 hours of editorial approval. Each accepted paper receives a permanent MPRA Paper No. and contributes to the author's IDEAS/RePEc author profile.

## How to submit

1. Login at https://mpra.ub.uni-muenchen.de
2. Click "New deposit" or "Submit paper"
3. Choose document type: **MPRA Paper**
4. For each paper below, copy each field from the corresponding block
5. Upload the PDF from the path noted in the block
6. Add the JEL codes using the MPRA built-in JEL picker (codes listed below)
7. Add keywords (one per line in the keywords field)
8. License: **Creative Commons Attribution 4.0 International (CC-BY 4.0)**
9. "Related URL": link to the corresponding GitHub paper folder
10. Submit for editor approval (1-2 working days)

---

## Paper 1

**PDF to upload**: `09_papers/paper1_tvp_methodology/tex/paper1_main.pdf`

### Title

A time-varying-parameter state-space approach to sparse-event survival modelling: methodological design, out-of-sample performance, and application to hydrogen project implementation-risk

### Author

Saakstra, Sake (sole author)

Affiliation: Independent researcher, Amsterdam

Email: S.Saakstra@student.vu.nl

### Abstract

We propose a time-varying-parameter (TVP) state-space approach to survival modelling under sparse-event data conditions, in which the conditional hazard depends on a generative-process parameter whose evolution is driven by the score of the predictive likelihood. The Score-Driven Generalized Autoregressive Score (GAS) specification of Creal, Koopman, and Lucas (2013) provides a parsimonious and asymptotically optimal mechanism for parameter time-variation, requiring only the score and a one-parameter persistence specification. The methodology is motivated by, and applied to, the empirical setting of irreversible clean-technology investments under transition uncertainty, where the policy-conditional hazard of project cancellation is plausibly regime-dependent rather than constant --- a setting in which constant-parameter survival models systematically under-estimate the time-variation of the operating economic mechanism.

Three rival TVP specifications are compared: M1 with constant parameter, M2 with parameter-driven block-step transitions, and M3 with observation-driven GAS persistence. The three are tested for out-of-sample forecast accuracy via three independent designs --- a 75-25 time split, 5-fold within-project block cross-validation, and rolling one-step-ahead full-sample prediction. Significance is assessed by the Diebold-Mariano-Harvey-Leybourne-Newbold test on per-observation Bernoulli log-loss. The Score-Driven specification wins uniformly in point estimates across all three designs and is the unique element of the Hansen-Lunde-Nason Model Confidence Set at alpha = 0.10 under the rolling-one-step design. The DM-HLN test statistics for M3 versus M1 and M3 versus M2 are +5.59 and +4.80 respectively (p < 0.0001) under the rolling-window design, with the largest performance gain concentrated in the 2023 cancellation wave where the carbon-conditional mechanism intensifies.

Following the framing of Blasques, Gorgi, Koopman, and Stegehuis (2024), we position the contribution as an extension of score-driven dynamic parameter modelling Creal, Koopman, and Lucas (2013) into a sparse-event implementation-risk context characterised by regime-sensitive transition dynamics, rather than as a fundamentally new econometric class. The methodology is applied to a sample of 714 hydrogen projects with 43 failure events, drawn from the v7 working-paper sample of Saakstra (2026), spanning announcement-stage status from 2010--2026. The aggregated person-year panel contains 4162 observations, reduced to 34 Binomial cells by year-and-technology aggregation. The interaction coefficient β_int(t) governing the carbon-conditional Blue/Green hazard differential is estimated to intensify from -0.46 in 2010 to -1.49 in 2024 under the score-driven specification, with a structural break detected around 2020. The Score-Driven TVP approach is a useful general-purpose methodology for survival modelling in domains with sparse-event data, sample-window dependence concerns, and reasonable suspicion of structural-break dynamics.

### JEL classification (use MPRA built-in picker)

C32, C41, Q42

### MPRA subject classification breakdown

C - Mathematical and Quantitative Methods > C3 - Multiple or Simultaneous Equation Models; C32 - Time-Series Models; Q - Agricultural and Natural Resource Economics; Q4 - Energy; Q42 - Alternative Energy Sources

### Keywords (one per line)

- time-varying parameter
- score-driven model
- state-space
- survival modelling
- Diebold-Mariano test
- hydrogen
- sparse events
- structural break

### Language

English

### License

Creative Commons Attribution 4.0 International (CC-BY 4.0)

### Related URL

https://github.com/SakeSaak/thesis_h2/tree/main/09_papers/paper1_tvp_methodology

### Date created

23 May 2026

---

## Paper 2

**PDF to upload**: `09_papers/paper2_carrot_policy_did/tex/paper2_main.pdf`

### Title

Mechanism Design over Magnitude: A Multi-Jurisdiction Evaluation of Carrot-Policy Effectiveness in Clean-Hydrogen Implementation

### Author

Saakstra, Sake (sole author)

Affiliation: Independent researcher, Amsterdam

Email: S.Saakstra@student.vu.nl

### Abstract

We evaluate six major clean-hydrogen policy interventions across four jurisdictions (US 45Q, US 45V three-pillars NPRM, EU Innovation Fund, EU CBAM, UK Track-1, China 14th Five-Year Plan) using a project-level panel of 1354 announced hydrogen developments from the S&P Global Hydrogen Project Database (2010--2026). Treatment effects on cumulative cancellation probability are estimated using modern difference-in-differences estimators (Sun--Abraham IW, Borusyak--Jaravel--Spiess imputation, IPWRA matching, Synthetic DiD, Causal Forests, and Deaner--Ku hazard DiD) and accompanied by Rambachan--Roth honest-sensitivity bounds.

Three substantive findings emerge. First, the magnitude ranking of policy effects (China 14th FYP > US 45Q > UK Track-1 EU Innovation Fund) systematically follows the number of economic frictions each instrument addresses, not the per-unit monetary value of the subsidy. The China FYP estimate of -4.5 percentage points (honest-DiD breakdown M* = 1.5) exceeds the US 45Q estimate of -3.4 percentage points (M* = 0.2) despite comparable per-unit subsidy value, consistent with multi-friction mechanism dominance. Second, two informative nulls are identified: the EU Innovation Fund produces a precise null across six convergent estimators, and the EU CBAM produces a precise null across eight convergent estimators. The substantive interpretation is that the financing-constraint friction is not binding in the contemporary capital-abundant hydrogen environment, and that border-adjustment transmission to project-level investment decisions is weak in the early-implementation phase. Third, the US 45V three-pillars NPRM triple-difference estimate of +0.285 on US-Green cancellation hazard identifies friction amplification by policy design --- the cleanest empirical test of perverse-direction κ-channel effects in the sample.

The methodological contribution is a pre-registered mechanism-falsifiability framework that disciplines mechanism interpretation against post-hoc rationalisation, combined with multi-method triangulation that strengthens both confirmatory and informative-null inferences. The policy implication is that reform of capex-grant instruments such as the EU Innovation Fund should incorporate offtake-commitment eligibility requirements, jointly addressing both financing and counterparty-risk frictions.

### JEL classification (use MPRA built-in picker)

C21, C23, Q42, Q48, Q58

### MPRA subject classification breakdown

C - Mathematical and Quantitative Methods > C2 - Single Equation Models; C21 - Cross-Sectional Models; Q - Agricultural and Natural Resource Economics > Q4 - Energy > Q48 - Government Policy; Q58 - Environmental Economics: Government Policy

### Keywords (one per line)

- difference-in-differences
- honest sensitivity
- clean hydrogen
- carbon pricing
- policy evaluation
- mechanism design
- carbon border adjustment

### Language

English

### License

Creative Commons Attribution 4.0 International (CC-BY 4.0)

### Related URL

https://github.com/SakeSaak/thesis_h2/tree/main/09_papers/paper2_carrot_policy_did

### Date created

23 May 2026

---

## Paper 3

**PDF to upload**: `09_papers/paper3_offtake_mechanism/tex/paper3_main.pdf`

### Title

The Offtake-Commitment Mechanism: Sigma-Channel Identification via Cross-Sectoral Heterogeneity in Clean-Hydrogen Investment

### Author

Saakstra, Sake (sole author)

Affiliation: Independent researcher, Amsterdam

Email: S.Saakstra@student.vu.nl

### Abstract

Pre-financial-investment-decision (pre-FID) offtake commitments in clean-hydrogen projects reduce the cumulative cancellation probability by 11.3 to 13.2 percentage points across five convergent matching estimators (IPWRA, OLS-adjusted, regression-adjusted matching, doubly-robust IPTW, naive IPW), using a project-level panel of 1354 announced developments from the S&P Global Hydrogen Project Database (2010--2026). The estimate is exceptionally robust to unobserved-confounder bias: the Oster _{{null}} = 20.23 implies that for unobservables to explain the effect, they would need to be twenty times more influential than the maximally-included set of observable controls. This is the largest and most identification-secure treatment effect in the related dissertation work.

The substantive interpretation invokes the σ-channel of the real-options framework: offtake commitments reduce revenue volatility (F1 friction) and counterparty risk (F7 friction) simultaneously. The σ-channel comparative statics predict that revenue-volatility-reducing instruments should produce larger effects in high-volatility sectors than in low-volatility sectors. We test this prediction directly via cross-sectoral heterogeneity: the offtake-commitment ATT is concentrated in power and heat (-0.30pp) and transport (-0.27pp), and substantially smaller or null in chemical (-0.04pp) and refinery (-0.02pp). The pattern matches the σ-channel prediction in sign and approximate magnitude, providing direct mechanism-identifying empirical evidence (L4) that complements the average-treatment-effect identification (L3.a + L3.b).

The methodological contribution is a cross-sectoral heterogeneity test as a direct mechanism-identifying strategy, supplementing the conventional partial-identification sensitivity analysis (Oster bounds). The policy implication is that capex-grant programmes such as the EU Innovation Fund should incorporate demonstrable pre-FID offtake-commitment eligibility requirements, jointly addressing the financing-constraint friction (F4, the IF's current target) and the counterparty-risk friction (F7, the binding friction the IF currently leaves unaddressed).

### JEL classification (use MPRA built-in picker)

D81, G31, Q42, Q48

### MPRA subject classification breakdown

D - Microeconomics > D8 - Information, Knowledge, and Uncertainty; D81 - Criteria for Decision-Making under Risk and Uncertainty; G - Financial Economics > G3 - Corporate Finance and Governance > G31 - Capital Budgeting; Q - Energy > Q42 - Alternative Energy Sources

### Keywords (one per line)

- offtake commitment
- counterparty risk
- revenue volatility
- real options
- sectoral heterogeneity
- matching estimators
- Oster sensitivity
- clean hydrogen

### Language

English

### License

Creative Commons Attribution 4.0 International (CC-BY 4.0)

### Related URL

https://github.com/SakeSaak/thesis_h2/tree/main/09_papers/paper3_offtake_mechanism

### Date created

23 May 2026

---

## Paper 4

**PDF to upload**: `09_papers/paper4_real_options_theory/tex/paper4_main.pdf`

### Title

Dynamic Investment under Transition Uncertainty: A Five-Channel Policy Framework for Clean Technology

### Author

Saakstra, Sake (sole author)

Affiliation: Independent researcher, Amsterdam

Email: S.Saakstra@student.vu.nl

### Abstract

Clean-technology investment under policy-regime transition exhibits a structure that the canonical real-options framework of Dixit and Pindyck (1994) characterises only partially. We develop a dynamic-investment model in which an irreversible project decision is taken sequentially across four lifecycle stages (front-end design, final investment decision, construction, operations) under two sources of stochastic variation: the payoff-determining state variable (e.g.\ carbon price, technology cost) and the policy-regime credibility belief that determines whether the policy environment will persist over the investment horizon. The optimal cancellation policy is characterised by stage-dependent thresholds that respond to five comparative-statics channels: the expected-return channel (μ), the uncertainty channel (σ), the timing/option-value channel (ρ), the coordination channel (η), and the implementation-cost channel (κ). The policy-credibility extension delivers a formal proposition that the optimal threshold is monotonically decreasing in policy-credibility belief whenever the policy-conditional payoff exceeds the regime-reversal baseline.

The framework's primary contribution is methodological discipline: each of the five channels is matched to a pre-registered falsifiability criterion that specifies, in advance of empirical testing, both the observable implication and the numerical threshold at which the channel hypothesis would be rejected. This disciplinary structure addresses a long-standing concern in mechanism-based empirical research that mechanisms can be formulated ex-post to rationalise observed patterns. Eighteen mechanism predictions are catalogued, of which fourteen would be classified as confirmed, two as partial, and two as falsified against existing empirical evidence from related clean-hydrogen investment research. The two falsifications --- the EU Innovation Fund capex-grant null and the EU Carbon Border Adjustment Mechanism transitional-phase null --- are themselves substantive contributions to the literature on policy-design effectiveness, identifying which frictions are binding in the contemporary capital-abundant clean-technology environment.

The framework is sector-agnostic and applies to any clean-technology investment context with sufficient sample size, regime-transition observation, and project-level data on cancellation events. The implications for the design of clean-technology policy portfolios are explicit: multi-friction-addressing instruments dominate single-friction high-magnitude instruments; credibility-anchoring instruments substitute for direct payoff transfers; and capex-grant instruments without offtake-commitment requirements are predicted to fail under the prevailing F4-non-binding contemporary environment.

### JEL classification (use MPRA built-in picker)

D81, D92, G31, Q42, Q48, Q55

### MPRA subject classification breakdown

D - Microeconomics > D8 - Information, Knowledge, and Uncertainty; D81 - Criteria for Decision-Making under Risk and Uncertainty; D92 - Intertemporal Firm Choice; G - Financial Economics > G3 > G31 - Capital Budgeting; Q - Energy > Q4 > Q42 - Alternative Energy Sources

### Keywords (one per line)

- real options
- irreversible investment
- policy uncertainty
- transition risk
- mechanism design
- clean technology
- pre-registered falsifiability
- comparative statics

### Language

English

### License

Creative Commons Attribution 4.0 International (CC-BY 4.0)

### Related URL

https://github.com/SakeSaak/thesis_h2/tree/main/09_papers/paper4_real_options_theory

### Date created

23 May 2026

---
