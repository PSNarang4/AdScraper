from __future__ import annotations

import asyncio
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import ScraperJob, slugify
from .detection import detect_ad_cards
from .image_utils import apply_mobile_chrome
from .logging_utils import RunLog, write_batch_log
from .platforms import PLATFORMS, PlatformSpec


MOBILE_DEVICE_FALLBACK = {
    "viewport": {"width": 412, "height": 915},
    "device_scale_factor": 3.5,
    "is_mobile": True,
    "has_touch": True,
    "user_agent": (
        "Mozilla/5.0 (Linux; Android 10; SM-G988B) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112 Mobile Safari/537.36"
    ),
}


DESKTOP_DEVICE = {
    "viewport": {"width": 1280, "height": 900},
}


async def run_job(job: ScraperJob) -> RunLog:
    logs = await run_job_group([job])
    return logs[0]


async def run_job_group(jobs: list[ScraperJob]) -> list[RunLog]:
    from playwright.async_api import async_playwright

    if not jobs:
        return []

    setup_job = jobs[0]
    validate_group_jobs(jobs)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_folder = output_folder_for(setup_job, timestamp)
    logs = [build_run_log(job, timestamp) for job in jobs]

    async with async_playwright() as playwright:
        device = resolve_device(playwright, setup_job.platform)
        device_details = device_log(device)
        for log in logs:
            log.device = device_details

        context, browser = await open_browser_context(playwright, setup_job, device)
        page = await context.new_page()
        page.set_default_timeout(12000)

        try:
            spec = PLATFORMS[setup_job.platform]
            if setup_job.platform == "swiggy_instamart":
                for log in logs:
                    log.warnings.append("Stealth disabled for Swiggy Instamart because it triggers Swiggy request blocking.")
            else:
                stealth_warning = await apply_stealth(page)
                if stealth_warning:
                    for log in logs:
                        log.warnings.append(stealth_warning)

            setup_warning_start = len(logs[0].warnings)
            await prepare_platform_page(page, spec, setup_job, logs[0])
            setup_warnings = logs[0].warnings[setup_warning_start:]
            for log in logs[1:]:
                log.warnings.extend(setup_warnings)

            for job, log in zip(jobs, logs):
                try:
                    await run_keyword_capture(page, spec, job, timestamp, log, output_folder)
                except Exception as exc:
                    log.errors.append(str(exc))
                    await capture_screen_screenshot(page, job, timestamp, log, output_folder)
        except Exception as exc:
            for job, log in zip(jobs, logs):
                log.errors.append(str(exc))
                await capture_screen_screenshot(page, job, timestamp, log, output_folder)
        finally:
            await context.close()
            if browser:
                await browser.close()

    write_batch_log(output_folder, logs)
    return logs


def validate_group_jobs(jobs: list[ScraperJob]) -> None:
    setup_job = jobs[0]
    for job in jobs[1:]:
        if job.platform != setup_job.platform:
            raise ValueError("Grouped jobs must target the same platform")
        if job.city_pincode != setup_job.city_pincode:
            raise ValueError("Grouped jobs must use the same pincode/location")
        if job.output_dir != setup_job.output_dir:
            raise ValueError("Grouped jobs must use the same output directory")
        if job.user_data_dir != setup_job.user_data_dir:
            raise ValueError("Grouped jobs must use the same browser profile")
        if job.browser_channel != setup_job.browser_channel or job.headless != setup_job.headless:
            raise ValueError("Grouped jobs must use the same browser settings")
        if job.login_wait_ms != setup_job.login_wait_ms or job.login_phone != setup_job.login_phone:
            raise ValueError("Grouped jobs must use the same login settings")


def build_run_log(job: ScraperJob, timestamp: str) -> RunLog:
    return RunLog(
        run_timestamp=timestamp,
        platform=job.platform,
        keyword=job.keyword,
        brand_filter=job.brand_filter,
        city_pincode=job.city_pincode,
        match_type=job.match_type,
    )


async def inject_clean_styles(page: Any, platform: str = "") -> None:
    try:
        css = """
            /* Hide scrollbars on all elements */
            ::-webkit-scrollbar {
                display: none !important;
            }
            html, body, * {
                scrollbar-width: none !important;
                -ms-overflow-style: none !important;
            }
        """
        if platform.lower() in ("blinkit", "zepto"):
            css += """
                /* Prevent product cards from stretching vertically inside grid/flex layouts next to tall banners */
                article, li, [role="listitem"], [data-testid], [class*="product"], [class*="card"], [class*="item"] {
                    align-self: start !important;
                    align-self: flex-start !important;
                    height: auto !important;
                }
            """
        await page.add_style_tag(content=css)
    except Exception:
        pass


