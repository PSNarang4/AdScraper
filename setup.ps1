# Setup script for AdScraper on Windows (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
python -m venv .venv

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Cyan
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Installing Playwright Chromium browser..." -ForegroundColor Cyan
playwright install chromium

Write-Host "`nSetup complete! You can now run the scraper using:" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\python.exe scraper.py --platform amazon --keyword `"baby soap`" --brand `"parachute`" --pincode 122001 --match-type broad --scroll-depth 3" -ForegroundColor Yellow
