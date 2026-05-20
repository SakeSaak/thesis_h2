# 25d_competing_risks_frailty_final.R
#
# Definitieve versie. Lost twee dimnames-issues op:
#   1. cmprsk::crr $var matrix heeft geen dimnames -> positionele indexering
#   2. coxph + frailty() summary heeft andere kolomstructuur dan gewone Cox

library(cmprsk)
library(survival)
library(dplyr)

PROJECT_ROOT <- "/Users/sakesaakstra/Desktop/thesis_h2"
CSV_FILE <- file.path(PROJECT_ROOT, "output_data/blueccs_project_level_for_R.csv")
OUT <- file.path(PROJECT_ROOT, "output_data")

df <- read.csv(CSV_FILE, stringsAsFactors = FALSE)
df$region <- factor(df$region,
  levels = c("EU","Other_Europe","North_America","Asia","ANZ","MENA","Other"))
df$sponsor_type <- factor(df$sponsor_type,
  levels = c("Oil_major","Utility","Industrial_gas","Steel",
             "Pure_play","Government","Other","Unknown"))
df$sponsor_owner <- as.factor(df$sponsor_owner)
df$event_any <- as.integer(df$event_type > 0)

cat(strrep("=", 70), "\n", sep="")
cat("DATA\n")
cat(strrep("=", 70), "\n", sep="")
cat(sprintf("  N=%d (Blue_CCS=%d, PEM=%d)\n",
            nrow(df), sum(df$is_blue_ccs==1), sum(df$is_blue_ccs==0)))
cat(sprintf("  Cancelled=%d, On-hold=%d\n",
            sum(df$event_type==1), sum(df$event_type==2)))

# ============================================================
# FINE-GRAY met POSITIONELE INDEXERING
# ============================================================
cat("\n", strrep("=", 70), "\n", sep="")
cat("FINE-GRAY (gereduceerd model: Blue_CCS + log_capacity)\n")
cat(strrep("=", 70), "\n", sep="")

X_minimal <- model.matrix(~ is_blue_ccs + log_capacity_mw, data=df)[, -1]
# Kolommen: [1] is_blue_ccs, [2] log_capacity_mw

extract_crr <- function(fit, label) {
  if (is.null(fit)) { cat(sprintf("  %s: FAILED\n", label)); return(NULL) }
  bc <- as.numeric(fit$coef[1])
  bs <- sqrt(as.numeric(fit$var[1, 1]))
  cat(sprintf("\n  %s:\n", label))
  cat(sprintf("    Blue_CCS HR = %.2f, SE = %.3f, p = %.4f\n",
              exp(bc), bs, 2*pnorm(-abs(bc/bs))))
  cat(sprintf("    95%% CI for HR: [%.2f, %.2f]\n",
              exp(bc - 1.96*bs), exp(bc + 1.96*bs)))
  invisible(list(coef=bc, se=bs, hr=exp(bc), p=2*pnorm(-abs(bc/bs)),
                 ci_low=exp(bc-1.96*bs), ci_high=exp(bc+1.96*bs)))
}

fg_cancel <- tryCatch(
  crr(ftime=df$duration, fstatus=df$event_type,
      cov1=X_minimal, failcode=1, cencode=0, maxiter=100),
  error = function(e) { cat(sprintf("    cancelled FAIL: %s\n", e$message)); NULL }
)
fg_onhold <- tryCatch(
  crr(ftime=df$duration, fstatus=df$event_type,
      cov1=X_minimal, failcode=2, cencode=0, maxiter=100),
  error = function(e) { cat(sprintf("    on-hold FAIL: %s\n", e$message)); NULL }
)

res_c <- extract_crr(fg_cancel, "Fine-Gray cancelled (event 1)")
res_h <- extract_crr(fg_onhold, "Fine-Gray on-hold (event 2)")

if (!is.null(res_c) && !is.null(res_h)) {
  cat(sprintf("\n  HR cancelled / HR on-hold ratio: %.2f\n", res_c$hr / res_h$hr))
  if (res_c$hr > res_h$hr) {
    cat("  -> Blue_CCS effect groter op TERMINAL CANCELLATION dan op delay\n")
    cat("     Interpretatie: technologie-specifieke fundamentele uitvoeringsproblemen\n")
  } else {
    cat("  -> Blue_CCS effect groter op DELAY dan op terminal cancellation\n")
    cat("     Interpretatie: real-option style wachten op policy clarity\n")
  }
}

# ============================================================
# COX BASELINE en FRAILTY
# ============================================================
cat("\n", strrep("=", 70), "\n", sep="")
cat("COX BASELINE en SHARED FRAILTY\n")
cat(strrep("=", 70), "\n", sep="")

cox_baseline <- coxph(
  Surv(duration, event_any) ~ is_blue_ccs + log_capacity_mw + region + sponsor_type,
  data = df
)
cb <- summary(cox_baseline)$coefficients["is_blue_ccs", ]
cat(sprintf("\n  Cox baseline Blue_CCS: HR = %.2f (SE = %.3f)\n",
            exp(cb["coef"]), cb["se(coef)"]))
cat(sprintf("    Concordance: %.3f\n", summary(cox_baseline)$concordance[1]))

