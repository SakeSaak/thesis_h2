# Thesis v1 — Manuscript draft for reviewer feedback

**Status**: Complete draft, ready for first external review (21 May 2026)
**Word count**: ~22,450 words across 13 chapters + abstract
**Compilation**:

```bash
cd 00_paper/thesis_v1
pdflatex thesis_main
bibtex thesis_main
pdflatex thesis_main
pdflatex thesis_main
```

## Chapter status

| # | Chapter | Words | Status |
|---|---|---|---|
| — | Abstract | 331 | ✅ Draft |
| 1 | Introduction | 868 | ✅ Draft |
| 2 | Literature Review | 1,204 | ✅ Draft |
| 3 | Theoretical Framework (Real Options) | 2,569 | ✅ From earlier work |
| 4 | Data | 2,880 | ✅ From earlier work |
| 5 | Methodology | 1,553 | ✅ Draft |
| 6 | Results I: Carrot-Policy DiD | 1,527 | ✅ Draft |
| 7 | Results II: TVP State-Space | 6,766 | ✅ From earlier work |
| 8 | Results III: Offtake Mechanism | 1,309 | ✅ Draft |
| 9 | Counterfactual Scenarios | 1,297 | ✅ Draft |
| 10 | Discussion | 1,379 | ✅ Draft |
| 11 | Conclusion | 595 | ✅ Draft |
| A | Appendix | 165 | 🟡 Skeleton (to populate from `06_thesis_extensions/`) |

## To do before final submission

- [ ] Populate appendix sections with detailed case-studies + additional tables
- [ ] Verify all empirical numbers against latest pijler output CSVs
- [ ] Add figures (currently text-only) from `06_thesis_extensions/*/figures/`
- [ ] Cross-check chapter labels (`\label{ch:...}`) match `\ref{}` calls in main file
- [ ] Update industry-source citations (decarbonizeweekly, ing, bucklebridge) with verified URLs
- [ ] Final pass on consistency of notation across chapters
