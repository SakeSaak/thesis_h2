# Causaliteit Onderzoeken Zonder Forceren — Onderzoeksdesign
**Sake Saakstra | 18 mei 2026**

---

## 1. Principes: Hoe Maak Je Valuable Onderzoek Zonder Forced Findings

Voordat we strategieën bespreken: **vijf principes** die voorkomen dat we onbewust "in een richting drukken":

### Principe 1: Pre-registreer hypotheses
Voor elke causale strategie, **schrijf vooraf op**:
- Welke specificatie ga je schatten
- Welk teken voorspelt je hypothese
- Wat is je significance threshold
- Welke robustness checks doe je *standaard* (niet alleen als hoofdresultaat tegenvalt)

Open Science Framework (OSF) heeft hier formele tools voor. Vooraf je analysis plan publiceren maakt het onmogelijk om p-hacked findings te verkopen als robust.

### Principe 2: Rapporteer alle resultaten
Als je drie identification-strategieën doet, **rapporteer alle drie** — ook de niet-significante. "We tested X with three strategies; one showed significant effect, two did not" is **eerlijker en wetenschappelijker** dan alleen het significante resultaat presenteren.

### Principe 3: Triangulatie boven enkele identificatie
Eén causale strategie kan toevallig werken. **Drie verschillende strategieën die convergeren** is overtuigend bewijs. Drie strategieën die divergeren is **ook informatief**: het wijst op heterogeniteit of confounding.

### Principe 4: Verwelkom null results
Als causale identificatie geen effect laat zien, is dat **een wetenschappelijke vinding**, niet een teleurstelling:
- "We find robust associational evidence but no causal identification confirms it" → suggereert confounding mechanismen die zelf onderzoek waard zijn
- Een MSc thesis die "we cannot conclude causality" eerlijk rapporteert is **methodologisch sterker** dan een die forced significance claimt

### Principe 5: Onderscheid mechanism van causation
Een **mechanism claim** ("we documenteren hoe X met Y samenhangt onder verschillende condities") is wetenschappelijk waardevol zelfs zonder causale identificatie. Een PhD thesis kan exclusief mechanism documenteren mits dat rigoureus gebeurt.

---

## 2. Aanvullende Identification Strategieën (Buiten Vorige Lijst)

Naast IRA-DiD, Russia-Ukraine event study, IV via beleidstiming, synthetic control, en RD, **zes additionele strategieën** die we kunnen overwegen:

### Strategie 6: Within-Sponsor Comparison (Firm Fixed Effects)
**Idee:** Als sponsor X zowel een Blue project als een Green project aankondigde, vergelijk hun overleving **binnen die sponsor**. Dit elimineert alle sponsor-specifieke confounders (financieel sterkte, management kwaliteit, strategische committment).

**Design:**
- Filter op sponsors met ≥ 1 Blue én ≥ 1 Green project
- Schat hazard model met sponsor fixed effects
- Test of Blue×EUA interactie blijft significant binnen-sponsor

**Identificatie:** Eliminates sponsor-level unobserved heterogeneity. Resterende identificatie via temporele variatie binnen sponsor.

**Voor v7 data:** Realistisch — major energy companies (Shell, BP, TotalEnergies, RWE, Equinor) hebben zowel Blue als Green projecten in hun portfolio. Vermoedelijk ~30-50 sponsors met multiple project types.

### Strategie 7: Heterogeneous Treatment Effects
**Idee:** Onderzoek **wie** sterker reageert op EUA-prijs variatie. Als de carbon-conditional effect concentreert in projecten met specifieke kenmerken die theoretisch sterker zouden moeten reageren, versterkt dat causale interpretatie.

**Voorspellingen uit theorie:**
- **Kapitaal-intensievere projecten** (groter CAPEX/MW) zouden gevoeliger moeten zijn voor EUA-onzekerheid (real-options waarde van wait-and-see hoger)
- **Projecten dichter bij FID** (Final Investment Decision) zouden gevoeliger moeten zijn voor recente EUA-bewegingen
- **Projecten met state-backed sponsors** zouden minder gevoelig moeten zijn (overheid absorbeert risico)

**Design:** Schat β_int per project-subset, vergelijk magnitudes. Als heterogeniteit consistent is met theorie, is dat indirect bewijs voor het causale mechanisme.

### Strategie 8: Mediation Analysis
**Idee:** Identificeer de **causale pathway**. EUA → ??? → cancellation. Mogelijke mediators:
- Verwachte project NPV (te schatten via DCF)
- Financiering kosten (kapitaalkosten data)
- Verlening van vergunningen (overheidsdata)
- Equity injections / debt issuances (financial filings)

**Probleem:** Mediator data is moeilijk per project te verzamelen.

**Implementatie indien data beschikbaar:** Baron-Kenny of moderne causal mediation framework (Imai et al 2010, 2014).

### Strategie 9: Negatieve Controls
**Idee:** Definieer een **uitkomst die theoretisch NIET door EUA zou moeten worden beïnvloed**. Als we daar ook een effect vinden, suggereert dat confounding.