cox_frailty <- tryCatch(
  coxph(Surv(duration, event_any) ~ is_blue_ccs + log_capacity_mw + region +
          sponsor_type + frailty(sponsor_owner, distribution="gamma"),
        data = df),
  error = function(e) { cat(sprintf("  Gamma frailty FAILED: %s\n", e$message)); NULL }
)

frailty_results <- NULL
if (!is.null(cox_frailty)) {
  s_fr <- summary(cox_frailty)$coefficients
  cat(sprintf("\n  Frailty Cox summary kolommen: %s\n",
              paste(colnames(s_fr), collapse=", ")))
  
  blue_fr <- s_fr["is_blue_ccs", ]
  c_val <- as.numeric(blue_fr["coef"])
  s_val <- as.numeric(blue_fr["se(coef)"])
  z_val <- c_val / s_val
  p_val <- 2 * pnorm(-abs(z_val))
  
  cat(sprintf("\n  Frailty Cox Blue_CCS:\n"))
  cat(sprintf("    coef = %.3f, HR = %.2f\n", c_val, exp(c_val)))
  cat(sprintf("    SE = %.3f, p = %.4f\n", s_val, p_val))
  cat(sprintf("    95%% CI for HR: [%.2f, %.2f]\n",
              exp(c_val - 1.96*s_val), exp(c_val + 1.96*s_val)))
  
  # Frailty variance
  fr_var <- NA_real_
  if (!is.null(cox_frailty$history)) {
    fr_keys <- grep("frailty", names(cox_frailty$history), value=TRUE)
    if (length(fr_keys) > 0) {
      fr_history <- cox_frailty$history[[fr_keys[1]]]
      if (!is.null(fr_history$theta)) {
        fr_var <- as.numeric(tail(fr_history$theta, 1))
      }
    }
  }
  if (!is.na(fr_var)) {
    cat(sprintf("\n  Frailty variance theta = %.4f\n", fr_var))
    if (fr_var < 0.01) cat("    -> Verwaarloosbare sponsor heterogeneity\n")
    else if (fr_var < 0.10) cat(sprintf("    -> Matige heterogeneity (CV ~ %.1f%%)\n", sqrt(fr_var)*100))
    else cat("    -> Substantiele heterogeneity\n")
  }
  
  cat(sprintf("\n  Vergelijking met baseline:\n"))
  cat(sprintf("    Cox baseline HR:      %.2f\n", exp(cb["coef"])))
  cat(sprintf("    Cox + frailty HR:     %.2f\n", exp(c_val)))
  cat(sprintf("    Verandering:          %.1f%%\n", (exp(c_val)/exp(cb["coef"]) - 1) * 100))
  
  frailty_results <- list(coef=c_val, se=s_val, hr=exp(c_val), p=p_val,
                            ci_low=exp(c_val-1.96*s_val), ci_high=exp(c_val+1.96*s_val),
                            theta=fr_var)
}

# ============================================================
# OUTPUT CSV
# ============================================================
build_row <- function(method, r, n_evt, n_sample) {
  if (is.null(r)) {
    return(data.frame(method=method, blue_ccs_hr=NA, blue_ccs_se=NA,
                       blue_ccs_p=NA, ci_low=NA, ci_high=NA,
                       n_events=n_evt, n_sample=n_sample))
  }
  data.frame(method=method, blue_ccs_hr=r$hr, blue_ccs_se=r$se,
              blue_ccs_p=r$p, ci_low=r$ci_low, ci_high=r$ci_high,
              n_events=n_evt, n_sample=n_sample)
}

results_df <- rbind(
  build_row("Fine-Gray cancelled", res_c, sum(df$event_type==1), nrow(df)),
  build_row("Fine-Gray on-hold", res_h, sum(df$event_type==2), nrow(df)),
  build_row("Cox baseline", list(hr=exp(cb["coef"]), se=cb["se(coef)"],
                                     p=cb["Pr(>|z|)"],
                                     ci_low=exp(cb["coef"]-1.96*cb["se(coef)"]),
                                     ci_high=exp(cb["coef"]+1.96*cb["se(coef)"])),
            sum(df$event_any==1), nrow(df)),
  build_row("Cox shared frailty", frailty_results, sum(df$event_any==1), nrow(df))
)

csv_out <- file.path(OUT, "25d_competing_risks_frailty_summary.csv")
write.csv(results_df, csv_out, row.names=FALSE)
cat(sprintf("\n  Saved: %s\n", csv_out))
print(results_df)

cat("\n", strrep("=", 70), "\n", sep="")
cat("VOOR PAPER v3b TABLE 3 PLACEHOLDERS:\n")
cat(strrep("=", 70), "\n", sep="")
if (!is.null(res_c)) cat(sprintf("  Fine-Gray cancelled:  HR = %.2f, CI [%.2f, %.2f], p = %.4f\n",
                                    res_c$hr, res_c$ci_low, res_c$ci_high, res_c$p))
if (!is.null(res_h)) cat(sprintf("  Fine-Gray on-hold:    HR = %.2f, CI [%.2f, %.2f], p = %.4f\n",
                                    res_h$hr, res_h$ci_low, res_h$ci_high, res_h$p))
if (!is.null(frailty_results)) cat(sprintf("  Frailty Cox:          HR = %.2f, CI [%.2f, %.2f], p = %.4f\n",
                                              frailty_results$hr, frailty_results$ci_low,
                                              frailty_results$ci_high, frailty_results$p))
cat("\nKLAAR.\n")
