#!/bin/bash

# This line ensures the script runs from its own directory, making file paths work correctly.
cd "$(dirname "$0")"

echo "--- Starting Daily Data Pipeline: $(date) ---"

# Define the path to the Python interpreter in your virtual environment
PYTHON_INTERP=".venv/bin/python"

echo "Step 1: Running scrape_reddit.py..."
$PYTHON_INTERP scrape_reddit.py

echo "Step 2: Running sentiment_analyzer.py..."
$PYTHON_INTERP sentiment_analyzer.py

echo "Step 3: Running signal_generator.py..."
$PYTHON_INTERP signal_generator.py

echo "--- Daily Data Pipeline Finished: $(date) ---"
