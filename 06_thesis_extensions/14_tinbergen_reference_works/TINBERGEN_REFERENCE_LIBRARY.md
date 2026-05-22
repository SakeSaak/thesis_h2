# Tinbergen Institute reference library

**Purpose**: Curated reference list of Tinbergen Institute (TI) research that directly relates to the methodological and substantive positioning of this thesis. Compiled to provide concrete benchmarks of what "Tinbergen-tradition" econometric work looks like — the style and discipline against which the present work will be evaluated and to which the thesis explicitly aligns itself.

**Compiled**: 22 May 2026 by Claude (with current web search), reviewed by SS.

**How to use**: For each category below, the references are listed in order of direct relevance to the thesis. The "Relevance" note specifies exactly which thesis chapter / paper benefits from citing or aligning with the reference. The "Stylistic lesson" notes (selected references) flag specific writing or methodological choices worth emulating.

---

## Part 1 — TVP / score-driven / state-space methodology (Paper 1 territory)

This is the canonical literature underlying Paper 1's GAS methodology. Most of these are by Koopman or his close collaborators (Blasques, Lucas, Gorgi, Creal). Sake's Paper 1 should cite the foundational entries and position itself explicitly relative to the most recent extensions.

### Foundational canon

**Creal, Koopman, Lucas (2013)**. *Generalized Autoregressive Score Models with Applications*. *Journal of Applied Econometrics*. (Original TI Discussion Paper 08-108/4, 2008.)
- **Relevance**: The founding paper of GAS models. Paper 1 is methodologically a direct extension; this paper is the primary methodological citation.
- **Stylistic lesson**: The paper introduces a unifying framework (score-driven updating) and then demonstrates it covers GARCH, ACD, ACI, and SSM as special cases — substantial generalisation argument before the empirical application. Paper 1's positioning relative to constant-parameter and parameter-driven alternatives mirrors this structure.

**Blasques, Koopman, Lucas (2012, TI 12-059/2)**. *Stationarity and Ergodicity of Univariate Generalized Autoregressive Score Processes*.
- **Relevance**: Establishes the theoretical conditions under which GAS specifications are well-behaved. Paper 1 should cite for the stationarity argument behind its parameter restrictions.

**Blasques, van Brummelen, Koopman, Lucas (2022)**. *Maximum likelihood estimation for score-driven models*. *Journal of Econometrics*, 227(2):325–346.
- **Relevance**: The asymptotic theory for ML estimation of GAS models. Paper 1's confidence intervals and inference statements rest on this result.

### Recent extensions (last 3 years)

**Blasques, Koopman, Nientker (2022)**. *A time-varying parameter model for local explosions*. *Journal of Econometrics*, 227(1):65–84.
- **Relevance**: Closest methodological cousin to Paper 1's structural-break-detection finding around 2020. Sake's β_int(t) discontinuity is an empirical analogue to the "local explosion" phenomenon this paper formalises. Strong candidate for a citation explicitly positioning Paper 1's finding.

**Creal, Koopman, Lucas, Zamojski (2024)**. *Observation-driven filtering of time-varying parameters using moment conditions*. *Journal of Econometrics*, 238(2).
- **Relevance**: Latest Koopman methodological paper (2024). Worth a discussion citation in Paper 1's literature section to demonstrate awareness of current frontier.

**Blasques, Gorgi, Koopman, Stegehuis (2024, TI 24-066/III)**. *Mitigating Estimation Risk: A Data-Driven Fusion of Experimental and Observational Data*.
- **Relevance**: ★ Directly relevant for Chapter 10 of the thesis. Addresses exactly the issue Sake's identification battery raises — how to use observational data well when experimental variation is not available. Strong candidate for a Chapter 10 / Appendix A.14 citation that legitimates the framing "observational data with explicit identification accounting" as a recognised methodological programme.
- **Stylistic lesson**: The title itself is worth noting — "Mitigating Estimation Risk" frames the contribution as risk-management of identification limits, not as a triumphant identification claim. That framing is congruent with Sake's "disciplined interpretive layer" approach.

**Blasques, Harvey, Koopman, Lucas (2023)**. *Time-Varying Parameters in Econometrics: The editor's foreword*. *Journal of Econometrics*, 237(2):1–3.
- **Relevance**: Editorial framing of where TVP econometrics is currently going. Paper 1's contribution can be positioned explicitly within this editorial vision.