async def hide_original_header(page: Any, platform: str) -> None:
    try:
        await page.evaluate("""(platform) => {
            let style = document.getElementById('adscraper-custom-styles');
            if (!style) {
                style = document.createElement('style');
                style.id = 'adscraper-custom-styles';
                document.head.appendChild(style);
            }
            
            let styleText = '';
            let p = platform.toLowerCase();
            if (p === "zepto") {
                let hideSelectors = [
                    'header', '[role="banner"]', '[class*="HeaderContainer"]',
                    'div[class*="responsive-wrapper"]', '[aria-label*="App promotion banner"]',
                    'div[class*="SearchBarContainer"]',
                    'div.tw-grid.tw-grid-cols-12.tw-place-items-start',
                    'div.kc6pc', 
                    'div:has(> div > div > input[placeholder*="search" i])',
                    'div:has(> div > div > input[placeholder*="search for" i])'
                ];
                styleText = `
                    ${hideSelectors.join(', ')} {
                        display: none !important;
                    }
                    body {
                        padding-top: 84px !important;
                    }
                `;
            } else if (p === "amazon") {
                let hideSelectors = [
                    'header', '#navbar', '#nav-logobar', '#nav-searchbar', '#nav-main',
                    '#nav-search-form', '#nav-top', '#gbox-iph',
                    '[role="banner"]', 'div[class*="nav-placeholder"]'
                ];
                styleText = `
                    ${hideSelectors.join(', ')} {
                        display: none !important;
                    }
                    body {
                        padding-top: 84px !important;
                    }
                `;
            } else if (p === "flipkart") {
                let hideSelectors = [
                    'header', '[role="banner"]', 'div[class*="responsive-wrapper"]'
                ];
                let transparentSelectors = [
                    'div.nc3hzK', '[id*="guidSearch"]'
                ];
                styleText = `
                    ${hideSelectors.join(', ')} {
                        display: none !important;
                    }
                    ${transparentSelectors.join(', ')} {
                        opacity: 0 !important;
                    }
                    body {
                        padding-top: 0px !important;
                    }
                `;
            } else {
                let hideSelectors = [
                    '[role="banner"]',
                    'div[class*="responsive-wrapper"]',
                    '[aria-label*="App promotion banner"]'
                ];
                let transparentSelectors = [
                    'header',
                    '[class*="HeaderContainer"]',
                    'div[class*="SearchBarContainer"]'
                ];
                styleText = `
                    ${hideSelectors.join(', ')} {
                        display: none !important;
                    }
                    ${transparentSelectors.join(', ')} {
                        opacity: 0 !important;
                    }
                    body {
                        padding-top: 0px !important;
                    }
                `;
            }
            
            style.textContent = styleText + `
                /* Convert product list grid from 2 columns to 3 columns (span 4 instead of span 6) */
                div[style*="grid-column: span 6"],
                div[style*="grid-column:span 6"],
                div[class*="col-span-6"] {
                    grid-column: span 4 !important;
                }
                /* Reduce card padding slightly to fit the narrower 3-column layout */
                div[class*="tw-w-full"][class*="tw-px-3"] {
                    padding-left: 4px !important;
                    padding-right: 4px !important;
                }
                /* Stack price and ADD button vertically on Blinkit product cards to prevent squishing and overlap */
                div.tw-flex.tw-items-center.tw-justify-between:has(div[class*="border-base-green"]) {
                    flex-direction: column !important;
                    align-items: stretch !important;
                    gap: 4px !important;
                }
                div.tw-flex.tw-items-center.tw-justify-between:has(div[class*="border-base-green"]) > div:first-child {
                    align-self: flex-start !important;
                }
                div.tw-flex.tw-items-center.tw-justify-between:has(div[class*="border-base-green"]) > div:last-child {
                    align-self: flex-end !important;
                    margin-top: 2px !important;
                }
            `;
            
            // Adjust Flipkart's dynamic container padding and Sort/Filter bar positions
            if (p === "flipkart") {
                const headerElements = Array.from(document.querySelectorAll('*')).filter(el => {
                    const style = window.getComputedStyle(el);
                    const topVal = parseFloat(style.top) || 0;
                    return style.position === 'absolute' && topVal >= 45 && topVal <= 110 && style.display !== 'none';
                });
                
                headerElements.forEach(el => {
                    const originalTop = parseFloat(window.getComputedStyle(el).top) || 0;
                    el.style.setProperty('top', (originalTop + 32) + 'px', 'important');
                });
                
                const containerDiv = Array.from(document.querySelectorAll('div')).find(el => {
                    const pt = parseFloat(window.getComputedStyle(el).paddingTop) || 0;
                    return pt >= 95 && pt <= 170;
                });
                
                if (containerDiv) {
                    const originalPt = parseFloat(window.getComputedStyle(containerDiv).paddingTop) || 0;
                    containerDiv.style.setProperty('padding-top', (originalPt + 32) + 'px', 'important');
                }
            }
        }""", platform)
    except Exception:
        pass


async def restore_original_header(page: Any) -> None:
    try:
        await page.evaluate("""() => {
            const style = document.getElementById('adscraper-custom-styles');
            if (style) {
                style.remove();
            }
        }""")
    except Exception:
        pass