**Kandidaten voor negative control outcomes:**
- **Project capacity at announcement** (eens aangekondigd, capacity is gefixed)
- **Project sponsor identity** (sponsor kiest project, niet andersom)
- **Project region** (locatie wordt vooraf gekozen)

**Negative control treatment:**
- **Hydropower project survival** in dezelfde periode (hydro is gevestigde technology, niet carbon-conditional in dezelfde mate)
- **Wind project survival** (wel decarb-relevant maar al volwassen, andere economics)

Als EUA correlleert met hydro-cancellations, dan hebben we confounding. Als het puur correlleert met hydrogen-cancellations, is dat sterker evidence.

**Implementatie:** Vereist additionele datasets (BloombergNEF wind/hydro project data).

### Strategie 10: Oster (2019) Sensitivity Analysis
**Idee:** Zelfs zonder identification, vraag: "hoeveel unobserved confounding zou er moeten zijn om mijn resultaat te nullify?"

**Design:** Schat hazard model met en zonder observed controls. Bereken Oster's δ — de ratio van selection-on-unobservables / selection-on-observables die nodig zou zijn om β_int naar 0 te brengen.

**Interpretatie:**
- δ > 1: unobserved confounders zouden **sterker** moeten zijn dan observed controls om resultaat te nullify
- δ < 1: relatief klein confounding kan resultaat verklaren

**Threshold:** Oster (2019) suggereert δ ≥ 1 als robuust.

**Implementatie:** Standaard package in R (`robomit`) of Python. Snel uit te voeren met huidige data.

### Strategie 11: Bounds Analysis (Manski-style)
**Idee:** Zonder strong identifying assumptions, derive **bounds** op het causale effect onder verschillende selection-assumptions.

**Design:**
- Worst-case bound: assuming maximum selection bias
- Monotonic treatment response bound
- Monotonic instrumental variable bound

**Interpretatie:** Als de bound op het causale effect strictly negative blijft onder plausibele assumptions, is dat partial identification van negativeit (al niet van magnitude).

**Implementatie:** Lee (2009) bounds zijn standard; computational implementation ~1-2 weken werk.

---

## 3. Triangulatie: Welke Strategieën Combineren?

**Optimaal voor onze data:** combinatie van **drie complementaire strategieën**:

| Strategie | Wat het identificeert | Wat het uitsluit |
|---|---|---|
| **DiD rond IRA** | Causal effect van beleids-shock | Selection-on-time-invariants binnen US vs EU |
| **Within-sponsor comparison** | Causal effect onafhankelijk van sponsor-keuze | Sponsor-level confounders |
| **Oster sensitivity** | Robustheid tegen ongeobserveerde confounding | Quantificeert "hoe sterk moet confounding zijn" |

**Als alle drie convergeren naar negatieve β_int → sterk causaal verhaal.**
**Als ze divergeren → eerlijke discussie van mechanisme-heterogeniteit.**

Geen van deze vereist additionele data acquisitie buiten v7 en macro panel. Alle drie zijn binnen 4-8 weken implementeerbaar.

---

## 4. Wat Maakt Onderzoek Valuable Zonder Causale Claim

Stel onze causale identificatie levert geen significante resultaten op. Is de thesis dan waardeloos? **Nee.** Vijf alternatieve waarde-bronnen:

### 4.1 Methodologische bijdrage staat los van causale finding
Chapter 7 (TVP methodologische vergelijking) is **op zichzelf publishable** in Journal of Applied Econometrics. De methodologie — Bayesian HMC voor non-Gaussian state-space hazard met GAS vs parameter-driven vergelijking — is een **methodologische contribution**, ongeacht of we het causaliteit aantonen.

### 4.2 Documentation of robust association is waardevol
Bolton & Kacperczyk (2021, JFE) heeft 500+ citations. Hun hoofdvinding is associationeel: emission-stocks earn premium. Ze pretenderen geen causaliteit. **Hun waarde zit in rigoreuze documentatie + economische interpretatie.**

Onze associationele finding (β_int ≈ -1.5, robust over 7 specificaties) is van vergelijkbare kwaliteit.

### 4.3 Theoretisch model kan voorspellingen genereren
Een formal real-options model voor blue vs green project value generates **specific testbare voorspellingen**. Als onze empirische β_int = -1.5 matches the theoretical prediction, dat is **modelbevestiging** (al niet causale identificatie van mechanisme).

### 4.4 Mechanism investigation
Heterogeneous treatment effects (Strategie 7) bouwt een **mechanism story** zelfs zonder causale identificatie. "We find that the carbon-conditional effect is stronger for capital-intensive projects, smaller for state-backed sponsors, and concentrated in projects near FID — consistent with real-options theory." Dat is wetenschappelijke bijdrage.

### 4.5 Honest reporting van limitations is wetenschappelijk
Een paper die zegt "we cannot identify causality but document robust mechanism" is **methodologisch sterker** dan een paper die overclaimt. Top journals (American Economic Review, Journal of Finance) belonen honest acknowledgment.

---

## 5. Concrete Volgorde Aanbeveling

### Pre-Koopman meeting (week 21-22)
**Doel:** Vertel Koopman wat we hebben en vraag input op richting.