**Harlaar, Commandeur, van den Brakel, Koopman, Bos, Bijleveld (2024, TI 24-037/III)**. *Statistical Early Warning Models with Applications*.
- **Relevance**: Application of state-space methodology to early-warning detection in administrative data. Methodologically parallel to Paper 1's structural-break-detection task in sparse-event survival.

**Schiavoni, Koopman, Palm, Smeekes, van den Brakel (2021)**. *Time-varying state correlations in state space models and their estimation via indirect inference*. (SSRN/Tinbergen)
- **Relevance**: Methodological precedent for time-varying parameters that capture regime change in survey-administrative-data integration. Sake's β_int(t) detection has the same epistemological character: a state-space parameter that captures structural rather than gradual change.

**Bram van Os (2023, TI 23-037/III)**. *Information-Theoretic Time-Varying Density Modeling*.
- **Relevance**: Recent VU/Tinbergen PhD-level work on TVP density modelling. Methodological direct neighbour to Paper 1; worth examining the writing style and identification-framing.

**Lange, van Dijk (2024–2025)**. *Implicit score-driven filters for time-varying parameter models*.
- **Relevance**: Featured on the Tinbergen homepage as a current research highlight. Recent extension of GAS to implicit (rather than explicit) score-driven updating. Worth tracking for Paper 1 revision rounds.

---

## Part 2 — Climate / transition risk / energy economics (Chapter 1-2 + Paper 2 territory)

These are the Tinbergen-tradition climate and energy economics references that anchor the thesis's substantive positioning. They are particularly valuable because they show how Tinbergen scholars frame climate / energy questions in a way that survives Tinbergen-style scrutiny — careful claims, explicit identification, no over-reaching.

**Loyson, Luijendijk, van Wijnbergen (2023, TI 23-041/IV)**. *The pricing of climate transition risk in Europe's equity market*.
- **Relevance**: ★ The single most directly relevant TI climate paper for the thesis. Frames transition risk as an asset-pricing phenomenon, exactly the macroeconomic-financial counterpart to Sake's project-level investment-risk perspective. Citation in Chapter 1 introduction and Chapter 2 literature review establishes the Tinbergen-tradition framing of "transition risk" that the thesis adopts.
- **Stylistic lesson**: Notice how the paper does not claim to identify "climate risk" as a structural causal factor; it identifies a pricing pattern consistent with transition-risk-aware investors. This is exactly the careful identification stance the supervisor advocates.

**Olijslagers, van der Ploeg, van Wijnbergen (2021, TI 21-045/VI)**. *On current and future carbon prices in a risky world*.
- **Relevance**: Carbon-price uncertainty and its implications for investment / pricing. Direct support for the thesis's treatment of σ (payoff volatility) and π (regime credibility) as both economically and empirically meaningful.

**van Wijnbergen, Willems (2012)**. *Optimal Learning on Climate Change: Why Climate Skeptics should reduce Emissions*. TI 2012-085.
- **Relevance**: Classic Tinbergen result on climate-uncertainty + irreversibility. Methodologically a real-options + learning argument; conceptually the foundation for the "transition uncertainty drives implementation risk" framing of the thesis.
- **Stylistic lesson**: A short, sharp paper that delivers one substantive result with full identification discipline. Worth re-reading for Paper 4's exposition style.

**Bremer, den Nijs, de Groot (2023, TI 23-043/VII)**. *The energy efficiency gap and barriers to investments*.
- **Relevance**: Tinbergen treatment of barriers-to-investment in the Dutch energy context. Methodologically the closest TI parallel to Sake's project-level investment-decision data (different sector, similar question structure).

---

## Part 3 — Identification methodology + observational-causal inference (Chapter 10 + Appendix A.12/A.14 territory)

The Tinbergen tradition has explicit ties to the Imbens-Athey programme on causal inference in observational settings. This is exactly where Sake's identification discipline should be positioned.

**Imbens Tinbergen Course (2018)**. *Causal Inference and Machine Learning*.
- **Relevance**: Imbens (Nobel 2021) gave the Tinbergen course on this topic. The thesis's identification hierarchy, observational-data-with-explicit-limits framing, and integration of multiple identification strategies is squarely within the Imbens-tradition methodology that Tinbergen formally teaches.

**Athey, Chetty, Imbens, Kang (2016)**. *Estimating Treatment Effects using Multiple Surrogates: The Role of the Surrogate Score and the Surrogate Index*.
- **Relevance**: Methodological precedent for using surrogate / proxy variables when direct measurement is not feasible. Direct support for the thesis's use of BBD-EPU, VIX, EUA-EWMA as proxies for π and σ respectively. Cite in Appendix A.14 as theoretical foundation for the proxy-based identification approach.