async def prepare_platform_page(page: Any, spec: PlatformSpec, job: ScraperJob, log: RunLog) -> None:
    await page.goto(spec.base_url, wait_until="domcontentloaded", timeout=30000)
    await inject_clean_styles(page, job.platform)
    await human_delay()
    if job.platform == "swiggy_instamart":
        await page.wait_for_timeout(12000)
        await recover_swiggy_error_page(page, log)
    await dismiss_obvious_modals(page)
    await handle_login(page, spec, job, log)
    await set_location(page, spec, job.city_pincode, log)
    await dismiss_obvious_modals(page)
    await inject_clean_styles(page, job.platform)


async def recover_swiggy_error_page(page: Any, log: RunLog, max_attempts: int = 10) -> None:
    for attempt in range(1, max_attempts + 1):
        state = await swiggy_error_state(page)
        if state != "something_went_wrong":
            return

        log.warnings.append(f"Swiggy showed 'Something went wrong'; retrying refresh {attempt}/{max_attempts}.")
        clicked_retry = False
        for selector in ("button:has-text('Retry')", "text=/retry/i", "button:has-text('Try Again')"):
            try:
                locator = page.locator(selector).first
                if await locator.count() and await locator.is_visible(timeout=1000):
                    await locator.click()
                    clicked_retry = True
                    break
            except Exception:
                continue

        if not clicked_retry:
            try:
                await page.reload(wait_until="domcontentloaded", timeout=30000)
            except Exception:
                await page.goto(page.url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)

    if await swiggy_error_state(page) == "something_went_wrong":
        log.warnings.append("Swiggy still showed 'Something went wrong' after 10 refresh attempts.")


async def swiggy_error_state(page: Any) -> str | None:
    try:
        body = (await page.locator("body").inner_text(timeout=5000)).lower()
    except Exception:
        return None
    if "something went wrong" in body:
        return "something_went_wrong"
    if "request blocked" in body or "looks automated" in body:
        return "request_blocked"
    return None


async def run_keyword_capture(
    page: Any,
    spec: PlatformSpec,
    job: ScraperJob,
    timestamp: str,
    log: RunLog,
    output_folder: Path,
) -> None:
    await restore_original_header(page)
    await dismiss_obvious_modals(page)
    await reset_scroll(page)
    await search_keyword(page, spec, job.keyword)
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=15000)
    except Exception:
        pass
    try:
        if job.platform == "zepto":
            await page.wait_for_selector("[data-slot-id='ProductImageWrapper']", timeout=10000)
        elif job.platform == "blinkit":
            await page.wait_for_selector("article, li, [role='listitem'], [data-testid]", timeout=10000)
        elif job.platform == "amazon":
            await page.wait_for_selector(".s-result-item, [data-component-type='s-search-result']", timeout=10000)
        elif job.platform == "flipkart":
            await page.wait_for_selector("[data-id], .css-g5y9jx", timeout=10000)
    except Exception:
        pass
    await inject_clean_styles(page, job.platform)
    await human_delay(job.wait_ms)

    if await bot_or_captcha_detected(page):
        log.warnings.append("CAPTCHA or bot-detection page detected; job skipped.")
        await capture_screen_screenshot(page, job, timestamp, log, output_folder)
        return
    # Focus and trigger suggestions list on Blinkit
    if job.platform == "blinkit":
        try:
            triggered_info = await page.evaluate("""() => {
                const inputs = Array.from(document.querySelectorAll("input"));
                const visibleInput = inputs.find(el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                });
                if (visibleInput) {
                    visibleInput.focus();
                    visibleInput.click();
                    const val = visibleInput.value;
                    if (!val.endsWith(' ')) {
                        visibleInput.value = val + ' ';
                        visibleInput.dispatchEvent(new Event('input', { bubbles: true }));
                        visibleInput.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    return "Found input. Value: '" + val + "' -> '" + visibleInput.value + "'";
                }
                return "No visible input found out of " + inputs.length + " inputs. Classes: " + inputs.map(i => i.className).join(', ');
            }""")
            print("TRIGGER INFO:", triggered_info)
            await page.wait_for_timeout(1000)
        except Exception as e:
            print("TRIGGER ERROR:", e)

    # Hide the original header now that searching is complete and screenshots are starting
    await hide_original_header(page, job.platform)
    await page.wait_for_timeout(1000)

    if job.save_screen:
        await capture_screen_screenshot(page, job, timestamp, log, output_folder)

    seen_card_keys: set[str] = set()
    raw_cards_seen = 0
    matching_cards_seen = 0
    placement_count = 0
    used_position_fallback = False

    for scroll_index in range(max(job.scroll_depth, 0) + 1):
        previous_placement_count = placement_count
        raw_count, matched_count, placement_count, used_position = await capture_visible_ad_placement(
            page,
            job,
            timestamp,
            log,
            output_folder,
            seen_card_keys,
            placement_count,
            scroll_index,
        )
        raw_cards_seen += raw_count
        matching_cards_seen += matched_count
        used_position_fallback = used_position_fallback or used_position

        if job.first_placement_only and placement_count > previous_placement_count:
            break

        if scroll_index < max(job.scroll_depth, 0):
            await scroll_results(page, random.randint(500, 850))
            await human_delay(job.wait_ms)

    if used_position_fallback:
        log.warnings.append("Position heuristic used; review captured cards manually.")

    log.total_sponsored_cards_found = matching_cards_seen

    if matching_cards_seen == 0:
        if raw_cards_seen == 0:
            message = f"0 tagged ads found in the first {max(job.scroll_depth, 0)} scroll(s)"
        elif job.brand_filter:
            message = "matching brand/keyword not found in tagged ads"
        else:
            message = "keyword not found in tagged ads"
        log.warnings.append(message)
        if job.save_screen:
            await capture_screen_screenshot(page, job, timestamp, log, output_folder)
        return

    if job.save_screen:
        await capture_screen_screenshot(page, job, timestamp, log, output_folder)

    if job.save_full_page:
        output_folder.mkdir(parents=True, exist_ok=True)
        full_page_name = file_name_for(job, timestamp, "full_page")
        full_page_path = output_folder / full_page_name
        await page.screenshot(path=str(full_page_path), full_page=True, scale="css")
        log.screenshots_saved.append(str(full_page_path))