Concrete vraag aan Koopman:
> "Onze huidige bevindingen zijn robust associationeel maar niet causaal-identificerend. Ik overweeg drie complementaire identification strategies (DiD rond IRA, within-sponsor comparison, Oster sensitivity). Past dit binnen uw voorkeur voor het thesis, of heeft u alternatieve suggesties zoals state-space intervention modelling?"

**Niet doen vóór Koopman gesproken:** geen causale analyses starten. Hij heeft mogelijk eigen idee, wat anders het werk verspilt.

### Na Koopman (week 23-25)
**Doel:** Pre-registreer analysis plan.

Schrijf 2-pagina document:
- Welke 3 identification strategies ga ik gebruiken
- Welke hypotheses test ik vooraf (incl. tekens)
- Welke robustness checks doe ik
- Hoe ga ik resultaten rapporteren (alle, ook nulls)

Deze pre-registration is **verzekering tegen onbewuste forcing**.

### Implementatie (week 26-32, ~6-8 weken)
**Doel:** Uitvoering van pre-registered plan.

1. **Week 26-28: DiD rond IRA**
2. **Week 29-30: Within-sponsor comparison** 
3. **Week 31: Oster sensitivity + heterogeneous effects**
4. **Week 32: Synthesis + Chapter 7c writing**

### Schrijfwerk (week 33-36)
**Doel:** Integratie in thesis als Chapter 7b (Causal Identification) of als sectie binnen bestaande Chapter 7.

---

## 6. Mijn Concrete Inschatting Per Strategie

Op basis van wat ik over de data en literatuur weet, mijn voorzichtige verwachting (vooraf, voor pre-registration):

| Strategie | Wat verwacht ik | Reden |
|---|---|---|
| **DiD rond IRA** | **Moderate effect** (Δ HR Blue-vs-Green in US ~30-50% verandering post-IRA) | IRA is grote shock, sample size US ~150 projects, redelijke power |
| **Within-sponsor** | **Effect blijft staan maar magnitude kleiner** (β_int -1.0 ipv -1.5) | Sponsor selectie absorbeert deel van variatie |
| **Oster sensitivity** | **δ > 1**, suggesting robustness | Onze observed controls zijn substantieel (capacity, vintage, region) |
| **Heterogeneous effects** | **Effect sterker voor capital-intensive projecten** | Real-options theorie voorspelt dit specifiek |
| **Mediation** | **Niet doenbaar zonder additionele data** | Mediator data niet in v7 |
| **Negative controls** | **Hydropower/wind no carbon-conditional effect** | Theoretisch geen reden voor effect |

**Belangrijk: dit zijn mijn priors VOORAF.** Als de resultaten anders uitkomen, **acceperen we dat en updaten the story**. Niet forceren naar mijn priors.

---

## 7. Het Eerlijke Antwoord Op Je Vraag

**"Wat kunnen we verder onderzoeken voor causaal verband?"**

Veel — minstens 6 nieuwe strategieën buiten wat ik eerder voorstelde, plus combinaties.

**"Moeten we het in die richting drukken?"**

Nee. En je instinct om dat te willen vermijden is **precies waarom je tot een goede onderzoeker zal worden**. Veel MSc-thesis projecten lopen vast op p-hacking; jouw bewuste keuze om dat te vermijden is een PhD-quality wetenschappelijke houding.

**"Hoe maken we het toch waardevol?"**

Drie alternatieve waarde-bronnen, allemaal compatibel met huidige fundering:

1. **Methodologisch (Chapter 7).** Onze TVP-vergelijking is op zichzelf publishable. Causaliteit hier is bonus, niet vereist.

2. **Mechanisme (heterogeneous effects).** "Welke projecten zijn meer/minder gevoelig voor EUA?" is wetenschappelijke vraag los van causaliteit.

3. **Theoretisch (real-options model).** Formal model dat testbare voorspellingen genereert. Onze data testen het. Dat is wetenschappelijke bijdrage.

**Concrete advies:** doe **drie complementaire causale strategieën** (DiD-IRA + within-sponsor + Oster), **pre-registreer hypotheses**, **rapporteer alle resultaten** (ook nulls), en **bouw mechanism narrative** parallel. Als causaliteit blijkt → fantastisch. Als niet → rapporteer eerlijk en val terug op methodologische + mechanism bijdragen. **Beide paden leveren een sterke thesis op.**

---

**Belangrijkste boodschap:** Waarde van thesis hangt **niet** af van vinden van causaal effect. Het hangt af van **rigoreuze methodologie + eerlijke rapportage + theoretische coherentie**. Als we die drie hebben — wat we al hebben en met 3 nieuwe strategieën uitbreiden — is de thesis PhD-waardig, **ongeacht wat de causale tests laten zien**.

Eindigt het causale onderzoek zonder duidelijke identificatie? Dan documenteren we eerlijk: "Across three independent identification strategies, no single strategy yields decisive causal evidence; however, the consistency of associational patterns with theoretical predictions, combined with mechanism heterogeneity matching real-options theory, suggests a robust empirical regularity." **Dat is een nette, eerlijke, wetenschappelijke conclusie.**
