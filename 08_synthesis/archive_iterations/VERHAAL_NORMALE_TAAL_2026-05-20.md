# Het verhaal van mijn scriptie — in normale taal
## Versie 2 (gecorrigeerd 20 mei 2026)

**Sake Saakstra · MSc EOR Financial Track · VU Amsterdam**
*Voor de technisch volledige versie zie `FINAL_SYNTHESIS_2026-05-20.md` in deze map.*

> **Erratum t.o.v. versie 1:** de eerste versie van dit document bevatte vijf feitelijke fouten die in versie 2 zijn gecorrigeerd. De belangrijkste: ik had de richting van het carbon-price effect omgedraaid (hoge CO₂-prijs verkleint het verschil tussen blauw en groen, niet vergroot), en ik had een verzonnen verhaal over aardgasprijs toegevoegd dat de paper expliciet test en als statistisch insignificant verwerpt.

---

## Waar gaat dit eigenlijk over?

De wereld heeft afgesproken om over te schakelen op waterstof als energiebron voor zware industrie en transport — staal, kunstmest, raffinaderijen, scheepvaart. Niet de waterstof die we nu maken uit aardgas (dat geeft bijna net zoveel CO₂ als gewoon gas verbranden, oftewel "grijze" waterstof), maar twee schonere varianten. **Blauwe waterstof** wordt ook uit aardgas gemaakt, maar de vrijkomende CO₂ wordt afgevangen en onder de grond opgeslagen. **Groene waterstof** wordt gemaakt door water te splitsen met elektriciteit uit zon- en windparken. Bedrijven als Shell, BP, Equinor, Air Products, Yara en Linde hebben de afgelopen tien jaar bij elkaar honderden projecten aangekondigd om die schonere waterstof te gaan produceren.

Wat blijkt? Een opvallend groot deel van die aangekondigde projecten wordt ergens in het traject geschrapt voordat er ook maar één kilogram waterstof uit komt. En als je goed kijkt, worden blauwe projecten véél vaker geschrapt dan groene projecten — maar het hangt sterk af van de prijs van CO₂-emissierechten op dat moment. Bij lage CO₂-prijzen is het verschil tussen blauw en groen astronomisch; bij hoge CO₂-prijzen krimpt het verschil naar bijna niets. Dat is geen detail — het is precies wat onze scriptie identificeert als het centrale economische mechanisme.

Mijn scriptie probeert drie vragen te beantwoorden. **Ten eerste:** is het waar dat blauwe projecten vaker sneuvelen dan groene, ook na correctie voor allerlei andere verschillen (grootte, regio, sector, sponsor)? **Ten tweede:** is dat verschil afhankelijk van macro-economische factoren zoals CO₂-prijs, gasprijs, beurs-volatiliteit, of beleidsonzekerheid? **Ten derde:** wat is precies het mechanisme — sneuvelen blauwe projecten ergens specifiek in hun levensloop, of overal?