async def open_browser_context(
    playwright: Any,
    job: ScraperJob,
    device: dict[str, Any],
) -> tuple[Any, Any | None]:
    args = [
        "--disable-blink-features=AutomationControlled",
        "--no-first-run",
        "--disable-dev-shm-usage",
    ]
    if not job.headless:
        viewport = device.get("viewport", {})
        # Add padding to window width and height to ensure the emulated viewport fits
        # inside the browser window without scaling/clipping or displaying scrollbars.
        width = int(viewport.get("width") or 520) + 150
        height = int(viewport.get("height") or 1080) + 200
        args.append(f"--window-size={width},{height}")

    if job.user_data_dir:
        job.user_data_dir.mkdir(parents=True, exist_ok=True)
        launch_options: dict[str, Any] = {
            **device,
            "headless": job.headless,
            "args": args,
        }
        if job.browser_channel != "chromium":
            launch_options["channel"] = job.browser_channel
        context = await playwright.chromium.launch_persistent_context(
            str(job.user_data_dir),
            **launch_options,
        )
        return context, None

    launch_options = {
        "headless": job.headless,
        "args": args,
    }
    if job.browser_channel != "chromium":
        launch_options["channel"] = job.browser_channel
    browser = await playwright.chromium.launch(**launch_options)
    context = await browser.new_context(**device)
    return context, browser


def resolve_device(playwright: Any, platform: str = "") -> dict[str, Any]:
    if platform == "swiggy_instamart":
        return dict(DESKTOP_DEVICE)
    device = playwright.devices.get("Samsung Galaxy S20 Ultra")
    if device:
        return dict(device)
    return dict(MOBILE_DEVICE_FALLBACK)


def device_log(device: dict[str, Any]) -> dict[str, Any]:
    viewport = device.get("viewport", {})
    return {
        "viewport_width": viewport.get("width"),
        "viewport_height": viewport.get("height"),
        "device_scale_factor": device.get("device_scale_factor"),
        "is_mobile": device.get("is_mobile"),
        "has_touch": device.get("has_touch"),
        "user_agent": device.get("user_agent"),
    }


async def apply_stealth(page: Any) -> str | None:
    try:
        from playwright_stealth import Stealth
    except ImportError:
        try:
            from playwright_stealth import stealth_async
        except ImportError:
            return "playwright-stealth is not installed; continuing without stealth."

        try:
            await stealth_async(page)
        except Exception as exc:
            return f"playwright-stealth failed to initialize: {exc}"
        return None

    try:
        await Stealth().apply_stealth_async(page)
    except Exception as exc:
        return f"playwright-stealth failed to initialize: {exc}"
    return None


async def capture_screen_screenshot(
    page: Any,
    job: ScraperJob,
    timestamp: str,
    log: RunLog,
    output_folder: Path,
) -> None:
    if not job.save_screen or log.screen_screenshots_saved:
        return

    try:
        output_folder.mkdir(parents=True, exist_ok=True)
        file_name = file_name_for(job, timestamp, "screen")
        screenshot_path = output_folder / file_name
        await page.screenshot(path=str(screenshot_path), full_page=False, scale="css")
        apply_mobile_chrome(screenshot_path, job.keyword, platform=job.platform)
        log.screen_screenshots_saved.append(str(screenshot_path))
    except Exception as exc:
        log.warnings.append(f"Could not save mobile screen screenshot: {exc}")


