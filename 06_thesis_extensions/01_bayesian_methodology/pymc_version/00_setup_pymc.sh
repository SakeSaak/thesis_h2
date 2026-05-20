#!/bin/bash
# Setup PyMC environment voor Bayesian survival analysis.
# Eenmalig draaien. Ongeveer 2-3 min installatie.

set -e
echo "================================================================"
echo "PyMC Environment Setup"
echo "================================================================"
echo ""

# Use Anaconda's pip
PIP="/opt/anaconda3/bin/pip"

echo "Installing PyMC stack..."
$PIP install --quiet --upgrade pymc arviz lifelines matplotlib seaborn

echo ""
echo "Verificatie:"
/opt/anaconda3/bin/python -c "
import pymc as pm
import arviz as az
import lifelines
print(f'  PyMC v{pm.__version__}')
print(f'  ArviZ v{az.__version__}')
print(f'  Lifelines v{lifelines.__version__}')
print('Setup OK.')
"
