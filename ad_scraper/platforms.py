from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformSpec:
    key: str
    base_url: str
    search_selectors: tuple[str, ...]
    location_triggers: tuple[str, ...]
    location_inputs: tuple[str, ...]
    search_triggers: tuple[str, ...] = ()
    login_triggers: tuple[str, ...] = ()
    login_inputs: tuple[str, ...] = ()


PLATFORMS: dict[str, PlatformSpec] = {
    "blinkit": PlatformSpec(
        key="blinkit",
        base_url="https://blinkit.com",
        location_triggers=(
            "text=/select location/i",
            "text=/change location/i",
            "text=/detect my location/i",
            "text=/enter pincode/i",
        ),
        location_inputs=(
            "input[placeholder*='pincode' i]",
            "input[placeholder*='location' i]",
            "input[placeholder*='address' i]",
            "input[type='search']",
            "input",
        ),
        search_selectors=(
            "input[placeholder*='search' i]",
            "input[type='search']",
            "[contenteditable='true']",
        ),
        search_triggers=(
            "text=/search/i",
            "a[href*='search']",
            "a[href*='/s/']",
        ),
        login_triggers=(
            "button:has-text('Login')",
            "text=/login/i",
            "text=/sign in/i",
            "[role='button']:has-text('Login')",
        ),
        login_inputs=(
            "input[type='tel']",
            "input[autocomplete='tel']",
            "input[inputmode='numeric']",
            "input[placeholder*='mobile' i]",
            "input[placeholder*='phone' i]",
            "input[placeholder*='number' i]",
            "input",
        ),
    ),
    "zepto": PlatformSpec(
        key="zepto",
        base_url="https://www.zeptonow.com",
        location_triggers=(
            "text=/select location/i",
            "text=/change location/i",
            "text=/enter location/i",
            "text=/deliver to/i",
        ),
        location_inputs=(
            "input[placeholder*='pincode' i]",
            "input[placeholder*='address' i]",
            "input[placeholder*='location' i]",
            "input[type='search']",
            "input",
        ),
        search_selectors=(
            "input[placeholder*='products' i]",
            "input[placeholder*='search for' i]",
            "input[placeholder*='search' i]:not([placeholder*='address' i]):not([placeholder*='location' i]):not([placeholder*='pincode' i])",
            "input[type='search']:not([placeholder*='address' i]):not([placeholder*='location' i]):not([placeholder*='pincode' i])",
            "[contenteditable='true']",
        ),
        search_triggers=(
            "a[aria-label*='search' i]",
            "[data-testid*='search' i]",
        ),
        login_triggers=(
            "button:has-text('Login')",
            "text=/login/i",
            "text=/sign in/i",
            "[role='button']:has-text('Login')",
        ),
        login_inputs=(
            "input[type='tel']",
            "input[autocomplete='tel']",
            "input[inputmode='numeric']",
            "input[placeholder*='mobile' i]",
            "input[placeholder*='phone' i]",
            "input[placeholder*='number' i]",
            "input",
        ),
    ),
    "swiggy_instamart": PlatformSpec(
        key="swiggy_instamart",
        base_url="https://www.swiggy.com/instamart",
        location_triggers=(
            "text=/search for an area or address/i",
            "text=/add your location/i",
            "text=/setup your precise location/i",
            "text=/enter your delivery location/i",
            "text=/change/i",
            "text=/location/i",
        ),
        location_inputs=(
            "input[placeholder*='area' i]",
            "input[placeholder*='street' i]",
            "input[placeholder*='location' i]",
            "input[placeholder*='address' i]",
            "input[type='search']",
            "input",
        ),
        search_selectors=(
            "input[placeholder*='search' i]",
            "input[placeholder*='Search for' i]",
            "input[type='search']",
            "[contenteditable='true']",
        ),
        search_triggers=(
            "button:has-text('Search for')",
            "a[href*='search']",
            "button[aria-label*='search' i]",
            "text=/search/i",
        ),
        login_triggers=(
            "button:has-text('Login')",
            "text=/login/i",
            "text=/sign in/i",
            "[role='button']:has-text('Login')",
        ),
        login_inputs=(
            "input[type='tel']",
            "input[autocomplete='tel']",
            "input[inputmode='numeric']",
            "input[placeholder*='mobile' i]",
            "input[placeholder*='phone' i]",
            "input[placeholder*='number' i]",
            "input",
        ),
    ),
    "flipkart": PlatformSpec(
        key="flipkart",
        base_url="https://www.flipkart.com",
        location_triggers=(),
        location_inputs=(),
        search_selectors=(
            "input[placeholder*='search' i]",
            "input[type='search']",
            "input[name='q']",
        ),
        search_triggers=(
            "text=/search/i",
            "a[href*='search']",
        ),
    ),
    "amazon": PlatformSpec(
        key="amazon",
        base_url="https://www.amazon.in",
        location_triggers=(
            "a#nav-global-location-slot",
            "text=/delivering to/i",
            "text=/select location/i",
        ),
        location_inputs=(
            "input#GLUXZipUpdateInput",
            "input[placeholder*='pincode' i]",
            "input[placeholder*='pin' i]",
            "input",
        ),
        search_selectors=(
            "input[placeholder*='search' i]",
            "input[type='search']",
            "input[name='field-keywords']",
        ),
        search_triggers=(
            "text=/search/i",
            "a[href*='search']",
        ),
    ),
}
