#!/bin/bash

# Rummy Assistant - Backend Setup Script
# This script sets up the Python environment and installs dependencies

set -e  # Exit on error

echo "🎴 Rummy Assistant - Backend Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Please run this script from the server/ directory."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Add template images to templates/ranks/ and templates/suits/"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Start CV Server: python3 card_cv_server.py"
echo "4. In another terminal, start Game Engine: python3 rummy_engine.py"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source venv/bin/activate"

