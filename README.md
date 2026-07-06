# Quick-Commerce and E-Commerce Ad Scraper

CLI automation for capturing mobile viewport proof screenshots of sponsored
product placements on Amazon, Flipkart, Blinkit, and Zepto in mobile viewport.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

## Single Run

**Amazon:**
```powershell
python scraper.py --platform amazon --keyword "baby soap" --brand "parachute" --pincode 122001 --match-type broad --scroll-depth 3
```

**Flipkart:**
```powershell
python scraper.py --platform flipkart --keyword "hair oil" --brand "parachute" --pincode 122001 --match-type broad --scroll-depth 3
```

**Blinkit:**
```powershell
python scraper.py --platform blinkit --keyword "essential oils" --brand "parachute" --pincode 122001 --match-type broad --scroll-depth 3
```

**Zepto:**
```powershell
python scraper.py --platform zepto --keyword "mustard oil" --brand "saffola" --pincode 122001 --match-type broad --scroll-depth 3
```

Screenshots are saved under:

```text
screenshots/<platform>/<YYYY-MM-DD_HH-MM-SS>/
```

All keyword screenshots captured in the same platform session are kept together
in that timestamped folder. Sponsored placement captures use this filename
pattern:

```text
{platform}__{keyword}__{brand_filter}__{YYYY-MM-DD_HH-MM-SS}__placement_{n}.png
```

Placement screenshots are viewport screenshots, not cropped card screenshots.
If two matching ad cards are visible together, one placement screenshot can show
both cards.

By default, screenshots are saved only when a visible `Ad`/`Sponsored` tag is
detected on a card that also matches the requested brand and keyword. The
scraper checks the initial result viewport and then up to three scrolls by
default; if the brand's tagged ad is not seen there, it does not save a
screenshot.

Use `--match-type` to control how the ad card text must match the keyword:

```text
broad  - all keyword words must appear, allowing simple singular/plural forms
phrase - keyword words must appear in order as a phrase
exact  - strict phrase/product-intent match inside the card text
none   - do not filter ad cards by keyword text
```

To stop after the first matching ad placement screenshot:

```powershell
python scraper.py --platform blinkit --keyword "essential oils" --brand "parachute" --pincode 122001 --match-type broad --first-placement-only
```

To reuse a logged-in browser session, launch a persistent scraper profile in
headful mode and log in once. Use `--login-phone` to type your number into the
login form automatically, then use `--login-wait-ms` to leave time for OTP or
manual completion:

```powershell
python scraper.py --platform blinkit --keyword "essential oils" --brand "parachute" --pincode 122001 --user-data-dir .\profiles\blinkit-edge --browser-channel msedge --headful --login-phone 9999999999 --login-wait-ms 120000 --first-placement-only
```

After the login/session is saved in that profile folder, later runs can reuse it
with the same `--user-data-dir` and without `--login-wait-ms`. Avoid pointing
this at your normal Edge/Chrome profile while that browser is already open; use
a dedicated scraper profile folder instead.

To run multiple keywords with the same platform/brand/pincode settings:

```powershell
python scraper.py --platform blinkit --keywords "essential oils" "rosemary essential oil" "tea tree essential oil" --brand "parachute" --pincode 122001 --match-type broad --first-placement-only
```

For multiple keywords with the same platform, pincode, browser profile, and
login settings, the scraper opens the platform once, searches each keyword in
sequence, and keeps all captures in the same timestamped folder. Different
platform/session groups are run concurrently.

## Batch Run

```powershell
python scraper.py --config jobs.yaml --output ./screenshots
```

Batch mode groups compatible jobs into shared platform sessions. Separate
platform/session groups run concurrently.

## Notes

- The browser context uses Playwright's `Samsung Galaxy S20 Ultra` device profile
  when available, with a PRD-matched fallback of 412x915 and DPR 3.5.
- Placement screenshots are only saved when matching tagged ad cards are visible.
  Organic cards can appear in the same viewport, but they do not trigger capture.
- Extra mobile `__screen.png` debug captures are off by default. Pass
  `--save-screen` if you want an additional viewport screenshot after a matching
  tagged ad is found or when a run hits a login/CAPTCHA/error path.
- Legacy CSS/position heuristics are off by default. Use
  `--allow-untagged-fallback --allow-position-fallback` only when you knowingly
  want non-tagged fallback detection.
- CAPTCHA and login/bot-detection pages are logged and skipped. This tool does
  not solve CAPTCHAs, purchase products, or interact with carts.
- `run_log.json` is written after each job folder run, and batch runs also write
  an aggregate log in the output directory.
