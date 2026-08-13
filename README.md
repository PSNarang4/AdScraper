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

## 📋 Running Scrapers for Your Own Brand & Keywords

You can easily set up your own brand and custom keyword list in a `.yaml` configuration file and run the scraper with persistent browser sessions and headful/headless controls.

### Step 1: Create Your Custom Keyword YAML File

Create a YAML file (e.g., `MyBrand_Keywords.yaml`) in the project directory:

```yaml
jobs:
  - platform: amazon
    keyword: Shampoo
    brand: Parachute
    pincode: '122001'

  - platform: amazon
    keyword: anti hairfall shampoo
    brand: Parachute
    pincode: '122001'

  - platform: amazon
    keyword: coconut milk shampoo
    brand: Parachute
    pincode: '122001'
```

---

### Step 2: Run Batch Commands with CLI Overrides

Pass your YAML file with `--config` and customize flags like browser profile (`--user-data-dir`), channel (`--browser-channel`), headful mode (`--headful`), placement limits (`--first-placement-only`), and scroll depth (`--scroll-depth`).

CLI flags passed on the command line automatically apply to **all jobs** in your YAML file!

#### 🛒 Amazon Custom Run:
```powershell
.\.venv\Scripts\python.exe scraper.py --config Amazon_SC.yaml --user-data-dir .\profiles\amazon-edge --browser-channel msedge --headful --first-placement-only --scroll-depth 3
```

#### 🛍️ Flipkart Custom Run:
```powershell
.\.venv\Scripts\python.exe scraper.py --config Flipkart_SC.yaml --user-data-dir .\profiles\flipkart-edge --browser-channel msedge --headful --first-placement-only --scroll-depth 3
```

#### ⚡ Flipkart Minutes Custom Run:
```powershell
.\.venv\Scripts\python.exe scraper.py --config Flipkart_SC.yaml --platform flipkart_minutes --user-data-dir .\profiles\flipkart-minutes --browser-channel msedge --headful --first-placement-only --scroll-depth 3
```

#### 🟡 Blinkit Custom Run:
```powershell
.\.venv\Scripts\python.exe scraper.py --config blinkit_keywords.yaml --user-data-dir .\profiles\blinkit-edge --browser-channel msedge --headful --first-placement-only --scroll-depth 3
```

#### 🟣 Zepto Custom Run:
```powershell
.\.venv\Scripts\python.exe scraper.py --config zepto_keywords.yaml --user-data-dir .\profiles\zepto-edge --browser-channel msedge --headful --first-placement-only --scroll-depth 3
```

---

## ⚡ Quick Start (Single Job CLI Commands)

If you want to quickly test a single keyword without creating a YAML file:

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

### Multi-Keyword Single Command Run
Run multiple keywords sequentially without a YAML file:

```powershell
python scraper.py --platform blinkit --keywords "essential oils" "rosemary oil" "tea tree oil" --brand "parachute" --pincode 122001 --match-type broad --first-placement-only
```

---

## 🛠️ CLI Flags & Configuration Options Reference

| Option | Description | Default |
| :--- | :--- | :--- |
| `--config` | Path to YAML or JSON batch job configuration file (e.g. `Amazon_SC.yaml`) | `None` |
| `--platform` | Target platform (`amazon`, `flipkart`, `flipkart_minutes`, `blinkit`, `zepto`) | *Required in CLI or YAML* |
| `--keyword` | Single search keyword query | *Required in CLI or YAML* |
| `--keywords` | Space-separated list of keywords for sequential run | `None` |
| `--brand` / `--brand-filter` | Filter captured ads by brand name matching | `""` |
| `--pincode` / `--city-pincode` | Delivery location pincode to set before capture | *Required in CLI or YAML* |
| `--match-type` | Ad card matching rule: `broad`, `phrase`, `exact`, or `none` | `none` |
| `--scroll-depth` | Number of viewport scroll steps to inspect | `3` |
| `--first-placement-only` | Stop immediately after capturing the first matching ad | `false` |
| `--headful` / `--headless` | Run browser in visible window or background headless mode | `--headless` |
| `--user-data-dir` | Path to persistent browser profile directory (e.g. `.\profiles\amazon-edge`) | `None` |
| `--browser-channel` | Browser engine channel (`chromium`, `chrome`, `msedge`) | `chromium` |
| `--login-phone` | Phone number for automated login prompt filling | `""` |
| `--login-wait-ms` | Pause time (ms) for OTP completion during headful login | `0` |
| `--output` | Root directory for output screenshots and logs | `./screenshots` |

---

## 🔑 Persistent Sessions & Automated Login Workflow

To maintain logged-in status or bypass repeated OTP verification across scraper runs:

1. Launch in headful mode with a dedicated browser profile directory:
```powershell
.\.venv\Scripts\python.exe scraper.py --platform blinkit --keyword "hair oil" --brand "parachute" --pincode 122001 --user-data-dir .\profiles\blinkit-edge --browser-channel msedge --headful --login-phone 9876543210 --login-wait-ms 90000
```
2. Log in / complete OTP verification once during the initial pause window.
3. All future runs pointing to `--user-data-dir .\profiles\blinkit-edge` will automatically reuse your authenticated session cookies.

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

- **Placement Screenshots**: Full mobile viewport captures centered on detected sponsored ad cards, preserving exact visual placement proof.
- **Run Logs**: Detailed JSON breakdown recording scroll state, matching metadata, warnings, and screenshot manifests for auditability.

---

## 🧪 Running Unit Tests

Verify installation integrity and core logic:

```bash
python -m unittest discover tests
```

---

## 📜 License

Internal Automation Utility for E-Commerce & Quick-Commerce Competitive Ad Tracking.
