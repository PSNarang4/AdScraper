# Quick-Commerce & E-Commerce Ad Scraper

A robust, high-performance CLI tool and batch runner for capturing mobile viewport proof screenshots of sponsored product placements on major Indian Quick-Commerce and E-Commerce platforms: **Amazon**, **Flipkart**, **Flipkart Minutes**, **Blinkit**, and **Zepto**.

---

## 🚀 One-Command Setup (New Device Setup)

Get up and running on any new machine with a single command!

### 🪟 Windows (PowerShell)
Open PowerShell in the repository directory and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

*(Or copy-paste this direct single-line command):*
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install --upgrade pip; pip install -r requirements.txt; playwright install chromium
```

---

### 🐧 macOS / Linux (Bash / Zsh)
Open Terminal in the repository directory and run:

```bash
chmod +x setup.sh && ./setup.sh
```

*(Or copy-paste this direct single-line command):*
```bash
python3 -m venv .venv && source .venv/bin/activate && python3 -m pip install --upgrade pip && pip install -r requirements.txt && playwright install chromium
```

---

## ⚡ Quick Start

Always activate your virtual environment first if opening a new terminal session:
- **Windows (PowerShell):** `.\.venv\Scripts\Activate.ps1`
- **macOS / Linux:** `source .venv/bin/activate`

### 1. Single Keyword Scraper Commands

**Amazon:**
```powershell
python scraper.py --platform amazon --keyword "baby soap" --brand "parachute" --pincode 122001 --match-type broad --scroll-depth 3
```

**Flipkart:**
```powershell
python scraper.py --platform flipkart --keyword "hair oil" --brand "parachute" --pincode 122001 --match-type broad --scroll-depth 3
```

**Flipkart Minutes:**
```powershell
python scraper.py --platform flipkart_minutes --keyword "milk" --brand "amul" --pincode 560001 --match-type broad --scroll-depth 3
```

**Blinkit:**
```powershell
python scraper.py --platform blinkit --keyword "essential oils" --brand "parachute" --pincode 122001 --match-type broad --scroll-depth 3
```

**Zepto:**
```powershell
python scraper.py --platform zepto --keyword "mustard oil" --brand "saffola" --pincode 122001 --match-type broad --scroll-depth 3
```

---

### 2. Multi-Keyword Single Run
Search multiple keywords in sequence under a single platform session:

```powershell
python scraper.py --platform blinkit --keywords "essential oils" "rosemary oil" "tea tree oil" --brand "parachute" --pincode 122001 --match-type broad --first-placement-only
```

---

### 3. Batch Execution via YAML Configuration

Execute multiple platform/keyword scraping jobs concurrently:

```powershell
python scraper.py --config jobs.yaml --output ./screenshots
```

#### Example `jobs.yaml`:
```yaml
jobs:
  - platform: amazon
    keyword: "baby soap"
    brand: "parachute"
    pincode: "122001"
    match_type: broad
    scroll_depth: 3

  - platform: blinkit
    keyword: "hair oil"
    brand: "parachute"
    pincode: "110001"
    match_type: phrase
    first_placement_only: true

  - platform: zepto
    keyword: "mustard oil"
    brand: "saffola"
    pincode: "560001"
    match_type: broad
```

---

## 🛠️ CLI Flags & Configuration Options

| Option | Description | Default |
| :--- | :--- | :--- |
| `--platform` | Target platform (`amazon`, `flipkart`, `flipkart_minutes`, `blinkit`, `zepto`) | *Required* |
| `--keyword` | Single search keyword query | *Required (or `--keywords`) |
| `--keywords` | Space-separated list of keywords for sequential run | `None` |
| `--brand` / `--brand-filter` | Filter captured ads by brand name matching | `""` |
| `--pincode` / `--city-pincode` | Delivery location pincode to set before capture | *Required* |
| `--match-type` | Ad card matching rule: `broad`, `phrase`, `exact`, or `none` | `none` |
| `--scroll-depth` | Number of viewport scroll steps to inspect | `3` |
| `--first-placement-only` | Stop immediately after capturing the first matching ad | `false` |
| `--headful` / `--headless` | Run browser in visible window or background headless mode | `--headless` |
| `--user-data-dir` | Path to persistent browser profile directory | `None` |
| `--browser-channel` | Browser engine channel (`chromium`, `chrome`, `msedge`) | `chromium` |
| `--login-phone` | Phone number for automated login prompt filling | `""` |
| `--login-wait-ms` | Pause time (ms) for OTP completion during headful login | `0` |
| `--config` | Path to YAML or JSON batch job configuration file | `None` |
| `--output` | Root directory for output screenshots and logs | `./screenshots` |

---

## 📁 Output Directory & File Naming Structure

Screenshots and execution logs are organized dynamically:

```text
screenshots/
├── <platform>/
│   └── <YYYY-MM-DD_HH-MM-SS>/
│       ├── <platform>__<keyword>__<brand>__<timestamp>__placement_1.png
│       ├── <platform>__<keyword>__<brand>__<timestamp>__placement_2.png
│       └── run_log.json
└── aggregate_run_log.json
```

- **Placement Screenshots**: Full mobile viewport captures centered on detected sponsored ad cards (not tightly cropped clips), preserving exact visual placement proof.
- **Run Logs**: Detailed JSON breakdown recording scroll state, matching metadata, warnings, and screenshot manifests for auditability.

---

## 🔑 Persistent Sessions & Automated Login

To maintain logged-in status or bypass repeated OTP verification across scraper runs:

1. Launch in headful mode with a dedicated browser profile path:
```powershell
python scraper.py --platform blinkit --keyword "hair oil" --brand "parachute" --pincode 122001 --user-data-dir .\profiles\blinkit_session --browser-channel msedge --headful --login-phone 9876543210 --login-wait-ms 90000
```
2. Complete OTP verification once.
3. Subsequent automated runs will re-use session cookies saved under `.\profiles\blinkit_session` without needing `--login-wait-ms`.

---

## 🧪 Running Unit Tests

Verify installation integrity and core logic:

```bash
python -m unittest discover tests
```

---

## 📜 License

Internal Automation Utility for E-Commerce & Quick-Commerce Competitive Ad Tracking.
