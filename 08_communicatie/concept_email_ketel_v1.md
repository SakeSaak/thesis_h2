# Concept email naar dr. N. Ketel — versie 1

**Onderwerp:** Concept hoofdstuk causale identificatie via CBAM — verzoek om gerichte feedback

**Aan:** n.ketel@vu.nl

**CC:** s.j.koopman@vu.nl

**Bijlagen:**
- `chapter8_cbam_full.pdf` (24 pp, 8.7k woorden) — concept Chapter 8
- `chapter8_cbam_design.tex` → optioneel: oorspronkelijk research design memo (2.5k woorden)

---

Beste Nadine,

Bedankt nogmaals voor je bereidheid om mee te denken over mijn MSc-scriptie. Bij dezen zoals afgesproken het concept van het hoofdstuk waar ik je gerichte feedback over zou willen vragen. Het bouwt voort op de eerdere associationale bevindingen uit mijn scriptie (Blue × EUA interactie $\beta_{\text{int}}$ in het bereik $[-1.17, -1.88]$ over diverse specificaties), en exploiteert de CBAM definitieve fase-launch van 1 januari 2026 als sudden-shock voor causale identificatie. Het werk is begeleid door Siem Jan Koopman; ik zou hem graag CC houden in deze correspondentie.

**Wat het hoofdstuk doet.** Vier pre-registered identification strategies op drie onafhankelijke data sources:

- v7 sample (714 projecten, 43 cancellation events, manueel gecureerd uit eerdere S&P versie)
- S&P Global Hydrogen Master Data Table (3.343 projecten, dagelijks ververst, definitie B = 206 events na transparante exclusion van 84% On-hold-assumed)
- IEA Hydrogen Production Projects Database (2.625 projecten, jaarlijks, multi-checkbox end-use)

De vier strategies zijn (i) equity event study DiD met placebo-correctie, (ii) project-level vintage cohort DiD, (iii) EU-gerestricteerde placebo-rich DiD met vijf placebo treatment dates, en (iv) triple-difference EU × CBAM-end × Post. Alle vier geven informative nulls. Het centrale resultaat: een robust associationaal patroon (+17pp tot +20pp hogere cancellation in EU-CBAM-exposed projecten, gerepliceerd in zowel S&P als IEA), maar placebo-dates binnen de EU produceren coefficient estimates van gelijke of grotere magnitude dan de echte CBAM-dates (ratio 0.72), en de triple-difference levert $\beta_7 = +1.15$ met 95% CrI $[-1.48, +3.78]$.

**Wat ik specifiek aan jou wil voorleggen.** Vier concrete punten waar ik je oordeel het meest waardevol zou vinden:

1. **Treatment definitie keuze.** Ik gebruik drie geneste exposure definities (T1 narrow end-use, T2 broad geographic-OR-end-use, T3 strict intersection). T3 levert de cleanste cross-sectional identification op maar trekt het sample te smal voor robust DiD. Is mijn argumentatie hierover (Sectie 3.1) defendable? Zou je een alternative definitie aanbevelen?

2. **De EU-only placebo-rich design (Sectie 7).** Ik volg hier expliciet het sudden-shock framework van jou, Hanemaaijer en Marie (2024). Mijn vraag: is de placebo grid van vijf cutoffs (2015, 2017, 2019, 2020, 2021) voldoende voor robuste falsification, of zou je een dichtere/andere placebo strategie aanbevelen? De ratio 0.72 (placebos > reals) lijkt mij voldoende reden om de causale interpretatie te verwerpen, maar ik wil zekerheid dat ik dit goed lees.

3. **Power constraint.** Met 60 EU CBAM-exposed cancelled-projecten en MDE van ~11pp bij 80% power, kan ik effecten <11pp niet detecteren. Vier maanden post-definitive launch is een fundamentele beperking. Zou je een synthetic-controls aanpak (à la Abadie-Diamond-Hainmueller) aanbevelen voor een eventuele uitbreiding, of acht je het methodologisch sterker om de informative null te accepteren?

4. **Framing in jouw 2023 (un)importance-paper traditie.** Ik framing het hoofdstuk expliciet in de honest-null methodologie van jullie IZA 16591. Sectie 11.3 stelt dat de bijdrage ligt in het *bounden* van een eventueel causaal effect ($\sim$14pp bovengrens) en het transparant rapporteren van waarom we het niet kunnen identificeren. Vind je dit een passende framing, of zou je hier een ander argument zien?

Daarnaast horen we graag van je of er een tweede-lezer rol voor je in zou kunnen zitten — dit is voor de hoofdscriptie 18 EC. Als die rol niet past, ben ik ook al heel dankbaar voor jouw inhoudelijke commentaar op dit ene hoofdstuk.

**Praktisch.** Het hoofdstuk staat als PDF bijgevoegd (~24 pp). De LaTeX source en alle achterliggende empirische scripts kan ik je toesturen indien gewenst. Ik kan ook voorstellen om in week 21 of 22 een afspraak van 30-45 min te plannen waarin we het kunnen doorlopen, mocht dat handiger zijn dan schriftelijke feedback.

Hartelijk dank alvast voor je tijd.

Met vriendelijke groet,

Sake Saakstra
MSc Econometrics & Operations Research (Financial Track)
Vrije Universiteit Amsterdam
06-XX-XXX-XXXX
sake.saakstra@student.vu.nl
