from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

from .config import ScraperJob, load_jobs_from_config
from .logging_utils import write_batch_log
from .runner import run_job_group


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture mobile screenshots of sponsored product cards on quick-commerce platforms."
    )
    parser.add_argument("--config", type=Path, help="YAML or JSON config containing a jobs list.")
    parser.add_argument("--platform", choices=("blinkit", "zepto", "swiggy_instamart", "flipkart", "amazon"), help="Platform to scrape.")
    parser.add_argument("--keyword", help="Search keyword, for example 'chips'.")
    parser.add_argument(
        "--keywords",
        nargs="+",
        help="Run the same settings for multiple keywords. Quote multi-word keywords.",
    )
    parser.add_argument("--brand", dest="brand_filter", default="", help="Optional brand/product filter.")
    parser.add_argument("--pincode", dest="city_pincode", help="Delivery pincode, for example 110001.")
    parser.add_argument(
        "--match-type",
        choices=("none", "broad", "phrase", "exact"),
        default="none",
        help="How strictly the ad card text must match the keyword.",
    )
    parser.add_argument("--output", dest="output_dir", type=Path, default=Path("./screenshots"))
    parser.add_argument("--scroll-depth", type=int, default=3)
    parser.add_argument("--wait-ms", type=int, default=1000)
    parser.add_argument("--headful", dest="headless", action="store_false", help="Show the Chromium window.")
    parser.add_argument(
        "--save-screen",
        dest="save_screen",
        action="store_true",
        help="Save an extra debug viewport screenshot only after a matching tagged ad is found.",
    )
    parser.add_argument(
        "--no-screen",
        dest="save_screen",
        action="store_false",
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--save-full-page", action="store_true", help="Also save a full-page screenshot.")
    parser.add_argument(
        "--first-placement-only",
        action="store_true",
        help="Stop after the first viewport screenshot that contains a matching ad.",
    )
    parser.add_argument(
        "--user-data-dir",
        type=Path,
        help="Persistent browser profile directory to reuse login/session/cookies.",
    )
    parser.add_argument(
        "--login-wait-ms",
        type=int,
        default=0,
        help="Wait after opening the site so you can log in or set location manually in headful mode.",
    )
    parser.add_argument(
        "--browser-channel",
        choices=("chromium", "chrome", "msedge"),
        default="chromium",
        help="Browser channel to launch. Use msedge or chrome with --user-data-dir for a persistent login profile.",
    )
    parser.add_argument(
        "--allow-position-fallback",
        dest="allow_position_fallback",
        action="store_true",
        help="Allow first-row fallback only when untagged fallback detection is also enabled.",
    )
    parser.add_argument(
        "--no-position-fallback",
        dest="allow_position_fallback",
        action="store_false",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--allow-untagged-fallback",
        dest="require_ad_tag",
        action="store_false",
        help="Allow legacy CSS/position heuristics that may capture cards without a visible Ad tag.",
    )
    parser.add_argument(
        "--login-phone",
        help="Phone number to type into the site's login form before waiting for OTP/manual completion.",
    )
    parser.set_defaults(headless=True, save_screen=False, allow_position_fallback=False, require_ad_tag=True)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        jobs = build_jobs(args)
        logs = asyncio.run(run_jobs(jobs))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    for log in logs:
        status = "ok" if not log.errors else "error"
        print(
            f"{status}: {log.platform} / {log.keyword} / {log.brand_filter or 'all'} - "
            f"{len(log.screenshots_saved)} placement screenshot(s), "
            f"{log.total_sponsored_cards_found} matching ad(s), "
            f"{len(log.screen_screenshots_saved)} screen screenshot(s), "
            f"{len(log.warnings)} warning(s), {len(log.errors)} error(s)"
        )
        for path in log.screen_screenshots_saved:
            print(f"  screen: {path}")
        for path in log.screenshots_saved:
            print(f"  placement: {path}")
        for warning in log.warnings:
            print(f"  warning: {warning}")
        for error in log.errors:
            print(f"  error: {error}")


def build_jobs(args: argparse.Namespace) -> list[ScraperJob]:
    defaults: dict[str, Any] = {
        "headless": args.headless,
        "scroll_depth": args.scroll_depth,
        "wait_ms": args.wait_ms,
        "output_dir": args.output_dir,
        "save_screen": args.save_screen,
        "save_full_page": args.save_full_page,
        "allow_position_fallback": args.allow_position_fallback,
        "require_ad_tag": args.require_ad_tag,
        "match_type": args.match_type,
        "first_placement_only": args.first_placement_only,
        "user_data_dir": args.user_data_dir,
        "browser_channel": args.browser_channel,
        "login_wait_ms": args.login_wait_ms,
        "login_phone": args.login_phone,
    }

    if args.config:
        return load_jobs_from_config(args.config, defaults)

    keywords = expand_keywords(args.keyword, args.keywords)

    required = ("platform", "city_pincode")
    missing = [name for name in required if not getattr(args, name)]
    if not keywords:
        missing.append("keyword")
    if missing:
        raise ValueError(f"Missing required arguments for single run: {', '.join('--' + m for m in missing)}")

    return [
        ScraperJob.from_mapping(
            {
                "platform": args.platform,
                "keyword": keyword,
                "brand_filter": args.brand_filter,
                "city_pincode": args.city_pincode,
                "match_type": args.match_type,
            },
            defaults,
        )
        for keyword in keywords
    ]


def expand_keywords(keyword: str | None, keywords: list[str] | None) -> list[str]:
    raw_values = []
    if keyword:
        raw_values.append(keyword)
    if keywords:
        raw_values.extend(keywords)

    expanded = []
    for value in raw_values:
        expanded.extend(part.strip() for part in value.split(","))

    return [value for value in expanded if value]


async def run_jobs(jobs: list[ScraperJob]):
    grouped_jobs = group_jobs_for_platform_sessions(jobs)
    grouped_logs = await asyncio.gather(*(run_job_group(group) for group in grouped_jobs))
    logs = [log for group in grouped_logs for log in group]

    output_dirs = {job.output_dir for job in jobs}
    if len(jobs) > 1 and len(output_dirs) == 1:
        write_batch_log(next(iter(output_dirs)), logs)

    return logs


def group_jobs_for_platform_sessions(jobs: list[ScraperJob]) -> list[list[ScraperJob]]:
    groups: dict[tuple[Any, ...], list[ScraperJob]] = {}
    for job in jobs:
        key = (
            job.platform,
            job.city_pincode,
            job.output_dir,
            job.user_data_dir,
            job.browser_channel,
            job.headless,
            job.login_wait_ms,
            job.login_phone,
        )
        groups.setdefault(key, []).append(job)
    return list(groups.values())