async def capture_visible_ad_placement(
    page: Any,
    job: ScraperJob,
    timestamp: str,
    log: RunLog,
    output_folder: Path,
    seen_card_keys: set[str],
    placement_count: int,
    scroll_index: int,
) -> tuple[int, int, int, bool]:
    cards = await detect_ad_cards(page, job.allow_position_fallback, job.platform, job.require_ad_tag)
    used_position_fallback = any(card["reason"] == "position" for card in cards)
    matching_cards = filter_cards_for_job(cards, job)

    fresh_cards = []
    fresh_keys = []
    fresh_key_set = set()
    for card in matching_cards:
        key = card_key(card)
        if key in seen_card_keys or key in fresh_key_set:
            continue
        fresh_cards.append(card)
        fresh_keys.append(key)
        fresh_key_set.add(key)

    if not fresh_cards:
        return len(cards), 0, placement_count, used_position_fallback

    saved_count = 0
    output_folder.mkdir(parents=True, exist_ok=True)
    last_saved_screenshot_path = None
    for card in sorted(fresh_cards, key=lambda item: (item.get("rect", {}).get("y", 0), item.get("rect", {}).get("x", 0))):
        try:
            next_placement_count = placement_count + 1
            file_name = file_name_for(job, timestamp, f"placement_{next_placement_count}")
            screenshot_path = output_folder / file_name
            # Scroll the card to the center of the viewport to ensure the entire card
            # (including pricing, brand details, and ADD button) is fully visible.
            card_id = card.get("id")
            is_fully_visible = False
            if card_id:
                card_locator = page.locator(f"[data-adscraper-capture-id='{card_id}']")
                if await card_locator.count() > 0:
                    box = await card_locator.bounding_box()
                    if box:
                        viewport = page.viewport_size or {"width": 412, "height": 915}
                        vw = viewport["width"]
                        vh = viewport["height"]
                        # Check if card is fully within viewport (below the 84px header)
                        if (box["x"] >= 0 and 
                            box["y"] >= 84 and 
                            (box["x"] + box["width"]) <= vw and 
                            (box["y"] + box["height"]) <= vh):
                            is_fully_visible = True
                    
                    if not is_fully_visible:
                        await center_locator(card_locator)
                        await human_delay(300, 600)  # Brief delay to let layout settle

            if is_fully_visible and last_saved_screenshot_path is not None:
                # Reuse the last screenshot to prevent duplicate files on disk
                log.ad_placements.append(placement_record_for(job, card, last_saved_screenshot_path, placement_count, scroll_index))
            else:
                await page.screenshot(path=str(screenshot_path), full_page=False, scale="css")
                apply_mobile_chrome(screenshot_path, job.keyword, platform=job.platform)
                log.screenshots_saved.append(str(screenshot_path))
                log.ad_placements.append(placement_record_for(job, card, screenshot_path, next_placement_count, scroll_index))
                placement_count = next_placement_count
                last_saved_screenshot_path = screenshot_path
                saved_count += 1
        except Exception as exc:
            log.warnings.append(f"Could not save placement screenshot: {exc}")

    seen_card_keys.update(fresh_keys)
    return len(cards), saved_count, placement_count, used_position_fallback


def placement_record_for(
    job: ScraperJob,
    card: dict[str, Any],
    screenshot_path: Path,
    placement_index: int,
    scroll_index: int,
) -> dict[str, Any]:
    return {
        "keyword": job.keyword,
        "brand_filter": job.brand_filter,
        "placement_index": placement_index,
        "scroll_index": scroll_index,
        "result_slot": card.get("resultSlot"),
        "ad_slot": card.get("adSlot"),
        "detection_reason": card.get("reason"),
        "screenshot_path": str(screenshot_path),
        "text": card.get("text", ""),
        "rect": card.get("rect", {}),
    }


async def dismiss_obvious_modals(page: Any) -> None:
    selectors = (
        "button:has-text('Continue on web')",
        "text=/continue on web/i",
        "button[aria-label*='close' i]",
        "[role='button'][aria-label*='close' i]",
        "button[class*='close' i]",
        "button:has-text('Not now')",
        "button:has-text('Maybe later')",
        "button:has-text('Skip')",
    )
    for _ in range(2):
        clicked = False
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if await locator.count() and await locator.is_visible(timeout=800):
                    await locator.click()
                    await human_delay(300, 900)
                    clicked = True
                    break
            except Exception:
                continue
        if not clicked:
            break
    try:
        await page.keyboard.press("Escape")
    except Exception:
        pass


async def handle_login(page: Any, spec: PlatformSpec, job: ScraperJob, log: RunLog) -> None:
    if not job.login_phone and job.login_wait_ms <= 0:
        return

    await open_login_form(page, spec)
    if job.login_phone:
        if await fill_login_phone(page, spec, job.login_phone):
            await click_login_continue(page)
            log.warnings.append("Login phone number entered; complete OTP if the site asks for it.")
        else:
            log.warnings.append("Login phone field was not found; waiting for manual login if login_wait_ms is set.")
    else:
        await scroll_first_login_input_into_view(page, spec)

    if job.login_wait_ms > 0:
        await page.wait_for_timeout(job.login_wait_ms)
        await dismiss_obvious_modals(page)


