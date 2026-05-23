# Submission metadata — SSRN and MPRA upload packages

This folder contains upload-ready metadata for the four standalone companion
papers (Papers 1–4), formatted for submission to two academic preprint
servers: SSRN (Social Science Research Network) and MPRA (Munich Personal
RePEc Archive).

The bridging thesis (159 pages) is not submitted to either platform — it
remains available exclusively via the Zenodo DOI deposit. The Executive
Summary and ETS2 Policy Brief are also not submitted to either platform;
they are distributed directly through GitHub and via DOI.

## Files in this folder

- `SSRN_submissions.md` — submission packages for SSRN, four papers
- `MPRA_submissions.md` — submission packages for MPRA, four papers
- `README.md` — this file

## How to use

For each paper, both files contain a self-contained block with all
fields the platform requires:

- Title (plain text, no LaTeX)
- Author and affiliation
- Abstract (cleaned of LaTeX citation commands)
- JEL classification codes (RePEc format)
- Keywords (comma-separated)
- Recommended platform-specific categories
- Suggested citation in BibTeX
- Date written

Upload procedure for each paper:

1. Open the platform's "submit new paper" page
2. Copy each field from the corresponding block in this file
3. Upload the PDF from `09_papers/<paper_name>/tex/<paper_name>_main.pdf`
4. Submit

After successful submission to MPRA, the paper receives an MPRA Paper No.
and is automatically indexed in RePEc, IDEAS, and EconPapers (typically
within 24–48 hours of editorial approval). SSRN provides immediate
visibility under its own index plus Google Scholar.

## Submission order — recommended

In order of expected citation impact and identification strength:

1. **Paper 3** (Offtake mechanism) — strongest empirical contribution
   (Oster δ_null = 20.23); most likely to attract citations
2. **Paper 2** (Carrot DiD) — multi-jurisdictional novelty; strongest
   policy relevance
3. **Paper 1** (TVP methodology) — methodological contribution; Tinbergen-
   tradition academic visibility through RePEc indexing
4. **Paper 4** (Real-options theory) — theoretical framework;
   supplementary positioning

The same paper can be uploaded to both SSRN and MPRA in parallel. Neither
platform requires exclusivity, and both explicitly accept previously-archived
research as long as a DOI link is provided.

## After submission

Once each paper has its SSRN URL and MPRA Paper No. available:

1. Update README badges to include SSRN and MPRA reference links
2. Update CITATION.cff with additional `repository-artifact` or
   `repository-code` entries pointing to the SSRN and MPRA versions
3. Mention the SSRN/MPRA references in the bibliography of related work
   submitted to other venues

Both platforms record citation counts automatically and feed into the
author's RePEc/IDEAS profile (MPRA) and SSRN author rankings (SSRN).
