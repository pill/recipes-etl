#!/bin/bash
# Activation script for recipes Python environment
# Usage: source activate.sh

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "${SCRIPT_DIR}/venv/bin/activate"

# Set PYTHONPATH to include src directory
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH}"

echo "✅ Recipes Python environment activated!"
echo "📁 PYTHONPATH set to: ${SCRIPT_DIR}/src"
echo ""
echo "Available commands:"
echo "  ./recipes --help              # Run CLI directly"
echo "  python -m recipes.cli         # Run CLI via Python"
echo "  python -m recipes.worker      # Start Temporal worker"
echo "  python -m recipes.client      # Run Temporal client"
echo ""