async def open_login_form(page: Any, spec: PlatformSpec) -> None:
    for selector in spec.login_triggers:
        try:
            locator = page.locator(selector).first
            if await locator.count() and await locator.is_visible(timeout=1200):
                await locator.click()
                await human_delay(800, 1600)
                return
        except Exception:
            continue


async def fill_login_phone(page: Any, spec: PlatformSpec, phone: str) -> bool:
    for selector in spec.login_inputs:
        try:
            field = page.locator(selector).first
            if await field.count() and await field.is_visible(timeout=2000):
                await center_locator(field)
                await field.click()
                await field.fill(phone)
                await human_delay(700, 1400)
                return True
        except Exception:
            continue
    return False


async def scroll_first_login_input_into_view(page: Any, spec: PlatformSpec) -> None:
    for selector in spec.login_inputs:
        try:
            field = page.locator(selector).first
            if await field.count() and await field.is_visible(timeout=1000):
                await center_locator(field)
                await field.click()
                return
        except Exception:
            continue


async def click_login_continue(page: Any) -> None:
    for selector in (
        "button:has-text('Continue')",
        "button:has-text('Submit')",
        "button:has-text('Next')",
        "button:has-text('Send OTP')",
        "text=/send otp/i",
        "text=/continue/i",
    ):
        try:
            locator = page.locator(selector).first
            if await locator.count() and await locator.is_visible(timeout=1200):
                await locator.click()
                await human_delay(1200, 2200)
                return
        except Exception:
            continue

    try:
        await page.keyboard.press("Enter")
        await human_delay(1200, 2200)
    except Exception:
        pass


async def center_locator(locator: Any) -> None:
    try:
        await locator.scroll_into_view_if_needed(timeout=2000)
    except Exception:
        pass
    try:
        await locator.evaluate("el => el.scrollIntoView({ block: 'center', inline: 'center' })")
    except Exception:
        pass


async def set_location(page: Any, spec: PlatformSpec, pincode: str, log: RunLog) -> None:
    trigger_clicked = False
    for trigger in spec.location_triggers:
        try:
            locator = page.locator(trigger).first
            if await locator.is_visible(timeout=300):
                await locator.click()
                trigger_clicked = True
                break
        except Exception:
            continue

    # Wait up to 3 seconds for location input to appear (either from trigger click or automatic modal popup)
    for _ in range(15):
        found = False
        for selector in spec.location_inputs:
            try:
                if await page.locator(selector).first.is_visible(timeout=0):
                    found = True
                    break
                # Let's also check if manual location button is visible
                if _ == 0:
                    for manual_sel in (
                        "button:has-text('Select manually')",
                        "text=/select manually/i",
                        "button:has-text('Enter manually')",
                        "text=/enter manually/i",
                    ):
                        if await page.locator(manual_sel).first.is_visible(timeout=0):
                            found = True
                            break
            except Exception:
                pass
        if found:
            break
        await page.wait_for_timeout(200)

    # Check if manual location option or location input is visible. If not, exit silently (location already configured).
    input_visible = False
    for selector in spec.location_inputs:
        try:
            if await page.locator(selector).first.is_visible(timeout=0):
                input_visible = True
                break
        except Exception:
            pass
    
    manual_visible = False
    for selector in (
        "button:has-text('Select manually')",
        "text=/select manually/i",
        "button:has-text('Enter manually')",
        "text=/enter manually/i",
    ):
        try:
            if await page.locator(selector).first.is_visible(timeout=0):
                manual_visible = True
                break
        except Exception:
            pass

    if not trigger_clicked and not input_visible and not manual_visible:
        # Location already set, return silently
        return

    await click_manual_location_option(page)

    for selector in spec.location_inputs:
        try:
            field = page.locator(selector).first
            if await field.is_visible(timeout=300):
                await center_locator(field)
                await field.click()
                await field.fill(pincode)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(1500)
                await click_first_location_suggestion(page, pincode)
                return
        except Exception:
            continue

    log.warnings.append("Location input was not found; continuing with existing/default location.")


async def click_manual_location_option(page: Any) -> None:
    for selector in (
        "button:has-text('Select manually')",
        "text=/select manually/i",
        "button:has-text('Enter manually')",
        "text=/enter manually/i",
        "text=/enter an Indian pincode/i",
        "text=/enter a pincode/i",
        "#GLUXChangePostalCodeLink",
    ):
        try:
            locator = page.locator(selector).first
            if await locator.is_visible(timeout=200):
                await locator.click()
                await page.wait_for_timeout(500)
                return
        except Exception:
            continue


