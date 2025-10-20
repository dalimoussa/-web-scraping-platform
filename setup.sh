#!/bin/bash
# Setup script for macOS - Japanese Public Officials Scraper
# Run this to set up the project on a fresh macOS system

set -e  # Exit on error

echo "🏛️  Japanese Public Officials Scraper - macOS Setup"
echo "=================================================="
echo ""

# Check if Python 3.10+ is installed
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo "✓ Found Python $PYTHON_VERSION"
    
    # Check if version is 3.10+
    if (( $(echo "$PYTHON_VERSION < 3.10" | bc -l) )); then
        echo "⚠️  Python 3.10+ required. Current: $PYTHON_VERSION"
        echo "Installing Python 3.11 via Homebrew..."
        
        # Check for Homebrew
        if ! command -v brew &> /dev/null; then
            echo "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        brew install python@3.11
        PYTHON_CMD="python3.11"
    else
        PYTHON_CMD="python3"
    fi
else
    echo "❌ Python not found. Installing Python 3.11 via Homebrew..."
    
    # Install Homebrew if needed
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    brew install python@3.11
    PYTHON_CMD="python3.11"
fi

echo ""
echo "Creating virtual environment..."
$PYTHON_CMD -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Creating data directories..."
mkdir -p data/cache
mkdir -p data/outputs
mkdir -p data/state
mkdir -p logs

echo ""
echo "✓ Setup complete!"
echo ""
echo "To get started:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run the scraper:"
echo "     python main.py run-all"
echo ""
echo "  3. Or run specific modules:"
echo "     python main.py scrape-officials"
echo "     python main.py scrape-elections"
echo "     python main.py scrape-funding"
echo ""
echo "For help:"
echo "  python main.py --help"
echo ""
