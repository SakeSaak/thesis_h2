# ============================================================================
# 00_setup_environment.R
#
# Eenmalig draaien om Bayesian survival packages te installeren.
# Auteur: Sake Saakstra
# Thesis extension: Bayesian survival met informatieve priors
# ============================================================================

cat("================================================================\n")
cat("Bayesian Survival - Environment Setup\n")
cat("================================================================\n\n")

# Belangrijkste packages
required_pkgs <- c(
  # Bayesian inference
  "brms",          # high-level Bayesian survival/regression
  "rstan",         # Stan backend (alternative: cmdstanr)
  "posterior",     # posterior draws manipulation
  "bayesplot",     # MCMC diagnostics plots
  "loo",           # leave-one-out cross-validation
  "tidybayes",     # tidy posterior manipulation
  # Survival
  "survival",      # frequentist baseline
  "survminer",     # survival plots
  "cmprsk",        # competing risks
  # Tidyverse essentials
  "dplyr", "tibble", "readr", "ggplot2", "tidyr", "purrr", "stringr",
  # Output
  "knitr", "kableExtra"
)

installed <- rownames(installed.packages())
missing <- setdiff(required_pkgs, installed)

if (length(missing) == 0) {
  cat("Alle packages al geïnstalleerd:\n")
  for (p in required_pkgs) cat("  +", p, "\n")
} else {
  cat("Te installeren packages (", length(missing), "):\n", sep="")
  for (p in missing) cat("  -", p, "\n")
  cat("\nDit kan 15-30 minuten duren (vooral rstan/brms vereisen Stan-compilatie).\n")
  cat("Doorgaan? (y/n): ")
  
  # Voor non-interactieve runs: zet auto_install op TRUE
  auto_install <- TRUE
  
  if (auto_install || tolower(readline()) == "y") {
    install.packages(missing,
                     repos = "https://cloud.r-project.org/",
                     dependencies = TRUE)
  } else {
    cat("Installatie geannuleerd.\n")
    quit(status = 1)
  }
}

# Verificatie
cat("\n================================================================\n")
cat("Verificatie\n")
cat("================================================================\n")

verify_pkgs <- c("brms", "rstan", "survival", "posterior", "bayesplot")
for (p in verify_pkgs) {
  ok <- requireNamespace(p, quietly = TRUE)
  cat(sprintf("  %-15s : %s\n", p, ifelse(ok, "OK", "FAILED")))
}

# Stan rekening houden met Mac-specifieke configuratie
cat("\nStan compiler check:\n")
if (requireNamespace("rstan", quietly = TRUE)) {
  rstan::rstan_options(auto_write = TRUE)
  options(mc.cores = parallel::detectCores())
  cat(sprintf("  CPU cores available: %d\n", parallel::detectCores()))
  cat("  rstan_options(auto_write = TRUE) ingesteld\n")
}

cat("\nSetup compleet. Je kunt nu 01_bayesian_cox_baseline.R draaien.\n")