async def click_first_location_suggestion(page: Any, pincode: str) -> None:
    candidates = (
        f"text=/{pincode}/",
        "li >> nth=0",
        "[role='option'] >> nth=0",
        "button:has-text('Confirm')",
        "button:has-text('Continue')",
    )
    for selector in candidates:
        try:
            locator = page.locator(selector).first
            if await locator.is_visible(timeout=300):
                await locator.click()
                await page.wait_for_timeout(1000)
                return
        except Exception:
            continue


async def reset_scroll(page: Any) -> None:
    try:
        await page.evaluate(
            """
            () => {
              window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
              const elements = Array.from(document.querySelectorAll('main, [role="main"], section, div'));
              elements
                .filter((el) => el.scrollHeight > el.clientHeight + 50)
                .forEach((el) => { el.scrollTop = 0; });
            }
            """
        )
    except Exception:
        try:
            await page.keyboard.press("Home")
        except Exception:
            pass


async def scroll_results(page: Any, delta_y: int) -> None:
    scrolled = False
    try:
        scrolled = await page.evaluate(
            """
            (deltaY) => {
              const viewportHeight = window.innerHeight || 915;
              const candidates = Array.from(document.querySelectorAll('main, [role="main"], section, div'))
                .filter((el) => {
                  const style = window.getComputedStyle(el);
                  const rect = el.getBoundingClientRect();
                  const canScroll = el.scrollHeight > el.clientHeight + 50;
                  const visible = rect.bottom > 80 && rect.top < viewportHeight && rect.width > 200 && rect.height > 180;
                  const overflow = /(auto|scroll)/.test(style.overflowY);
                  return canScroll && visible && (overflow || rect.height >= viewportHeight * 0.35);
                })
                .sort((a, b) => {
                  const ar = a.getBoundingClientRect();
                  const br = b.getBoundingClientRect();
                  return (br.height * br.width) - (ar.height * ar.width);
                });

              const target = candidates[0] || document.scrollingElement || document.documentElement;
              const before = target.scrollTop;
              target.scrollBy({ top: deltaY, left: 0, behavior: 'instant' });
              if (Math.abs(target.scrollTop - before) > 2) return true;

              const windowBefore = window.scrollY;
              window.scrollBy({ top: deltaY, left: 0, behavior: 'instant' });
              return Math.abs(window.scrollY - windowBefore) > 2;
            }
            """,
            delta_y,
        )
    except Exception:
        scrolled = False

    if not scrolled:
        try:
            await page.mouse.move(206, 700)
            await page.mouse.wheel(0, delta_y)
        except Exception:
            try:
                await page.keyboard.press("PageDown")
            except Exception:
                pass


async def search_keyword(page: Any, spec: PlatformSpec, keyword: str) -> None:
    import urllib.parse
    plat = spec.key.lower()
    if plat == "flipkart":
        url = f"https://www.flipkart.com/search?q={urllib.parse.quote(keyword)}"
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return
    if plat == "amazon":
        url = f"https://www.amazon.in/s?k={urllib.parse.quote(keyword)}"
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return

    # First, try to fill the search input directly if it's already visible
    for selector in spec.search_selectors:
        try:
            field = page.locator(selector).first
            if await field.is_visible(timeout=200):
                await center_locator(field)
                await field.click()
                await field.fill(keyword)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(1500)
                try:
                    if spec.key.lower() != "blinkit":
                        await page.evaluate("document.activeElement.blur()")
                except Exception:
                    pass
                return
        except Exception:
            continue

    # If not visible, click the trigger to open the search bar/field
    trigger_clicked = False
    for trigger in spec.search_triggers:
        try:
            locator = page.locator(trigger).first
            if await locator.is_visible(timeout=500):
                await locator.click()
                trigger_clicked = True
                break
        except Exception:
            continue

    if trigger_clicked:
        # Wait up to 3 seconds for search input to appear
        for _ in range(15):
            found = False
            for selector in spec.search_selectors:
                try:
                    if await page.locator(selector).first.is_visible(timeout=0):
                        found = True
                        break
                except Exception:
                    pass
            if found:
                break
            await page.wait_for_timeout(200)

    # Try to find and fill the input again
    for selector in spec.search_selectors:
        try:
            field = page.locator(selector).first
            if await field.is_visible(timeout=300):
                await center_locator(field)
                await field.click()
                await field.fill(keyword)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(1500)
                try:
                    if spec.key.lower() != "blinkit":
                        await page.evaluate("document.activeElement.blur()")
                except Exception:
                    pass
                return
        except Exception:
            continue

    raise RuntimeError("Search input was not found")


async def bot_or_captcha_detected(page: Any) -> bool:
    content = (await page.locator("body").inner_text(timeout=5000)).lower()
    signals = ("captcha", "verify you are human", "unusual traffic", "robot", "access denied", "blocked")
    return any(signal in content for signal in signals)


