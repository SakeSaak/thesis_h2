# Makefile voor end-to-end thesis reproduction
# Usage: make all | make pijler1 | make pijler4 | make thesis | make clean

PYTHON := /opt/anaconda3/bin/python
THESIS_DIR := /Users/sakesaakstra/Desktop/thesis_h2

.PHONY: all pijler1 pijler2 pijler3 pijler4 thesis clean help

help:
	@echo "Targets:"
	@echo "  make all       — Run all analyses end-to-end (~25 min)"
	@echo "  make pijler1   — S&P Global cross-sectional + DiD analyses"
	@echo "  make pijler2   — IEA cross-validation"
	@echo "  make pijler3   — v7 → S&P matching + augmented hazard"
	@echo "  make pijler4   — Advanced robustness suite"
	@echo "  make thesis    — Recompile LaTeX chapters"
	@echo "  make clean     — Remove all intermediate output files"

all: pijler1 pijler2 pijler3 pijler4 thesis

pijler1:
	@echo "=== Pijler 1: S&P Global ==="
	cd $(THESIS_DIR)/06_thesis_extensions/09_sp_global_cbam && \
	for f in *.py; do echo "Running $$f"; $(PYTHON) $$f || exit 1; done

pijler2:
	@echo "=== Pijler 2: IEA cross-validation ==="
	cd $(THESIS_DIR)/06_thesis_extensions/10_iea_cross_validation && \
	for f in *.py; do echo "Running $$f"; $(PYTHON) $$f || exit 1; done

pijler3:
	@echo "=== Pijler 3: v7-S&P matching ==="
	cd $(THESIS_DIR)/06_thesis_extensions/11_v7_sp_matching && \
	for f in *.py; do echo "Running $$f"; $(PYTHON) $$f || exit 1; done

pijler4:
	@echo "=== Pijler 4: Advanced robustness ==="
	cd $(THESIS_DIR)/06_thesis_extensions/12_advanced_robustness && \
	for f in 01_*.py 02_*.py 03_*.py 04_*.py 05_*.py 06_*.py; do \
	    echo "Running $$f"; $(PYTHON) $$f || exit 1; \
	done

thesis:
	@echo "=== Recompile LaTeX chapters ==="
	cd $(THESIS_DIR)/07_thesis_drafts/chapter8_cbam && \
	pdflatex -interaction=nonstopmode chapter8_cbam_full.tex && \
	pdflatex -interaction=nonstopmode chapter8_cbam_full.tex && \
	pdflatex -interaction=nonstopmode chapter8_cbam_full.tex
	@echo "Chapter 8 PDF: $(THESIS_DIR)/07_thesis_drafts/chapter8_cbam/chapter8_cbam_full.pdf"

clean:
	@echo "=== Remove all derived output files ==="
	cd $(THESIS_DIR) && \
	find . -type f \( -name '*.aux' -o -name '*.log' -o -name '*.toc' -o -name '*.lof' -o -name '*.lot' -o -name '*.bbl' -o -name '*.blg' -o -name '*.fls' -o -name '*.fdb_latexmk' -o -name '*.out' -o -name '*.synctex.gz' \) -delete

.PHONY: backup
backup:
	@echo "=== Backup current results to dated archive ==="
	tar czf $(THESIS_DIR)/backup_$(shell date +%Y%m%d_%H%M%S).tar.gz \
	    $(THESIS_DIR)/06_thesis_extensions $(THESIS_DIR)/07_thesis_drafts
