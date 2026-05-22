# Test 2 — Offtake Mechanism Decomposition: Results Summary

**Date**: 22 May 2026
**Sample**: 2.098 Blue+Green projects with non-Unknown end-use sector, 680 failure events (cancelled / on-hold / decommissioned), 266 offtake-committed.

## Question
Does offtake-commitment work primarily through σ (uncertainty reduction) as Paper 3 claims, or does it operate through multiple channels simultaneously as the reviewer suggests?

## Method
Logit model of failure event on offtake-commitment × channel-proxy interaction, where channel proxies use primary end-use sector:
- **μ_proxy**: chemical feedstock + refinery feedstock (fixed-price contracts expected)
- **σ_proxy**: power & heat + industry (other) (indexed pricing expected)
- **η_proxy**: transport (road/shipping/aviation/rail) + gas grid (coordination expected)

Controls: log capacity, capex support indicator, region fixed effects, year announced, blue dummy.

## Results — Offtake effect per channel

| Channel | Sample n | Offtake-committed | Events | Offtake β | SE | p | Odds ratio |
|---|---|---|---|---|---|---|---|
| μ_proxy | 489 | 111 | 118 | **−0.848** | 0.306 | 0.006 | 0.43 |
| σ_proxy | 761 | 75 | 302 | **−1.006** | 0.304 | 0.001 | 0.37 |
| η_proxy | 848 | 80 | 260 | **−1.566** | 0.397 | <0.001 | 0.21 |

**LR test of offtake × channel heterogeneity**: LR = 1.736, df = 1, p = **0.188** → **cannot reject homogeneity at p<0.10**.

## Interpretation

**Three substantive findings:**

1. **Offtake effect is robustly negative across all three channels**. The general claim that pre-FID offtake commitments reduce cancellation hazard survives at every channel-stratified analysis. This is the central Paper 3 finding and it remains intact.

2. **Strongest effect is in η-proxy, not σ-proxy.** The η-channel (transport + gas grid, where coordination-network considerations dominate) shows a 79% reduction in failure odds, exceeding both σ (63%) and μ (57%). This contradicts the strict reading of Paper 3 that "σ is the dominant operating channel".

3. **The reviewer's concern is empirically confirmed.** The likelihood-ratio test of channel × offtake heterogeneity cannot reject the null of uniform effect. The three channel-effects are statistically indistinguishable. Offtake commitment empirically operates through **multiple co-operating channels** rather than a uniquely identified σ-channel.

## Implications for Paper 3

The claim "σ-channel uniquely identified by cross-sectoral heterogeneity" cannot be sustained in its strong form. Recommended re-framing:

- **Keep**: the central empirical finding (offtake commitment reduces cancellation hazard by ~70% on average), the multi-estimator robustness (5 estimators converging), the Oster bound ($\delta_{null} = 20.23$).
- **Soften**: the claim about σ-channel identification. The new framing should be:
  > "Pre-FID offtake commitments reduce cancellation hazard robustly across end-use sectors. While the theoretical motivation emphasises the σ-channel (uncertainty reduction via volatility-stabilising long-term contracts), the empirical test of channel-stratified heterogeneity cannot statistically discriminate between σ, μ, and η operating channels: all three show significant negative effects of similar magnitude. We therefore interpret offtake commitment as a **multi-channel intervention with empirically indistinguishable channel-specific contributions**, consistent with the theoretical taxonomy being interpretive and organising rather than empirically structurally separable."

## Implications for Chapter 3 (mechanism taxonomy)

This is direct empirical evidence for the reviewer's concern about mechanism orthogonality. The five-channel framework in Chapter 3 must be explicitly framed as **interpretive** rather than **empirically separable**.

## Companion finding: Blue × channel heterogeneity

A separate analysis of the Blue-Green hazard differential across channels finds a different pattern:

| Channel | Blue β | p | n_blue | Events |
|---|---|---|---|---|
| μ_proxy | +0.188 | 0.63 | 67 | 118 |
| σ_proxy | **+0.457** | **0.10** | 70 | 302 |
| η_proxy | +0.433 | 0.25 | 35 | 260 |

LR test of Blue × channel: LR = 2.900, p = **0.089** → marginally rejects homogeneity at p<0.10. The Blue-Green differential is concentrated in σ_proxy (consistent with the carbon-conditional payoff mechanism of Chapter 7), but small and non-significant in μ_proxy (chemical/refinery, where the fixed-price contracts insulate from carbon-volatility).

This is a **separate finding** from the offtake decomposition: the Blue-Green vulnerability appears σ-driven, but the offtake-protection appears η-driven. The two mechanisms are not the same.

## Limitations

- End-use sector is a proxy for contract type, not a direct measurement. A subset analysis using actual offtaker-identity industry confirms the pattern qualitatively but with weaker power (only 280 projects have named offtakers).
- Logit event model conflates timing of event with occurrence. A Cox proportional-hazards re-estimation is a natural robustness check.
- Sample is observational; the channel-effect estimates do not have a causal interpretation.

## Files
- `01_test2_main_decomposition.py`: descriptive analysis script
- `02_test2_offtake_decomposition.py`: main analysis script (this analysis)
- `event_rates_by_channel_tech.csv`: descriptive event-rate table
- `blue_green_gap_by_channel.csv`: Blue-Green gap per channel
- `offtake_by_channel_logit_results.csv`: main results table
- `test2_forest_plot.pdf` + `.png`: visualization
- `test2_analysis_sample.csv`: analysis sample (n=3097)