def filter_cards_for_job(cards: list[dict[str, Any]], job: ScraperJob) -> list[dict[str, Any]]:
    brand_lower = job.brand_filter.strip().lower()
    if "parachute" in brand_lower:
        matched_cards = []
        for card in cards:
            card_text = card.get("text", "")
            # Ensure it is a Parachute card
            if not text_matches_filter(card_text, job.brand_filter):
                continue

            # Normalize keyword and card text tokens
            keyword_toks = normalized_tokens(job.keyword)
            card_toks = set(normalized_tokens(card_text))

            # Specific Keywords check
            is_rosemary_essential = "rosemary" in keyword_toks and "essential" in keyword_toks
            is_rosemary_oil = "rosemary" in keyword_toks and "oil" in keyword_toks and "essential" not in keyword_toks
            is_bhringraj = "bhringraj" in keyword_toks

            if is_rosemary_essential:
                # Must be advanced rosemary essential oil
                if "rosemary" in card_toks and "essential" in card_toks and "enriched" not in card_toks:
                    matched_cards.append(card)
            elif is_rosemary_oil:
                # Must be advanced rosemary enriched coconut hair oil
                if "rosemary" in card_toks and ("enriched" in card_toks or "coconut" in card_toks or "hair" in card_toks) and "essential" not in card_toks:
                    matched_cards.append(card)
            elif is_bhringraj:
                # Must be bhringraj hair oil
                if "bhringraj" in card_toks:
                    matched_cards.append(card)
            else:
                # Generic or competition keyword -> match any Parachute card
                matched_cards.append(card)
        return matched_cards

    return [
        card
        for card in cards
        if text_matches_filter(card.get("text", ""), job.brand_filter)
        and keyword_matches(card.get("text", ""), job.keyword, job.match_type)
    ]


CATEGORY_FILTER_LABELS = {
    "s&c",
    "s c",
    "s and c",
    "shampoo conditioner",
    "shampoo and conditioner",
    "shampoo & conditioner",
}


def text_matches_filter(text: str, filter_value: str) -> bool:
    value = filter_value.strip()
    if not value or value.lower() in {"all", "any", "*"}:
        return True

    normalized_filter = " ".join(normalized_tokens(value))
    if value.lower() in CATEGORY_FILTER_LABELS or normalized_filter in CATEGORY_FILTER_LABELS:
        return True

    text_lower = text.lower()
    value_lower = value.lower()
    if value_lower in text_lower:
        return True

    text_tokens = set(normalized_tokens(text))
    return all(token in text_tokens for token in normalized_tokens(value))


def keyword_matches(text: str, keyword: str, match_type: str) -> bool:
    if match_type == "none":
        return True

    text_tokens = normalized_tokens(text)
    keyword_tokens = normalized_tokens(keyword)
    if not keyword_tokens:
        return True

    if match_type == "broad":
        text_token_set = set(text_tokens)
        return all(token in text_token_set for token in keyword_tokens)

    return contains_sequence(text_tokens, keyword_tokens)


def contains_sequence(tokens: list[str], needle: list[str]) -> bool:
    if len(needle) > len(tokens):
        return False
    for start in range(len(tokens) - len(needle) + 1):
        if tokens[start : start + len(needle)] == needle:
            return True
    return False


def normalized_tokens(value: str) -> list[str]:
    return [normalize_token(token) for token in re.findall(r"[a-z0-9]+", value.lower()) if token]


def normalize_token(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return f"{token[:-3]}y"
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def card_key(card: dict[str, Any]) -> str:
    text = " ".join(normalized_tokens(card.get("text", "")))
    if text:
        return text
    rect = card.get("rect", {})
    return f"{rect.get('x')}:{rect.get('y')}:{rect.get('width')}:{rect.get('height')}"


def output_folder_for(job: ScraperJob, timestamp: str) -> Path:
    return job.output_dir / slugify(job.platform) / timestamp


def file_name_for(job: ScraperJob, timestamp: str, suffix: str) -> str:
    platform = slugify(job.platform)
    keyword = slugify(job.keyword)
    brand = slugify(job.brand_filter)
    return f"{platform}__{keyword}__{brand}__{timestamp}__{suffix}.png"


async def human_delay(base_ms: int | None = None, max_ms: int | None = None) -> None:
    # Scale down all human-like delays by a factor of 2.5 to increase execution speed by 2x - 3x comfortably
    SPEED_FACTOR = 2.5
    if base_ms is None:
        low, high = int(300 / SPEED_FACTOR), int(1200 / SPEED_FACTOR)
    elif max_ms is None:
        scaled_base = int(base_ms / SPEED_FACTOR)
        low = max(100, int(scaled_base * 0.75))
        high = max(low + 1, int(scaled_base * 1.25))
    else:
        low, high = int(base_ms / SPEED_FACTOR), int(max_ms / SPEED_FACTOR)
    await asyncio.sleep(random.randint(low, high) / 1000)
