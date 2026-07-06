from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SUPPORTED_PLATFORMS = {"blinkit", "zepto", "swiggy_instamart", "flipkart", "amazon"}
SUPPORTED_MATCH_TYPES = {"none", "broad", "phrase", "exact"}
SUPPORTED_BROWSER_CHANNELS = {"chromium", "chrome", "msedge"}


@dataclass(frozen=True)
class ScraperJob:
    platform: str
    keyword: str
    brand_filter: str = ""
    city_pincode: str = ""
    headless: bool = True
    scroll_depth: int = 3
    wait_ms: int = 1000
    output_dir: Path = Path("./screenshots")
    save_screen: bool = False
    save_full_page: bool = False
    allow_position_fallback: bool = False
    require_ad_tag: bool = True
    match_type: str = "none"
    first_placement_only: bool = False
    user_data_dir: Path | None = None
    browser_channel: str = "chromium"
    login_wait_ms: int = 0
    login_phone: str = ""

    @classmethod
    def from_mapping(cls, data: dict[str, Any], defaults: dict[str, Any] | None = None) -> "ScraperJob":
        values = dict(defaults or {})
        values.update(data)

        platform = normalize_platform(str(values.get("platform", "")).strip())
        keyword = str(values.get("keyword", "")).strip()
        brand_filter = str(values.get("brand_filter", values.get("brand", "")) or "").strip()
        city_pincode = str(values.get("city_pincode", values.get("pincode", "")) or "").strip()
        match_type = str(values.get("match_type", values.get("keyword_match_type", "none"))).strip().lower()
        first_placement_only = bool(values.get("first_placement_only", False))
        raw_user_data_dir = values.get("user_data_dir")
        user_data_dir = Path(raw_user_data_dir) if raw_user_data_dir else None
        browser_channel = str(values.get("browser_channel", "chromium")).strip().lower()
        login_wait_ms = int(values.get("login_wait_ms", 0))
        login_phone = str(values.get("login_phone", values.get("phone", values.get("mobile", ""))) or "").strip()

        if platform not in SUPPORTED_PLATFORMS:
            raise ValueError(f"Unsupported platform '{platform}'. Choose one of: {', '.join(sorted(SUPPORTED_PLATFORMS))}")
        if not keyword:
            raise ValueError("keyword is required")
        if not city_pincode:
            raise ValueError("city_pincode/pincode is required")
        if match_type not in SUPPORTED_MATCH_TYPES:
            raise ValueError(f"Unsupported match_type '{match_type}'. Choose one of: {', '.join(sorted(SUPPORTED_MATCH_TYPES))}")
        if browser_channel not in SUPPORTED_BROWSER_CHANNELS:
            raise ValueError(
                f"Unsupported browser_channel '{browser_channel}'. "
                f"Choose one of: {', '.join(sorted(SUPPORTED_BROWSER_CHANNELS))}"
            )

        return cls(
            platform=platform,
            keyword=keyword,
            brand_filter=brand_filter,
            city_pincode=city_pincode,
            headless=bool(values.get("headless", True)),
            scroll_depth=int(values.get("scroll_depth", 3)),
            wait_ms=int(values.get("wait_ms", 2000)),
            output_dir=Path(values.get("output_dir", "./screenshots")),
            save_screen=bool(values.get("save_screen", False)),
            save_full_page=bool(values.get("save_full_page", False)),
            allow_position_fallback=bool(values.get("allow_position_fallback", False)),
            require_ad_tag=bool(values.get("require_ad_tag", True)),
            match_type=match_type,
            first_placement_only=first_placement_only,
            user_data_dir=user_data_dir,
            browser_channel=browser_channel,
            login_wait_ms=login_wait_ms,
            login_phone=login_phone,
        )


def normalize_platform(value: str) -> str:
    value = value.lower().strip().replace("-", "_")
    aliases = {
        "swiggy": "swiggy_instamart",
        "instamart": "swiggy_instamart",
        "swiggyinstamart": "swiggy_instamart",
    }
    return aliases.get(value, value)


def slugify(value: str, fallback: str = "all") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return cleaned or fallback


def load_jobs_from_config(path: Path, defaults: dict[str, Any] | None = None) -> list[ScraperJob]:
    data = _load_config_data(path)
    raw_jobs = data.get("jobs") if isinstance(data, dict) else data
    if not isinstance(raw_jobs, list):
        raise ValueError("Config must contain a list or a top-level 'jobs' list")
    return [ScraperJob.from_mapping(item, defaults) for item in raw_jobs]


def _load_config_data(path: Path) -> Any:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        return json.loads(text)
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML is required for YAML config files. Install dependencies from requirements.txt.") from exc
        return yaml.safe_load(text)
    raise ValueError("Config must be .yaml, .yml, or .json")
