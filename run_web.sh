#!/bin/bash

# Ensure we are in the project root
cd "$(dirname "$0")"

# Set PYTHONPATH to include the current directory so 'adqlm' module is found
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Check if keys are set
if [ -z "$GEMINI_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ]; then
    echo "WARNING: GEMINI_API_KEY (or GOOGLE_API_KEY) is not set. The AI features will not work."
    echo "Usage: GEMINI_API_KEY=your_key_here ./run_web.sh"
    echo "Starting anyway..."
fi

# Run the Flask app using the 'adqlm' conda environment
echo "Starting web app in 'adqlm' conda environment..."
conda run -n adqlm --no-capture-output python web/app.py
