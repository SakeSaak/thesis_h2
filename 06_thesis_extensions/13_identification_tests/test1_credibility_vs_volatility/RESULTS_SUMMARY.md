# Test 1 — Policy Credibility (π) Joint Identification with Volatility (σ): Results Summary

**Date**: 22 May 2026
**Sample**: 2.989 Blue+Green projects (272 Blue, 2.717 Green), 1.000 failure events, with non-missing monthly π/σ proxies.

## Question
Can policy credibility (π) be empirically distinguished from general volatility (σ) as the driver of the Blue-Green carbon-conditional cancellation differential? This is the central identification question behind Proposition 1 of Chapter 3.6 and Proposition 7 of Paper 4 §6 (credibility-conditional threshold).

## Method
Pooled logit event model with Blue × π and Blue × σ interactions. Each project assigned the proxy values of its announcement month (year, month merged from master_panel_monthly.csv).

**Proxies**:
- π_t: BBD US Economic Policy Uncertainty index (text-based policy-specific uncertainty)
- σ_t (general): VIXCLS (overall market volatility)
- σ_t (carbon-specific): EWMA volatility of EUA carbon returns (Dixit-Pindyck-relevant)

Diagnostic battery: Wald test of joint loading significance, Wald test of loading equality, VIF for multicollinearity, single-channel benchmark models.

## Results

### Diagnostic 1 — Proxy correlations
| | π | σ (general) | σ (carbon) |
|---|---|---|---|
| π | 1.00 | 0.37 | -0.34 |
| σ (general) | 0.37 | 1.00 | -0.27 |
| σ (carbon) | -0.34 | -0.27 | 1.00 |

Correlations are **moderate, not high** — there is no multicollinearity problem at the proxy level.

### Diagnostic 2 — Variance Inflation Factors (multicollinearity)
All VIFs are 1.2-2.3 (well below the 5.0 problem threshold). **Multicollinearity is not the issue.**

### Diagnostic 3 — Interaction coefficients
| Model | Blue × π coef | SE | p | Blue × σ coef | SE | p |
|---|---|---|---|---|---|---|
| Model A (σ general) | +0.039 | 0.182 | 0.83 | -0.043 | 0.183 | 0.81 |
| Model B (σ carbon) | +0.006 | 0.155 | 0.97 | +0.089 | 0.349 | 0.80 |

**ALL Blue × proxy interaction coefficients are non-significant (p > 0.79).**

### Diagnostic 4 — Joint Wald tests
| Test | Wald χ² | df | p | Conclusion |
|---|---|---|---|---|
| (Blue × π) AND (Blue × σ_general) = 0 | 0.07 | 2 | 0.964 | **Cannot reject joint null** |
| (Blue × π) = (Blue × σ_general) | 0.07 | 1 | 0.787 | Loadings indistinguishable |
| (Blue × π) AND (Blue × σ_carbon) = 0 | 0.07 | 2 | 0.965 | **Cannot reject joint null** |
| (Blue × π) = (Blue × σ_carbon) | 0.04 | 1 | 0.836 | Loadings indistinguishable |

### Diagnostic 5 — Single-channel benchmark models
| Model | ΔLL vs base | ΔAIC | LR-stat | p |
|---|---|---|---|---|
| Add π (BBD EPU) alone | +2.4 | −0.83 | 4.83 | 0.090 |
| Add σ (VIX general) alone | +140.8 | **−277.67** | 281.67 | <0.0001 |
| Add σ (EUA carbon EWMA) alone | +30.6 | **−57.20** | 61.20 | <0.0001 |

σ has a **massively dominant direct effect**; π has a weak marginal effect.

## Interpretation

**Three substantive findings:**

1. **π and σ are NOT empirically separable in this design.** The joint Wald tests cannot reject the hypothesis that both interaction coefficients are zero (p = 0.96-0.97). The loadings cannot be statistically distinguished from each other (p = 0.79-0.84). This holds for both general-volatility (VIX) and carbon-specific (EUA EWMA) σ proxies.

2. **The failure is NOT due to multicollinearity.** Proxy correlations are moderate (0.27-0.37) and VIFs are all below 2.5. The issue is fundamental: at the project-level cross-section, π and σ proxies do not generate distinguishable signals in the Blue-carbon-conditional event hazard.

3. **σ dominates as a direct effect; π is marginal.** Single-channel benchmark models show σ (both general and carbon-specific) generates an enormous improvement in fit (ΔAIC −58 to −278), while π is only marginally significant (ΔAIC −0.8, p = 0.09). This is consistent with Test 2's finding that the η-proxy (coordination) and σ-proxy show the strongest effects, while μ-proxy (which would map to π-like mechanisms) shows the weakest.

## Implications for the thesis and papers

**Proposition 1 (Chapter 3.6) and Proposition 7 (Paper 4 §6) must be softened.** The formal statement `∂z*/∂π < 0` cannot be empirically defended in this design. Recommended reformulation:

> "Policy credibility π is treated as an interpretive lens for the temporal pattern of β_int(t) detected in Chapter 7's TVP analysis, **not as a structurally identifiable parameter distinct from σ or expectations dynamics**. Joint identification of π and σ in the project-level event hazard cannot be achieved (Test 1, this section): the BBD-EPU-proxied policy uncertainty and EWMA-volatility-proxied σ both show statistically indistinguishable Blue × proxy loadings, consistent with the observation that observational data on irreversible investment decisions does not contain exogenous variation in only π."

**This is a NEGATIVE identification finding that strengthens the Chapter 10 "scientific value of negative findings" narrative.** The TVP β_int(t) intensification documented in Chapter 7 / Paper 1 remains a robust empirical fact. What this Test 1 result tells us is that the *interpretation* of that intensification through any single channel (π versus σ versus expectations) cannot be empirically privileged. Multiple interpretations are observationally equivalent.

**Combined with Test 2 (offtake decomposition)**, the picture is now consistent: mechanism orthogonality is a theoretical organising principle but not an empirical identification claim. This is exactly what the reviewer warned against, and we now have empirical evidence to support that warning rather than mere theoretical concession.

## Caveats

- This is a pooled logit, not a full bivariate state-space. A full bivariate GAS extension might detect joint identification through dynamic loadings (the proxies move differently over time and could load differently on the score). Test 1 with the project-level approach is the practical and tractable version.
- BBD EPU is a proxy; a more targeted Climate-Policy-Uncertainty (CPU, Berestycki et al.) or Energy-Environmental Policy Uncertainty (EEPU, Gavriilidis) index might generate more identifying variation. We tested only the BBD EPU here.
- Sample of Blue projects (n = 272) is small; with n_blue = 67-70 per stratum (Test 2 result for μ/σ/η-proxies), power for detecting cross-channel differences is limited.

## Files
- `01_test1_pi_sigma_joint_identification.py`: main analysis script
- `test1_results_summary.csv`: key diagnostic results
- `test1_pi_sigma_diagnostic.pdf` + `.png`: time-series + coefficient plots
