# Paper 1 — TVP state-space methodology for sparse-event hazard models
## Score-driven specification, OOS-optimal performance, and a Diebold-Mariano test

**Target**: Journal of Applied Econometrics
**Authors**: Sake Saakstra (VU Amsterdam), Siem Jan Koopman (VU Amsterdam) [TBC]
**Status**: Outline + abstract + introduction drafted (May 2026)

---

## Working title
"A time-varying-parameter state-space approach to sparse-event survival modelling: 
methodological design, out-of-sample performance, and application to hydrogen project implementation-risk"

## Working abstract (~250 words target)

We propose a time-varying-parameter (TVP) state-space approach to survival modelling under sparse-event data conditions, in which the conditional hazard depends on a generative-process parameter whose evolution is driven by the score of the predictive likelihood. The Score-Driven Generalized Autoregressive Score (GAS) specification of Creal, Koopman, and Lucas (2013) provides a parsimonious and asymptotically optimal mechanism for time-variation in the parameter governing the hazard-conditioning relation, requiring only the score and a one-parameter persistence specification.

Three rival TVP specifications are compared: M1 with constant parameter, M2 with random-walk innovations, and M3 with GAS-driven persistence. The three are tested for out-of-sample forecast accuracy via rolling one-step-ahead prediction across the full sample, with significance assessed by the Diebold-Mariano-Harvey-Leybourne-Newbold test on per-observation log-loss. The Score-Driven specification M3 wins uniformly across three test designs (75-25 time split, 5-fold cross-validation, full-sample rolling), with the largest performance gain concentrated in the 2023 cancellation wave where the carbon-conditional mechanism intensifies.

The methodology is applied to a sample of 1,354 hydrogen projects spanning announcement-stage status from the S&P Global database (2010-2024), with a binary failure-status outcome aggregating cancellation, decommissioning, and on-hold transitions. The interaction coefficient $\beta_{\text{int}}(t)$ governing the carbon-conditional Blue/Green hazard differential is estimated to intensify from $-0.46$ in 2010 to $-1.49$ in 2024, with a structural break detected around 2020.

The Score-Driven TVP approach is a useful general-purpose methodology for survival modelling in domains with sparse-event data, sample-window dependence concerns, and reasonable suspicion of structural-break dynamics.

JEL classification: C32, C41, Q42
Keywords: time-varying parameter, score-driven, state-space, survival modelling, Diebold-Mariano test, hydrogen

## Outline

### 1. Introduction (3-4 pages)
- The general problem: survival modelling with sparse events and potentially time-varying conditioning
- Why TVP matters: structural-break detection, distinction between true effect and sample-window artefact
- Why Score-Driven over Random-Walk TVP: asymptotic optimality, parsimony, identification
- Contribution of this paper: rigorous methodological design + OOS validation + sparse-event application
- Roadmap

### 2. Related literature (2 pages)
- TVP econometrics: Cogley & Sargent (2005), Primiceri (2005), D'Agostino et al. (2013)
- Score-Driven models: Creal, Koopman, Lucas (2013), Harvey (2013)
- Survival with TVP: Pirisi & Pegoraro (2018), Hubbard & Cunningham (2024)
- Sparse-event survival: Sun (2006), Klein & Moeschberger (2003)
- Diebold-Mariano framework: DM (1995), HLN (1997), Hansen-Lunde-Nason MCS (2011)

### 3. Methodology (4-5 pages)
- 3.1 Model setup: $y_{it} \in \{0,1\}$ event indicator, $\beta_{\text{int}}(t)$ time-varying coefficient
- 3.2 Three specifications of $\beta_{\text{int}}(t)$:
  - M1: constant
  - M2: random-walk innovations
  - M3: Score-Driven (GAS)
- 3.3 Estimation: Bayesian state-space inference for M2 and M3; MCMC implementation details
- 3.4 OOS framework: time-split, 5-fold, rolling 1-step-ahead
- 3.5 DM test: standard DM, HLN small-sample correction, MCS at $\alpha = 0.10$

### 4. Data (1-2 pages)
- S&P Global hydrogen project database, 1,354 projects, 2010-2024
- Covariates: technology (Blue/Green), region, capacity, year-of-announcement
- Project-year panel construction
- Sample window robustness considerations

### 5. Results (4-5 pages)
- 5.1 TVP trajectory estimates per specification (M1/M2/M3)
- 5.2 OOS performance comparison: time-split, CV, rolling
- 5.3 Diebold-Mariano test results: M3 superior across all designs
- 5.4 Model Confidence Set at $\alpha = 0.10$: M3 unique winner
- 5.5 Concentration of M3 advantage in 2023 cancellation wave
- 5.6 Robustness across alternative window sizes and DF specifications

### 6. Discussion (2 pages)
- Interpretation of the TVP trajectory
- Structural-break detection and the 2020 carbon-pricing inflection
- Methodological lessons for survival modelling with sparse events
- Limitations: small-sample inference; identification of $\beta_{\text{int}}(t)$ at the boundary

### 7. Conclusion (1 page)

### Appendix
- Full MCMC convergence diagnostics
- DM test under alternative loss functions
- Specification of GAS recursion and prior structure
- Reproducibility note: scripts at `09_papers/paper1_tvp_methodology/`

---

## Writing strategy
- Use thesis sections as direct source material:
  - Thesis Ch. 7 (Results TVP State-Space) → Paper Section 5
  - Pijler 47 (Diebold-Mariano test, scripts 47 + 47b) → Paper Section 5.3-5.5
  - Pijler 48 (interval-censored timing) → Paper Section 6 (sensitivity / limitations)
  - Thesis Ch. 5 (Identification hierarchy, L4 sub-section) → Paper Section 3
- Goal: ~30 pages including references, target sub-180 days from outline to submission

## Key advantages over thesis chapter
- More detailed methodological exposition (5 pages instead of 1)
- Explicit Bayesian state-space algorithm (currently sketched in thesis Appendix)
- Standalone narrative not requiring thesis context
- Diebold-Mariano-only focus (no comparison to non-TVP DiD methods)
- Direct connection to JAE-style methodological-contribution paper format

## Next session targets (in priority order)
1. Draft Section 3 (Methodology) - 4-5 pages of formal exposition
2. Lift Section 5 (Results) directly from thesis Ch. 7 + Pijler 47, adapt to standalone format
3. Draft Introduction (Section 1) - 3-4 pages
4. Polish abstract; iterate with Koopman; identify gaps before drafting Sections 2, 4, 6
