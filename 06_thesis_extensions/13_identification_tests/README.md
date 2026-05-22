# Identification Tests — addressing reviewer feedback on mechanism separation

**Started**: 22 May 2026
**Trigger**: Reviewer feedback on (1) policy credibility π not separately identified from σ; (2) mechanism orthogonality risk (offtake works through μ + σ + η simultaneously); (3) overall identification hierarchy in observational data.
**Strategic choice**: User-decided to run identification tests despite reviewer's "no more broadening" advice, to obtain robustness for current claims (Proposition 1 in Ch 3.6, Proposition 7 in Paper 4 §6, σ-channel identification in Paper 3).

## Tests

### Test 1: Policy credibility (π) separately identified from σ
**Folder**: `test1_credibility_vs_volatility/`
**Approach**: Bivariate score-driven state-space with EPU/EEPU/CPU as exogenous π proxy, joint MLE with σ-component (EWMA-style on hazard residuals).
**Pre-conditions**:
- External proxy data: Baker-Bloom-Davis EPU, Gavriilidis EEPU, or Berestycki CPU
- Computation: extend M3 GAS specification to bivariate; ~500 line script
**Realistic outcome distribution**:
- 40% identification succeeds → Proposition 1 verdedigbaar
- 30% identification fails → claim must be downscaled
- 30% inconclusive (high parameter correlation) → mixed signal

### Test 2: Offtake mechanism decomposition (μ vs σ vs η)
**Folder**: `test2_offtake_decomposition/`
**Approach**: Stratify offtake-committed projects by contract type (fixed-price → μ; indexed → σ; multi-counterparty → η). Re-estimate IPWRA per stratum.
**Pre-conditions**:
- S&P metadata must contain offtake-contract-type information (TO BE CHECKED — feasibility-gate)
- If not directly in S&P: proxy via offtaker industry + tenure
**Realistic outcome distribution**:
- 40% sub-samples sufficient + heterogeneity detected → σ-channel claim strengthened
- 30% sub-samples too small → inconclusive
- 30% uniform effects → multi-channel co-operation confirmed, claim softened

### Test 3: Instrumental variables / sharp identification
**Folder**: `test3_instrumental_variables/`
**Approach**: Regression discontinuity around IRA-passage week for 45Q (μ-channel sharp); cross-jurisdictional spillover instrument for η-channel.
**Pre-conditions**:
- IRA passage week: 16 August 2022
- 30-60 projects in narrow window (90 days)
- Cross-jurisdictional infrastructure data
**Realistic outcome distribution**: lowest expected payoff; high risk of inconclusive
- 30% RD significant
- 50% inconclusive (sample too small)
- 20% RD null

## Execution order
1. **Test 2 feasibility check** (1 sessie) — fastest go/no-go decision
2. **Test 1 setup + external data acquisition** (1 sessie parallel)
3. **Test 2 stratified analyses** (2-3 sessies, conditional on feasibility)
4. **Test 1 bivariate state-space** (3-4 sessies)
5. **Test 3 RD analysis** (2-3 sessies, lowest priority)

## What goes back into the thesis
- Test results → new section in Chapter 10 ("Identification robustness tests")
- Successful tests → strengthen specific claims in Chapter 7, Paper 3, Paper 4 §6
- Failed/inconclusive tests → bolster the methodological-discipline narrative in Chapter 10 ("scientific value of negative identification findings")
