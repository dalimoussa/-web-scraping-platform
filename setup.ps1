# Japanese Public Officials Scraper - Windows Setup
# PowerShell script for Windows users

Write-Host "🏛️  Japanese Public Officials Scraper - Windows Setup" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found $pythonVersion" -ForegroundColor Green
    
    # Extract version number
    $version = $pythonVersion -replace '.*(\d+\.\d+).*', '$1'
    if ([version]$version -lt [version]"3.10") {
        Write-Host "⚠️  Python 3.10+ required. Please install from https://www.python.org/downloads/" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Python not found. Please install Python 3.10+ from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host ""
Write-Host "Creating data directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data\cache" | Out-Null
New-Item -ItemType Directory -Force -Path "data\outputs" | Out-Null
New-Item -ItemType Directory -Force -Path "data\state" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

Write-Host ""
Write-Host "✓ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To get started:" -ForegroundColor Cyan
Write-Host "  1. Activate the virtual environment:"
Write-Host "     .\venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "  2. Run the scraper:"
Write-Host "     python main.py run-all"
Write-Host ""
Write-Host "  3. Or run specific modules:"
Write-Host "     python main.py scrape-officials"
Write-Host "     python main.py scrape-elections"
Write-Host "     python main.py scrape-funding"
Write-Host ""
Write-Host "For help:"
Write-Host "  python main.py --help"
Write-Host ""