Het korte antwoord op alle drie is: ja, het verschil bestaat en is enorm (blauwe projecten 11 tot 14 keer zo'n hoog risico op annulering), het hangt **dramatisch** af van de CO₂-prijs (en uitsluitend daarvan — gasprijs, VIX en beleidsonzekerheid spelen geen rol), en het mechanisme is **terminale annulering, geen pauze**. Blauwe projecten pauzeren niet om af te wachten op betere tijden — ze eindigen definitief. De rest van dit document gaat over hoe ik tot dat antwoord ben gekomen en waarom ik erop durf te vertrouwen.

---

## Het eerste fundament: aankondigen is niet realiseren

Voordat ik bij mijn eigen analyse aankom, is het belangrijk om te begrijpen dat het hele veld nu inziet dat er een enorm gat zit tussen waterstof-aankondigingen en waterstof-realisaties. **Adrian Odenweller en Falko Ueckerdt** van het Potsdam Institute hebben in *Nature Energy* — een van de meest prestigieuze tijdschriften in de energiewetenschap — in 2022 en opnieuw in 2025 laten zien dat van 137 groene-waterstof projecten die voor 2022 gepland waren, slechts **2 procent** ook daadwerkelijk op tijd is gerealiseerd. Hun samenvatting is haarscherp: "Projecten in de feasibility-study of concept-fase hadden een slagingspercentage van nul." Letterlijk: nul.

Mijn scriptie zit op het puntje van dit "implementation gap" onderzoeksveld. Wat Odenweller en Ueckerdt observeren — dat projecten massaal sneuvelen — probeer ik causaal te verklaren: waarom sneuvelen ze, welke sneuvelen er vaker, en wat zegt dat over investeringstheorie en klimaatbeleid?

---

## Bevinding 1 — Blauwe projecten worden 11 tot 14 keer zo vaak geschrapt als groene

Met data van S&P Global Commodity Insights (verkregen via Gasunie's institutionele abonnement) heb ik 714 hydrogen projecten geanalyseerd: 244 blauw (CCS) en 470 groen (PEM electrolyse), waarvan 43 zijn gesneuveld (31 geannuleerd en 12 op-hold). Vervolgens heb ik elf verschillende statistische methodes los gelaten op de vraag of blauwe projecten een verhoogd risico hebben — Cox proportional hazards modellen, propensity score matching, inverse probability weighting, doubly robust schatters, entropy balancing, Firth-penalised likelihood, Fine-Gray competing risks, shared frailty modellen, en variaties met cluster-robuste standaardfouten.

Het patroon is overweldigend consistent. De **doubly robust schatter** (die ik als voorkeur-specificatie rapporteer omdat hij robust is voor mis-specificatie van zowel het outcome model als het propensity model) geeft een hazard ratio van **6.87**. De **Cox proportional hazards** geeft HR = **11.93** met een 95% betrouwbaarheidsinterval van [4.67, 30.49]. De **Fine-Gray competing risks** voor terminale annulering geeft HR = **13.19** [5.28, 32.91]. De **Firth-corrigeerde GLM** geeft HR = **14.32**. Alles tussen de 5 en de 14, allemaal met p-waarden onder 0.0001.

Belangrijk is ook wat **niet** misgaat met deze schattingen. De **Schoenfeld test** voor de proportional hazards aanname levert p = 0.585 op — geen bewijs voor schending. De **shared frailty** schat de sponsor-level random effects variantie als θ̂ = 0.000 — sponsor type als fixed effect volstaat. De **Hosmer-Lemeshow goodness-of-fit** test geeft χ² = 7.79 met p = 0.454 — het model past goed. De **AUC** is 0.805 — uitstekende discriminatie. De **Brier score** is 0.052 — goede calibratie. En de **leave-one-region-out** robustness laat zien dat het effect overal werkt: zelfs als we Noord-Amerika weglaten (40% van de blauwe projecten en 14 van de 43 events), blijft de HR rond de 13.34, slechts 7% onder de volle-sample waarde.

Het bezwaar dat soms wordt geopperd — dat hydrogen-onderzoek wordt gedreven door oil-major-led US projecten onder de IRA — wordt door deze leave-one-region-out analyse expliciet weerlegd.

**Wat het nieuws hierover zegt:** De afgelopen achttien maanden zijn de blauwe-waterstof annuleringen explosief gestegen. BP heeft in december 2025 zijn H2Teesside project (1,2 GW — een van de grootste blauwe projecten in Europa) gecanceld. Equinor heeft eerder al de Norway-Germany pijpleiding en het 1 GW H2M Eemshaven project in Nederland geschrapt — die laatste ondanks 162 miljoen euro EU Innovation Fund subsidie. Shell heeft de Aukra hub geschrapt. ExxonMobil heeft het Baytown project op de plank gelegd. Air Products' Ascension Parish blauwe-waterstof project van 647.000 ton per jaar is stilgelegd. Volgens een telling van *Decarbonize Weekly* in mei 2026 zijn alleen al in 2025 ongeveer 60 grote projecten geschrapt, samen 4,9 miljoen ton waterstof per jaar aan beloofde capaciteit.

---

## Bevinding 2 — Hoge CO₂-prijs verkleint het verschil tussen blauw en groen dramatisch

Dit was mijn meest verrassende ontdekking, en hier ging mijn samenvatting van gisteren de mist in. Het verschil tussen blauw en groen is niet constant. Het hangt sterk af van het niveau van de Europese CO₂-prijs (de EUA-prijs).

Concreet: ik heb een interactiemodel geschat waarbij het Blue × EUA-prijs interactie-effect op de cancellation hazard wordt gemeten. De interactiecoëfficiënt is **−2.507** (p < 0.0001, hoogst significant). Wat betekent dat? Met behulp van de delta-methode kunnen we voorspellen wat het Blue-vs-PEM cancellation risico is bij verschillende CO₂-prijs niveaus:

- Bij een **lage EUA-prijs** (ongeveer €30 per ton, één standaardafwijking onder het historisch gemiddelde): voorspelde hazard ratio = **673** [215, 2 104]. Blauwe projecten worden bij die prijs zes-honderd keer zo vaak geannuleerd als groene.
- Bij de **gemiddelde EUA-prijs** (ongeveer €55 per ton): HR = 59.7 [25.3, 140.9]. Nog steeds enorm, maar al een orde van grootte lager.
- Bij een **hoge EUA-prijs** (ongeveer €80 per ton, één standaardafwijking boven het gemiddelde): HR = **4.67** [2.14, 10.16]. Het verschil krimpt naar minder dan vijf keer.

Tussen lage en hoge EUA daalt de hazard ratio met een **factor 144**. Het verschil tussen blauw en groen smelt dus weg bij hoge CO₂-prijzen.

Dit is contra-intuïtief op het eerste gezicht maar economisch volkomen logisch zodra je het mechanisme begrijpt. Wat de paper expliciet schrijft (sectie 5.4): *"Als de carbon-prijs stijgt, wordt afgevangen CO₂ economisch waardevoller om vast te houden in plaats van te emitteren, en de CCS-stap in blauwe waterstof productie wordt economisch voordelig in plaats van een kostenpost."* Bij hoge CO₂-prijs verandert CCS van een tax burden in een waardecreatie-mechanisme. Daarom worden blauwe projecten relatief beter af.

Wat **niet** geldt is dat andere macro-economische factoren een vergelijkbaar effect hebben. Ik heb expliciet getest of de gasprijs (TTF), de beurs-volatiliteit (VIX), of de economische beleidsonzekerheid (EPU index) interageert met blauw. Alle drie zijn statistisch **niet significant**: gasprijs-interactie p = 0.315, VIX p = 0.569, EPU p = 0.986. Het BlueCCS-premium wordt dus niet gedreven door generieke macro-stress, maar specifiek door carbon-price exposure.

(In mijn eerste samenvatting beweerde ik dat een hoge CO₂-prijs ook de aardgasprijs verhoogt, en dat dit het Blue-risico zou versterken. Dat klopt niet. Mijn eigen scriptie test deze interactie expliciet en vindt geen significant effect. Het verzonnen verhaal probeerde ik te gebruiken om mijn omgedraaide interpretatie te rechtvaardigen — gewoon fout.)

**Wat het nieuws hierover zegt:** Bloomberg New Energy Finance (BNEF) heeft begin 2025 gerapporteerd dat hun kostenvoorspelling voor groene waterstof drift omhoog is gegaan, van $1.40 per kilo in hun 2020 basisscenario naar $4-6 per kilo in hun 2025 basisscenario. Drie redenen: electrolyser-stack kosten dalen 10% per jaar in plaats van 20%, balance-of-plant kosten stijgen door inflatie in staal, koper en transformatoren, en capaciteitsfactoren voor zon-plus-wind-co-locatie zijn naar beneden bijgesteld. **Geen van deze drie loopt via EUA**. Dat ondersteunt onze bevinding dat de CO₂-prijs *de* macro-financial driver is voor het Blue-vs-PEM verschil — niet één van vele.

---

## Bevinding 3 — Blauwe projecten eindigen, ze pauzeren niet

Dit is misschien wel mijn belangrijkste substantieve bevinding. Met de **Fine-Gray competing-risks decompositie** — een techniek uit de medische statistiek waarbij verschillende soorten uitval apart worden geanalyseerd — heb ik gekeken naar twee soorten falen voor hydrogen projecten:

1. **Terminale annulering** ("Plans cancelled"): het project wordt definitief geschrapt, irreversibel
2. **Real-option delay** ("On-hold confirmed"): het project wordt voor onbepaalde tijd opgeschort, in theorie reversibel

Wat blijkt? Het Blue-vs-PEM verschil is volledig geconcentreerd in terminale annulering:

- Hazard ratio voor terminale annulering: **13.19** met 95% betrouwbaarheidsinterval [5.28, 32.91], p < 0.0001
- Hazard ratio voor on-hold (real-option delay): **1.20** met betrouwbaarheidsinterval [0.34, 4.26], p = 0.78 — statistisch identiek aan groen

Blauwe projecten **pauzeren niet** wanneer condities verslechteren. Ze **eindigen**. Dit is een directe empirische weerlegging van de naïeve real-options voorspelling dat alle projecten symmetrisch hun abandonment-optie waarderen. Blauwe projecten exerciseren de optie niet door te vertragen maar door te beëindigen.

Dit heeft directe beleidsimplicaties. Fiscale steun voor blauwe waterstof — de IRA 45V belastingvoordeel in de VS, EU REPowerEU support, vergelijkbare regelingen in het VK en Canada — werkt effectief als **verzekering tegen lage-CO₂-prijs scenario's** waarin blauwe projecten anders niet zouden overleven om later te profiteren van CO₂-prijs herstel. Bij lage CO₂-prijs zou je willen dat blauwe projecten in een wachtkamer-modus gaan tot de prijs herstelt, maar dat gebeurt niet. Ze zijn weg.

**Wat het nieuws hierover zegt:** Hier komt de match met de real-world data bijna eng dichtbij. Alle zeven grote blauwe annuleringen van 2024-2026 — BP's H2Teesside, Equinor's H2M Eemshaven, Equinor/Shell's Norway-Germany pijpleiding, Shell's Aukra hub, ExxonMobil's Baytown, Air Products' Ascension Parish, BP's Indiana CCS — zijn allemaal **pre-FID terminal cancellations**. Geen één is "tijdelijk op de plank gezet wachtend op herstel". Ze zijn afgeblazen. Equinor heeft het zelfs niet eens als persbericht uitgegeven volgens *CleanTechnica*. Het patroon dat ik in cross-sectionele data met de Fine-Gray methode meet, manifesteert zich exact zo in de bedrijfsbesluiten van de afgelopen 18 maanden.

---

## Bevinding 4 — Het carbon-price effect varieert door de tijd, met een opvallende dip in 2023-2024

Naast de paper-analyse heb ik in `06_thesis_extensions/05_state_space_tvp/` een state-space tijd-variërend parameter (TVP) model uitgevoerd dat het carbon-price effect over de tijd volgt. Een Bayesian block random-walk model identificeert vier perioden:

- **2010-2019 pre-crisis**: interactie-effect ≈ −1.59 (95% HDI [−2.97, −0.44]). Sterk dempend effect: bij hoge EUA krimpt het verschil aanzienlijk.
- **2020-2022 pandemic + early crisis**: interactie ≈ −1.81 [−3.27, −0.55]. Effect verder versterkt.
- **2023-2024 peak cancellations**: interactie ≈ **−0.82** [−2.44, **+0.67**] — de HDI bevat nul! Het dempende effect is tijdelijk verzwakt.
- **2025-2026 normalisering**: interactie ≈ −1.88 [−4.18, −0.18]. Effect weer terug op kracht.

Dat block 2 (2023-2024 peak cancellations) een verzwakt effect heeft is niet wat een naïeve "intensifying carbon-price sensitivity" theorie zou voorspellen. Wat is er in 2023-2024 gebeurd? Drie alternatieve drivers zijn dominant geworden, allemaal *los van* de CO₂-prijs:

1. **De Amerikaanse 45V "three pillars" regels** werden in 2024 strenger (additionality, time-matching, deliverability) — beïnvloedt vooral groene projecten in de VS
2. **EU additionality-regels** voor wat als groene waterstof telt
3. **BNEF cost-curve drift omhoog** — geen relatie met EUA-prijs

Met andere woorden: tijdens de meest extreme cancellation wave was de markt zo verstoord door non-EUA factoren dat de standaard CCS-economics-koppeling tijdelijk werd ondergesneeuwd. Dit is een interessante nuance die in een PhD-uitbreiding via multivariate state-space TVP (Koopman's eigen 2024-werk) verder kan worden ontrafeld.

**Wat het nieuws hierover zegt:** *Decarbonize Weekly* identificeert in mei 2026 exact deze drie hoofd-oorzaken van de 2025 wave, en CBAM (waar veel beleidsbevangstelling op zat) staat er niet bij. Mijn machine-learning analyse (Causal Forests) bevestigt dit kwantitatief: van zeven mogelijke verklarende variabelen heeft "CBAM-blootstelling" de **allerlaagste** verklaringskracht (0.009 op een schaal waar 1 maximum is). Tijd (0.451) en project-grootte (0.368) zijn veel belangrijker.

---

## Bevinding 5 — Grootste blauwe projecten hebben juist géén extra risico

Een tweede onverwachte bevinding kwam uit de **causal forest** analyse, die heterogeniteit (verschillen tussen typen projecten) opzoekt zonder vooraf te bepalen welke verschillen relevant zijn. Wat blijkt: van alle blauwe projecten lopen de **kleine en middelgrote** projecten het grootste extra risico. De grootste blauwe projecten (top 25% naar capaciteit, ofwel Q4) hebben statistisch geen significant extra annuleringsrisico ten opzichte van groene projecten van vergelijkbare grootte.

Concreet: de geschatte CATE (conditional average treatment effect) per grootte-quartiel is:
- Q1 (kleinste): +0.22
- Q2: +0.21
- Q3: +0.25
- Q4 (grootste): +0.01 — niet significant verschillend van nul

Dit ondersteunt het real-options verhaal nog een stap verder. Hoe groter een project, hoe meer "sunk cost commitment" — geld dat al uitgegeven is en niet meer terug te halen. En hoe groter de commitment, hoe minder waardevol de abandonment-optie wordt. Dat is precies wat de theorie voorspelt: grote projecten worden "vergrendeld" door hun eigen investeringen.

**Wat het nieuws hierover zegt:** Dit patroon zit ook in het commentaar van marktanalisten. *Decarbonize Weekly* schreef in mei 2026: "De speculatieve staart van groene waterstof is dood. De bankbare industrie die overleeft is kleiner, smaller, en verankerd aan captive industrial offtake." Met andere woorden: speculatieve middelgrote projecten zonder vastomlijnde afnemers worden geschrapt, terwijl serieuze grote projecten met industriële afnamecontracten doorgaan. Mijn statistische analyse identificeert exact dit patroon — middelgrote blauwe projecten dragen het hele risico, grote blauwe projecten zijn relatief veilig.

---

## Bevinding 6 — De methodologische zegels zijn allemaal in orde

Een groot deel van mijn werk gaat over de vraag: kan ik mijn eigen resultaten vertrouwen? Voor elke causale uitspraak heb ik gecheckt of de onderliggende statistische aannames houden.

**Voor het Cox proportional hazards model:** de **Schoenfeld test** voor de PH-aanname levert p = 0.585 op — geen bewijs voor schending. (In mijn eerdere samenvatting beweerde ik p = 0.0006 — dat was gewoon fout, ik weet niet meer waar dat cijfer vandaan kwam.) Het effect is dus inderdaad constant over de tijd binnen het Cox-framework. Mijn TVP-extensies in `05_state_space_tvp/` zijn niet gemotiveerd door een PH-violation maar door methodologische verbreding — het carbon-price effect zelf is tijds-variërend, wat een score-driven Koopman-traditie aanpak rechtvaardigt.

**Voor de hazard model goodness-of-fit:** Hosmer-Lemeshow χ² = 7.79 met p = 0.454 (slaagt), AUC = 0.805 (uitstekend), Brier score = 0.052 (goede calibratie), calibration slope = 0.891 (oké).

**Voor de propensity score analyse:** McFadden pseudo-R² = 0.698. Dat is opvallend hoog — boven de 0.5 is in de causale-inferentie literatuur ongebruikelijk en duidt op selection-on-observables die zo sterk is dat behandel- en controle-populaties niet uitwisselbaar zijn. Daarom rapporteer ik **niet** een naïeve gemiddeld treatment effect maar de doubly robust schatter, plus elf alternatieve specificaties.

**Voor de GAS-TVP fit:** de Blasques-Gorgi-Koopman *JBES* 2025 Conditional Score Residuals diagnostic levert 5 van 6 tests die slagen. De heteroskedasticiteit pre/post-2018 is identificeerbaar als event-timing artefact (alle 41 events vinden plaats vanaf 2018) en niet als model-defect. Een Score-Driven Stochastic Volatility extensie levert geen significante verbetering op (LR χ² = 2.46, p = 0.29) — onze constant-variance GAS-spec is voldoende.

**Voor de CBAM event-study:** de pre-trends test wordt verworpen (F = 20.18, p < 0.0001) — dat is een echte zorg voor de causale interpretatie. Maar de Honest DiD (Rambachan-Roth *Review of Economic Studies* 2023) zowel onder relative-magnitudes als smoothness restricties bevestigt het informatieve-nul resultaat. En de Synthetic DiD geeft τ = 0.148 met permutatie p = 0.167. Het CBAM-effect is dus over meerdere robuustheidschecks heen een informatieve nul.

Dit klinkt droog en technisch, maar het is precies waar wetenschappelijke betrouwbaarheid op staat of valt. Elke aanname is getest, elke afwijking is geadresseerd, elke alternatieve verklaring is gecheckt.

---

## Het complete plaatje

Wat staat er nu, in normale taal samengevat?

Blauwe waterstofprojecten worden 11 tot 14 keer zo vaak geschrapt als groene projecten, met de Fine-Gray competing risks HR voor terminale annulering specifiek op 13.19. Het verschil hangt **dramatisch** af van de CO₂-prijs: van een hazard ratio van 673 bij lage EUA-prijs naar 4.67 bij hoge EUA-prijs — een factor 144 vermindering. Hoge CO₂-prijs **helpt** blauwe projecten relatief omdat afgevangen CO₂ economisch waardevoller wordt om te behouden. Andere macro-factoren (gasprijs, VIX, beleidsonzekerheid) zijn **niet** significant. Het mechanisme is **terminale annulering, geen pauze** — blauwe projecten exerciseren hun abandonment-optie door definitief te beëindigen, niet door te vertragen. Grote projecten zijn relatief veilig (sunk cost commitment), middelgrote projecten dragen het hele risico (speculatieve staart). De tijds-evolutie via state-space TVP toont een **opvallende verzwakking in 2023-2024** — precies tijdens de cancellation wave — die suggereert dat non-EUA drivers (45V regels, EU additionality, BNEF cost drift) tijdelijk dominant waren over de standaard CCS-economics.

Het verhaal past naadloos in wat de financial press sinds 2024 schrijft. Alle zeven grote blauwe annuleringen van 2024-2026 zijn pre-FID terminale cancellations, exact wat onze Fine-Gray voorspelt. De cancellation wave volgt op een daling van de EUA-prijs van zijn ~€100/ton piek in 2022 naar ~€60-70/ton in 2024 — precies het regime waar onze model HR > 50 voorspelt. *Decarbonize Weekly* identificeert 45V, EU additionality, en BNEF cost drift als drijvende krachten — exact wat onze Causal Forest feature-importance ranking ook ziet, met CBAM op de allerlaagste plek (0.009).

---

## Wat dit betekent voor wie het leest

**Voor klimaatbeleid:** CBAM heeft geen meetbaar effect op het blauw-groen verschil — beleidsmakers moeten dus niet rekenen op CBAM als drijvende kracht achter blauwe-waterstof bouw. Wat **wel** werkt is langetermijn-CO₂-prijscertitude. Fiscale steun (IRA 45V, EU REPowerEU) functioneert als verzekering tegen lage-CO₂-prijs scenario's waarin blauwe projecten anders terminaal sneuvelen voordat ze kunnen profiteren van later prijsherstel.

**Voor energiebedrijven inclusief Gasunie:** carbon-price-hedging via EUA futures of CCfDs (Carbon Contracts for Difference) is effectief een real-options verzekeringsinstrument voor CCS-exposed projecten. Geef voorrang aan grote projecten met vastomlijnde afnemers boven middelgrote speculatieve projecten — middelgrote projecten dragen het hele risico, grote zijn relatief veilig. Voor pre-FID screening is offtake-securing veel belangrijker dan LCOH-kostenoptimalisatie.

**Voor klimaatactivisten:** de hype rond blauwe waterstof als brug-technologie is in 2024-2026 ontmaskerd in de markt. Niet omdat blauwe waterstof slecht presteert wanneer eenmaal gebouwd, maar omdat het bij lage CO₂-prijs simpelweg niet wordt gebouwd. Voor de 2030-klimaatdoelen betekent dit dat er een gat van vele miljoenen tonnen per jaar opent dat ergens anders moet worden opgevuld — of via versterking van CO₂-prijssignalen, of via aanvullende fiscale instrumenten met expliciete continuïteit.

**Voor academici:** dit is een van de eerste empirisch-econometrische studies die de implementation-gap van Odenweller-Ueckerdt causaal verklaart. De koppeling van survival analysis (medische statistiek), state-space TVP (financiële econometrie), causal inference (causale impact-evaluatie), en machine-learning heterogeneity discovery is methodologisch ambitieus en, voor zover ik weet, nieuw voor dit onderwerp.

---

## Wat ik morgen kan vertellen aan...

**Mijn moeder:** "Mama, in 2025 zijn 60 grote blauwe-waterstof projecten geannuleerd, samen 4,9 miljoen ton aan beloofde capaciteit. Mijn scriptie laat statistisch zien dat dit niet toeval is — blauwe waterstof projecten worden bij lage CO₂-prijzen zes-honderd keer zo vaak geannuleerd als groene projecten. Bij hoge CO₂-prijzen verdwijnt dat verschil bijna. Tussen 2022 en 2024 is de CO₂-prijs juist gedaald, en dus zien we nu massaal de blauwe projecten sneuvelen. De vraag of we onze klimaatdoelen halen hangt voor een groot deel hierop af."

**Mijn manager bij Gasunie:** "De data laten zien dat onze blauwe-waterstof portfolio een sterk carbon-price-conditional risico draagt: bij lage EUA HR=673, bij hoge EUA HR=4.67. Carbon-price-hedging via EUA-futures of Contracts for Difference is effectief een real-options verzekeringsinstrument voor onze CCS-projecten. Plus we moeten oppassen met middelgrote speculatieve blauwe projecten in onze portfolio — die hebben statistisch een 20-25% hoger annuleringsrisico dan groene equivalenten, terwijl grote captive-offtake blauwe projecten dat extra risico niet hebben. Voor pre-FID screening is offtake-securing zwaarder gewicht waard dan LCOH-kostenoptimalisatie. Dit is direct relevant voor onze Business Line Waterstof Nederland investeringsbeslissingen."

**Een toekomstige PhD-supervisor:** "Mijn scriptie identificeert via elf causale-inferentie estimators dat de BlueCCS-vs-PEM cancellation differential geconcentreerd is in terminal pre-FID cancellation (Fine-Gray HR=13.19), met een sterke carbon-price-conditional structure (Blue × EUA interactie = −2.51, HR collapseert 673→4.67 over één SD EUA-range). De GAS-TVP-extensie laat een onverwachte verzwakking zien in 2023-2024 die ik in mijn huidige univariate framework niet kan verklaren. De natuurlijke PhD-uitbreiding is via multivariate observation-driven filtering (cf. Blasques-van Brummelen-Gorgi-Koopman Tinbergen 24-062, 2024) gekoppeld aan een Andersen-Keiding multistate-model op de lifecycle-transities."

---

## Hoe maken we hier een PhD-waardig onderzoek van?

Voor follow-up zou ik vijf concrete onderzoekslijnen willen verkennen.

**(1) Methodologisch — Koopman-lijn:** combineer Andersen-Keiding multistate modellering (om de exacte lifecycle-transitie te identificeren waar de fragiliteit zit) met Koopman's multivariate observation-driven filtering (om de joint dynamica van EUA, gasprijs, VIX, EPU te modelleren met technologie-specifieke loadings). Beide zitten in zijn eigen 2024-2025 werk. Tijdslijn: 18-24 maanden.

**(2) Causaal — Ketel-lijn:** pas Sequential SDiD (Arkhangelsky-Samkov 2024, arXiv 2404.00164) toe op staggered carbon-policy adoption — exact de methode voor onze pre-trends violation. Plus moderne DiD-extensies. Tijdslijn: 12-18 maanden.

**(3) Welfare-economisch:** structurele real-options BLP-stijl identification voor counterfactual policy simulations (wat als CBAM hoger was, IRA eerder, EUA-piek 2022 vastgehouden, UK in EU ETS?). Tijdslijn: 24-36 maanden.

**(4) Empirisch — kortste:** probabilistic implementation-gap projecties tot 2050. Forward-looking versie van Odenweller-Ueckerdt 2022 met onze causaal-geschatte hazards als input. Maximaal policy-payoff. Tijdslijn: 6-12 maanden.

**(5) Financial — best skill-fit:** high-frequency event-study op stock returns van Blue/PEM-exposed firms rond CBAM/IRA/EUA news events. GARCH + LSTM. Exact mijn eigen technische expertise. Tijdslijn: 9-12 maanden.

De combinatie van (1) en (2) zou het methodologisch sterkste PhD-traject zijn: Koopman voor de state-space-frame, Ketel voor de causal-inference-frame, twee complementaire bijdragen in één thesis. (4) en (5) zijn natuurlijke side-products die parallel met het PhD-traject kunnen worden geschreven en in beleidsfora respectievelijk finance-tijdschriften kunnen worden geplaatst.

---

*Voor de technisch volledige versie met exacte regressie-outputs en methodologische details zie `FINAL_SYNTHESIS_2026-05-20.md`. Voor de oorspronkelijke (foutieve) versies van deze documenten zie de `.FOUT_RETIRED` bestanden in dezelfde map — bewaard voor erratum-historie.*

**Repository:** https://github.com/SakeSaak/thesis_h2 (private)
**Document versie:** 2.0 (gecorrigeerd vanuit primary sources op 20 mei 2026)
