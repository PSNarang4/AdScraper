#!/usr/bin/env bash
# Setup script for AdScraper on macOS/Linux
set -e

echo "Creating Python virtual environment..."
python3 -m venv .venv

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing dependencies from requirements.txt..."
python3 -m pip install --upgrade pip
pip install -r requirements.txt

echo "Installing Playwright Chromium browser..."
playwright install chromium

echo ""
echo "Setup complete! You can now run the scraper using:"
echo "  .venv/bin/python scraper.py --platform amazon --keyword 'baby soap' --brand 'parachute' --pincode 122001 --match-type broad --scroll-depth 3"
