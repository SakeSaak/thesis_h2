# Concept-mail aan supervisor — response op feedback v2.2

**Status**: Concept, ter review door Sake voor verzending.
**Datum**: 22 mei 2026
**Aanleiding**: Reviewer-feedback (twee rondes, geconsolideerd) op v2.2 over mechanism-orthogonality, π vs σ separability, en scope-discipline.

---

**Onderwerp**: Identification-robustheid v2.3 — verwerking feedback op v2.2

Beste prof. Koopman,

Bedankt voor de scherpe feedback op v2.2. Twee punten in het bijzonder hebben mij aan het werk gezet: (i) de zorg dat policy-credibility π en general volatility σ niet structureel scheidbaar zijn in onze observationele data, en (ii) de mechanism-orthogonality-zorg over de offtake-decompositie in Paper 3. Ik heb deze beide methodologisch geadresseerd in v2.3.

Concreet zijn drie formele identification-tests uitgevoerd in een nieuwe Appendix A.14, met onafhankelijke identification-strategieën:

1. **Test 1 (pooled cross-section)**: gepoolde logit met continue Baker-Bloom-Davis EPU-proxy en EWMA-volatility-proxy. Resultaat: joint Wald test van (Blue × π, Blue × σ) = 0 geeft p = 0,96; loading-equality test cannot reject equality (p = 0,79–0,84). Multicollineariteit is uitgesloten (VIF 1,2–1,3). Conclusie: π en σ zijn niet apart identificeerbaar in de cross-section.

2. **Test 2 (channel-stratified offtake decomposition)**: stratificatie op end-use sector als channel-proxy (μ via chemical/refinery, σ via power/heat, η via transport/gas-grid). Resultaat: offtake-effect significant in alle drie strata, sterkste in η-proxy (OR=0,21), niet σ-proxy. LR-test van heterogeneity p = 0,19 — kanalen zijn empirisch indistinguishable. Bevestigt uw zorg over multi-channel co-operation empirisch.

3. **Test 3 (event-study met exogene shocks)**: vier events (EU Green Deal, COVID, Ukraine-invasie, IRA-passage) als π-pure en σ-pure shocks. Resultaat: alleen IRA-effect significant (p = 0,05), maar beter te interpreteren als μ-channel (45Q-subsidie) dan als π-channel; combined π-vs-σ test p = 0,96. Placebo-test schoon (p = 0,66).

De drie tests convergeren: structurele separatie van π en σ kan in deze observationele data niet worden bereikt. Dit is uiteraard precies wat u voorvoelde, maar de empirische bevestiging maakt het methodologisch tot een vinding in plaats van een concessie.

In v2.3 zijn de implicaties als volgt verwerkt:

- **Propositions 1 (Ch 3.6) en 7 (Paper 4 §6)** behouden hun theoretische status onder de modelaannames, maar krijgen een expliciete methodological note die verwijst naar A.14 en de directe causale interpretatie als interpretive layer markeert, niet als geïdentificeerde claim.
- **Chapter 3.7 en Appendix A.13** krijgen een framing-paragraph die de mechanism taxonomy als theoretisch-organising labelt, niet als empirisch-separable.
- **Paper 3** krijgt een methodological-discipline paragraph in de framework-sectie die de σ-channel claim softer maakt tot "dominant interpretation, not unique identification".
- **Chapter 10** krijgt een nieuwe subsection (§4.4) over de identification tests, geframed binnen het bestaande "scientific value of negative findings"-narratief van het hoofdstuk.

Daarnaast levert Test 3 één bijvangst die in **Paper 2** is verwerkt: het IRA event-effect (β = –0,75, p = 0,05) is direct evidence voor μ-channel operation van het 45Q production-tax-credit, en dient als event-study-corroboratie van de principale 45Q DiD-estimate via een identification-design dat niet op non-US controls steunt. Paper 2 §7.10 documenteert dit.

Het future-research-agenda is mede daarmee scherper geworden: een full structural-identification studie zou exogene variatie nodig hebben in alleen π (RDD rond grondwettelijke carbon-budget-amendments, election-driven climate-policy reversals) of in alleen σ (well-identified pandemic/oorlog shocks in jurisdicties met stabiele climate-policy regimes). Dit is geïdentificeerd als standalone publicatietarget in de discussion.

De huidige v2.3-PDF is beschikbaar in de repository (`00_paper/thesis_v1/thesis_main.pdf`), de papers eveneens. Implementation scripts, output-tabellen en de drie RESULTS_SUMMARY.md documents van de tests staan onder `06_thesis_extensions/13_identification_tests/`. Ik laat u graag aanvullende toelichting geven waar gewenst.

Met vriendelijke groet,
Sake Saakstra
