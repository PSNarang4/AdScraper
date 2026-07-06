from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RunLog:
    run_timestamp: str
    platform: str
    keyword: str
    brand_filter: str
    city_pincode: str
    match_type: str = "broad"
    total_sponsored_cards_found: int = 0
    screenshots_saved: list[str] = field(default_factory=list)
    screen_screenshots_saved: list[str] = field(default_factory=list)
    ad_placements: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    device: dict[str, Any] = field(default_factory=dict)

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")


def write_batch_log(output_dir: Path, logs: list[RunLog]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "jobs": [asdict(log) for log in logs],
        "total_jobs": len(logs),
        "total_screenshots_saved": sum(len(log.screenshots_saved) for log in logs),
        "total_screen_screenshots_saved": sum(len(log.screen_screenshots_saved) for log in logs),
        "total_errors": sum(len(log.errors) for log in logs),
    }
    (output_dir / "run_log.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "ad_slot_report.txt").write_text(build_slot_report(logs), encoding="utf-8")
    
    summary_content = build_summary_report(logs)
    (output_dir / "summary.txt").write_text(summary_content, encoding="utf-8")
    try:
        (output_dir.parent.parent / "summary.txt").write_text(summary_content, encoding="utf-8")
    except Exception:
        pass


def build_summary_report(logs: list[RunLog]) -> str:
    keyword_slots = {}
    for log in logs:
        keyword_title = log.keyword.strip().title()
        if not keyword_title:
            continue
        if keyword_title not in keyword_slots:
            keyword_slots[keyword_title] = []
        for placement in log.ad_placements:
            ad_slot = placement.get("ad_slot")
            if ad_slot is not None:
                keyword_slots[keyword_title].append(int(ad_slot))
                
    lines = []
    for keyword, slots in keyword_slots.items():
        if slots:
            unique_slots = sorted(list(set(slots)))
            slot_strings = [ordinal(s) for s in unique_slots]
            if len(slot_strings) == 1:
                lines.append(f"{keyword} - {slot_strings[0]} ad slot")
            else:
                slots_str = ", ".join(slot_strings[:-1]) + f" and {slot_strings[-1]}"
                lines.append(f"{keyword} - {slots_str} ad slots")
    return "\n".join(lines) + "\n" if lines else ""


def ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"


def build_slot_report(logs: list[RunLog]) -> str:
    lines = ["keyword\tbrand\tstatus\tresult_slot\tad_slot\tscreenshot"]
    for log in logs:
        if not log.ad_placements:
            status = "no matching tagged ad captured"
            if log.errors:
                status = f"error: {'; '.join(log.errors)}"
            elif log.warnings:
                status = "; ".join(log.warnings)
            lines.append(f"{log.keyword}\t{log.brand_filter or 'all'}\t{status}\t\t\t")
            continue

        for placement in log.ad_placements:
            result_slot = placement.get("result_slot") or ""
            ad_slot = placement.get("ad_slot") or ""
            screenshot = placement.get("screenshot_path") or ""
            lines.append(
                f"{log.keyword}\t{log.brand_filter or 'all'}\tcaptured\t{result_slot}\t{ad_slot}\t{screenshot}"
            )
    return "\n".join(lines) + "\n"

