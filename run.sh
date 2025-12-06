#!/bin/bash
# Convenience script to run the app with uv or pip

if command -v uv &> /dev/null; then
    echo "Using uv to run the app..."
    uv run app.py
else
    echo "uv not found, using python..."
    echo "Install uv for faster package management: curl -LsSf https://astral.sh/uv/install.sh | sh"
    python app.py
fi
