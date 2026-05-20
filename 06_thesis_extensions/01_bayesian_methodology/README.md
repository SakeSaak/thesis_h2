# Bayesian Survival - Thesis Extension

Spoor 1 van de thesis-extensie: Bayesian Cox PH en Fine-Gray met informatieve priors,
toegepast op het v7 dataset voor Blue_CCS vs PEM hydrogen project cancellation.

## Bestanden

| Bestand | Doel |
|---|---|
| `bayesian_methodology_design.pdf` | Volledige methodologische onderbouwing — priors per parameter, sensitivity plan, open questions voor supervisor |
| `bayesian_methodology_design.tex` | LaTeX bron van design document |
| `00_setup_environment.R` | Eenmalige R package installatie (brms, rstan, etc.) |
| `01_bayesian_cox_baseline.R` | Hoofdscript: Bayesian Cox PH met 4-prior sensitivity grid |
| `results/` | Wordt aangemaakt door scripts — bevat fits, tabellen, figuren |

## Eerste keer draaien

Stap 1 — packages installeren (15-30 min, eenmalig):
```bash
cd /Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/01_bayesian_methodology
Rscript 00_setup_environment.R
```

Stap 2 — quick run (5-10 min) om te verifiëren dat alles werkt:
```bash
Rscript 01_bayesian_cox_baseline.R
```

Stap 3 — productie run (45 min) voor finale resultaten:
- Open `01_bayesian_cox_baseline.R`
- Zet `RUN_MODE <- "full"` (regel 30)
- Sla op en draai opnieuw

## Wat het script produceert

```
results/
├── fits/
│   ├── cox_vague_quick.rds
│   ├── cox_weakly_informative_quick.rds
│   ├── cox_skeptical_quick.rds
│   └── cox_informative_quick.rds
├── tables/
│   └── posterior_summary.csv      # Vergelijkingstabel
└── figures/
    ├── posterior_HR.pdf           # Posterior densities Blue_CCS HR
    └── trace_plots.pdf            # MCMC diagnostiek
```

## Sensitivity grid (4 priors x is_blue_ccs coefficient)

| Prior label | Specificatie op β₁ (Blue_CCS) | Interpretatie |
|---|---|---|
| `vague` | Normal(0, 5) | Quasi-niet-informatief; sanity check dat data de schatting domineert |
| `weakly_informative` | Normal(0, 2) | Default; allows large effects maar bounds extreme uitkomsten |
| `skeptical` | Normal(0, 1) | Gecentreerd op géén effect; tests dat het signaal door de prior dringt |
| `informative` | Normal(1.5, 0.7) | Literatuur-gebaseerd (HR ~4.5 ± uncertainty) |

Voor andere coefficiënten (region, sponsor_type, log_capacity): default weakly informative Normal(0, 1.5).

## Bekende beperkingen v0.1

1. **Geen time-varying covariates**: dit baseline script gebruikt static project-level data.
   Voor carbon-conditional Cox (de hoofdfinding van het paper) is person-period data
   met time-varying EUA nodig. Komt in `02_bayesian_carbon_conditional.R`.

2. **Geen competing risks**: cancellation en on-hold worden samengevoegd tot event_any.
   Fine-Gray competing-risks Bayesian model komt in `03_bayesian_finegray.R`.

3. **Default brms M-spline baseline hazard**: methodology document beveelt piecewise
   constant met K=5 aan, maar voor v0.1 gebruiken we brms default. Open question voor Bos.

## Vervolgscripts (gepland)

- `02_bayesian_carbon_conditional.R` — uitbreiding met time-varying EUA + Blue×EUA interactie
- `03_bayesian_finegray.R` — competing risks (cancellation vs on-hold)
- `04_prior_predictive_checks.R` — simulatie-validatie van prior keuzes
- `05_posterior_predictive_checks.R` — model fit assessment

## Referentie

Zie `bayesian_methodology_design.pdf` voor:
- Volledige rationale per prior keuze
- Open questions Q1-Q6 voor Bos
- Literatuur-onderbouwing (Bolton & Kacperczyk, Odenweller, Bauwens-Bos-Van Dijk, etc.)
- Implementation roadmap (10 weken)
