#!/bin/bash

# FinanceApp Installation Script
# This script automates the installation and setup of FinanceApp

set -e  # Exit on any error

echo "FinanceApp Installation Script"
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.12 or higher first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.12"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION detected. FinanceApp requires Python $REQUIRED_VERSION or higher."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "✅ uv package manager detected"
    USE_UV=true
else
    echo "ℹ️  uv not found, will use pip instead"
    USE_UV=false
fi

# Create virtual environment if using pip
if [ "$USE_UV" = false ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created and activated"
fi

# Install dependencies
echo "📥 Installing dependencies..."
if [ "$USE_UV" = true ]; then
    uv sync
else
    pip install -r requirements.txt
fi
echo "✅ Dependencies installed"

# Download spaCy model
echo "🧠 Downloading spaCy language model..."
if [ "$USE_UV" = true ]; then
    uv run python -m spacy download en_core_web_lg
else
    python -m spacy download en_core_web_lg
fi
echo "✅ spaCy model downloaded"

# Test the installation
echo "🧪 Testing the installation..."
if [ "$USE_UV" = true ]; then
    uv run python -c "import fastapi, spacy; print('✅ All imports successful')"
else
    python -c "import fastapi, spacy; print('✅ All imports successful')"
fi

echo ""
echo "FinanceApp installation completed successfully!"
echo ""
echo "To start the application:"
if [ "$USE_UV" = true ]; then
    echo "  uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
else
    echo "  source venv/bin/activate"
    echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
fi
echo ""
echo "Then visit: http://localhost:8000/docs for the API documentation"
echo ""