**Heckman, Urzua (2010)**. *Comparing IV with structural models: What simple IV can and cannot identify*. *Journal of Econometrics* 156.1.
- **Relevance**: Foundational reading on the limits of IV-style identification in observational settings. Directly informs the thesis's framing of Test 3 (event-study with exogenous shocks) as corroborative rather than structurally causally identified.

**Deaton, Cartwright (2018)**. *Understanding and misunderstanding randomized controlled trials*. *Social Science & Medicine*.
- **Relevance**: Critique of RCT-supremacy that legitimates careful observational designs. Direct support for the thesis's epistemological positioning of observational identification limits as substantive findings, not deficiencies.

---

## Part 4 — Real-options + investment under uncertainty (Paper 4 territory)

The real-options literature is well-developed outside Tinbergen too (Dixit-Pindyck, McDonald-Siegel, etc.), so the Tinbergen-specific connections are sparser. The relevant TI work is:

**Jacobs (2007)**. *Real Options and Human Capital Investment*. (TI affiliated, Erasmus/CESifo.)
- **Relevance**: A TI-affiliated real-options application. Methodologically transferable: irreversibility + option value + heterogeneous returns; mathematically isomorphic to Sake's Blue-vs-Green choice framework with technology-specific implementation thresholds.

**van Wijnbergen, Willems (2012)** (see Part 2 above). The Tinbergen-tradition treatment of irreversibility + learning under uncertainty.

---

## Part 5 — Stylistic lessons from the Tinbergen-tradition

A pattern that emerges from reading these references closely:

**Claims are calibrated to identification status.** Tinbergen-tradition papers rarely claim "we have identified X" without explicit discussion of what identifies X and what doesn't. Sake's "disciplined interpretive layer" framing for Proposition 1 / 7 is exactly this calibration.

**Methodology + application together.** The best TI papers are not pure methodology papers nor pure applications — they are both, with the methodology motivated by a real empirical question and the application sharpened by the methodological discipline. Paper 1 is positioned correctly: TVP methodology with sparse-event survival application.

**Negative findings are reported as findings.** The van Wijnbergen-Willems (2012) result that "uncertainty is no reason for inaction" is a negative-in-form, substantive-in-content finding. The Blasques-Gorgi-Koopman-Stegehuis (2024) "Mitigating Estimation Risk" framing is precisely the same epistemic move. The thesis Chapter 10 framing of regime instability as a substantive contribution belongs in this tradition.

**Multiple specifications, not single robust standard errors.** TI-style robustness reporting is via multiple specifications (Sun-Abraham + BJS-imputation + IPWRA + Honest DiD, as in Paper 2). The convergence of multiple identification strategies, not the robustness of one, carries the credibility.

**Theoretical organisation is praised; over-claiming is punished.** Theoretical frameworks (μ/σ/ρ/η/κ channels, sequential staging, real-options threshold) are valued as organising tools. Claims that those frameworks are empirically structurally identified in observational data without exogenous variation are penalised. The supervisor's "observationally entangled" terminology is the explicit verbal marker of this distinction.

---

## Next steps for citation integration

If the goal is to strengthen the Tinbergen-tradition positioning of the thesis (which is consistent with the supervisor's PhD-traject framing), the priority additions to the bibliography are:

1. **Blasques, Gorgi, Koopman, Stegehuis (2024)** in Chapter 10 + Appendix A.14 — strongest single citation for the "observational identification with explicit risk-accounting" methodological programme.
2. **Blasques, Koopman, Nientker (2022)** in Paper 1 — closest methodological analogue to the β_int(t) structural-break finding.
3. **Creal, Koopman, Lucas, Zamojski (2024)** in Paper 1's literature section — demonstrates awareness of current GAS frontier.
4. **Loyson, Luijendijk, van Wijnbergen (2023)** in Chapter 1 + Chapter 2 — anchors the transition-risk framing in the Tinbergen-tradition.
5. **van Wijnbergen, Willems (2012)** in Chapter 3 + Paper 4 — historical Tinbergen-tradition reference for the uncertainty + irreversibility argument that Paper 4 develops further.

These five additions would establish the thesis's positioning within the Tinbergen-tradition explicitly and credibly without requiring substantive content changes.

---

*Last updated: 22 May 2026*
