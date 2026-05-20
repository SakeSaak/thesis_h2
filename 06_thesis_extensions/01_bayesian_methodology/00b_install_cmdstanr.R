# ============================================================================
# 00b_install_cmdstanr.R  (v2 - met expliciete CRAN mirror)
#
# Fix voor de rstan compile-error 'cmath file not found' op macOS 26.5.
# Switcht naar cmdstanr backend: precompiled CmdStan binaries i.p.v. on-the-fly
# C++ compilatie. Veel betrouwbaarder op moderne macOS.
# ============================================================================

# Expliciete CRAN mirror (anders krijg je "trying to use CRAN without setting a mirror")
options(repos = c(
  STAN = "https://stan-dev.r-universe.dev",
  CRAN = "https://cloud.r-project.org/"
))

cat("================================================================\n")
cat("Installing cmdstanr (alternative Stan backend)\n")
cat("================================================================\n\n")

# Stap 1: cmdstanr package
if (!requireNamespace("cmdstanr", quietly = TRUE)) {
  cat("Installing cmdstanr package...\n")
  install.packages("cmdstanr")
} else {
  cat("cmdstanr package already installed.\n")
}

# Stap 2: Toolchain check
cat("\nChecking toolchain...\n")
cmdstanr::check_cmdstan_toolchain(fix = TRUE)

# Stap 3: CmdStan binaries (~150MB download, 5-15 min compile)
cat("\nInstalling CmdStan binaries (kan 5-15 min duren)...\n")
existing <- tryCatch(cmdstanr::cmdstan_version(), error = function(e) NULL)

if (is.null(existing)) {
  cmdstanr::install_cmdstan(
    cores = parallel::detectCores(),
    overwrite = FALSE,
    quiet = FALSE
  )
} else {
  cat(sprintf("CmdStan al geïnstalleerd: versie %s\n", existing))
}

# Stap 4: Verificatie
cat("\n================================================================\n")
cat("Verificatie\n")
cat("================================================================\n")
cat(sprintf("  cmdstan path:    %s\n", cmdstanr::cmdstan_path()))
cat(sprintf("  cmdstan version: %s\n", cmdstanr::cmdstan_version()))

# Stap 5: Hello-world Stan test
cat("\nTest compile (hello world)...\n")
test_model <- "
data { int<lower=0> N; vector[N] y; }
parameters { real mu; real<lower=0> sigma; }
model { y ~ normal(mu, sigma); }
"
test_file <- tempfile(fileext = ".stan")
writeLines(test_model, test_file)
mod <- tryCatch(
  cmdstanr::cmdstan_model(test_file, compile = TRUE),
  error = function(e) {
    cat("FAIL test compile:\n"); print(e); NULL
  }
)
if (!is.null(mod)) {
  cat("  Test compile: OK\n")
  fit <- mod$sample(data = list(N = 10, y = rnorm(10)),
                    chains = 1, iter_warmup = 200, iter_sampling = 200,
                    refresh = 0, show_messages = FALSE)
  cat(sprintf("  Test sample: OK (mu mediaan = %.3f)\n",
              median(fit$draws("mu"))))
}

cat("\nCmdStanr setup compleet. Run nu:\n")
cat("  Rscript 01_bayesian_cox_baseline.R\n")
