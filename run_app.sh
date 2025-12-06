#!/bin/bash

# Script to run the Book Learning App with uv

echo "======================================"
echo "Starting Book Learning App"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found"
    echo "Please run this script from the book-learning-app directory"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ Using uv for dependency management"

# Check if LLM Studio is running
echo ""
echo "Checking LLM Studio connection..."
if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo "✅ LLM Studio is running on http://localhost:1234"
else
    echo "⚠️  LLM Studio not detected on http://localhost:1234"
    echo "   Make sure LLM Studio is running with a loaded model"
    echo "   The app will start but LLM features may not work"
fi

# Check required directories
echo ""
echo "Checking directories..."
mkdir -p data/books data/processed
echo "✅ Directories ready"

# Show configuration
echo ""
echo "======================================"
echo "Configuration:"
echo "======================================"
echo "LLM Studio URL: http://localhost:1234/v1"
echo "Upload folder: data/books/"
echo "Processed folder: data/processed/"
echo "Debug mode: True"
echo ""

# Start the app with uv
echo "======================================"
echo "Starting Flask app with uv..."
echo "======================================"
echo ""
echo "🚀 App will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uv run python app.py
