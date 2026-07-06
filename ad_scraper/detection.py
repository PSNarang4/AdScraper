from __future__ import annotations

from typing import Any


DETECTION_SCRIPT = """
({ allowPositionFallback, platform, requireVisibleAdTag }) => {
  const labels = ["ad", "sponsored", "promoted"];
  const keywordRegex = /(^|\\b)(ad|sponsored|promoted)(\\b|$)/i;
  const classRegex = /(^|[\\s_-])(ad|advertisement|sponsor|sponsored|promoted|paid)([\\s_-]|$)/i;
  const platformKey = platform || "";
  const viewportHeight = window.innerHeight || 915;
  const viewportWidth = window.innerWidth || 412;
  const seen = new Set();
  const results = [];

  function isVisible(el) {
    if (!el || !(el instanceof Element)) return false;
    const style = window.getComputedStyle(el);
    if (style.visibility === "hidden" || style.display === "none" || Number(style.opacity) === 0) return false;
    const rect = el.getBoundingClientRect();
    return rect.width >= 1 && rect.height >= 1 && rect.bottom > 0 && rect.right > 0 &&
      rect.top < viewportHeight && rect.left < viewportWidth;
  }

  function cleanText(el) {
    return (el.innerText || el.textContent || "").replace(/\\s+/g, " ").trim();
  }

  function attrsFor(el) {
    return `${el.className || ""} ${el.id || ""} ${el.getAttribute("data-testid") || ""}`;
  }

  function labelMatches(el) {
    const text = cleanText(el).toLowerCase();
    if (text && text.length <= 40) {
      if (labels.includes(text) || keywordRegex.test(text)) return true;
    }

    const alt = (el.getAttribute("alt") || "").toLowerCase().trim();
    if (alt && alt.length <= 40) {
      if (labels.includes(alt) || keywordRegex.test(alt)) return true;
    }

    const aria = (el.getAttribute("aria-label") || "").toLowerCase().trim();
    if (aria && aria.length <= 40) {
      if (labels.includes(aria) || keywordRegex.test(aria)) return true;
    }

    if (el.getAttribute("data-slot-id") === "SponsorTag") return true;

    return false;
  }

  function productCardScore(el) {
    if (!isVisible(el)) return -1;
    const rect = el.getBoundingClientRect();
    const text = cleanText(el);
    if (rect.width < 90 || rect.height < 90) return -1;
    if ((platformKey === "blinkit" || platformKey === "zepto") && rect.width > viewportWidth * 0.75) return -1;
    if (rect.width > viewportWidth * 1.05 || rect.height > viewportHeight * 0.8) return -1;
    if (text.length < 3 || text.length > 900) return -1;
    if (platformKey === "blinkit" && !/(add|rs\\.?|\\u20b9)/i.test(text)) return -1;
    let score = 0;
    const attrs = attrsFor(el);
    if (el.getAttribute("data-id")) score += 6;
    if (/(card|product|tile|item|grid|sku|s-result-item|s-search-result|_1AtVbE)/i.test(attrs)) score += 4;
    if (el.querySelector("img, picture, svg")) score += 3;
    if (/add|price|rs\\.?|\\u20b9|off|g|kg|ml|pack/i.test(text)) score += 2;
    if (keywordRegex.test(text)) score += 2;
    score += Math.max(0, 5 - Math.floor(text.length / 180));
    return score;
  }

  function closestCard(labelEl) {
    let current = labelEl;
    for (let depth = 0; current && depth < 16; depth += 1, current = current.parentElement) {
      if (current === document.body || current === document.documentElement) break;
      const score = productCardScore(current);
      if (score >= 4) {
        return current;
      }
    }
    return null;
  }

  function sortedVisibleProductCards() {
    const candidates = Array.from(document.querySelectorAll("article, li, [role='listitem'], [data-testid], div"))
      .filter((el) => productCardScore(el) >= 4)
      .sort((a, b) => {
        const ar = a.getBoundingClientRect();
        const br = b.getBoundingClientRect();
        const aArea = ar.width * ar.height;
        const bArea = br.width * br.height;
        return bArea - aArea;
      });

    const deduped = [];
    candidates.forEach((el) => {
      if (deduped.some((existing) => existing.contains(el) || el.contains(existing))) return;
      deduped.push(el);
    });

    return deduped.sort((a, b) => {
      const ar = a.getBoundingClientRect();
      const br = b.getBoundingClientRect();
      return ar.top - br.top || ar.left - br.left;
    });
  }

  function visibleResultSlotFor(cardEl) {
    const cards = sortedVisibleProductCards();
    const index = cards.findIndex((el) => el === cardEl || el.contains(cardEl) || cardEl.contains(el));
    return index >= 0 ? index + 1 : null;
  }

  function hasBlinkitAdBadge(cardEl) {
    const cardRect = cardEl.getBoundingClientRect();
    return Array.from(cardEl.querySelectorAll("*")).some((el) => {
      if (!isVisible(el)) return false;
      const rect = el.getBoundingClientRect();
      const inBadgeZone = rect.left >= cardRect.right - 70 &&
        rect.right <= cardRect.right + 4 &&
        rect.top >= cardRect.top &&
        rect.top <= cardRect.top + 48 &&
        rect.width <= 54 &&
        rect.height <= 28;
      if (!inBadgeZone) return false;

      const text = cleanText(el).toLowerCase();
      const ariaText = [
        el.getAttribute("aria-label") || "",
        el.getAttribute("title") || "",
        el.getAttribute("alt") || ""
      ].join(" ").toLowerCase();
      if (text === "ad" || /(^|\\b)(ad|sponsored|promoted)(\\b|$)/i.test(ariaText)) return true;

      const attrs = attrsFor(el).toLowerCase();
      const imageSource = (el.getAttribute("src") || "").toLowerCase();
      if (/ad_without_bg|\\/assets\\/ui\\/ad/i.test(imageSource)) return true;

      const style = window.getComputedStyle(el);
      const isSmallGreyText = rect.width >= 8 &&
        rect.height >= 6 &&
        /tw-text-grey|text-grey|grey|gray/.test(attrs) &&
        /rgb\\((1[4-9][0-9]|2[0-2][0-9]),\\s*(1[4-9][0-9]|2[0-2][0-9]),\\s*(1[4-9][0-9]|2[0-2][0-9])\\)/.test(style.color);
      return isSmallGreyText && !el.querySelector("img, picture, svg");
    });
  }

  function isBlinkitSponsoredCard(el) {
    if (platformKey !== "blinkit") return false;
    if (!isVisible(el)) return false;
    const rect = el.getBoundingClientRect();
    if (rect.width < 120 || rect.height < 160) return false;
    if (rect.width > viewportWidth * 0.75 || rect.height > viewportHeight * 0.7) return false;
    const text = cleanText(el);
    if (!/(add|mins?|off|rs\\.?|\\u20b9)/i.test(text)) return false;
    if (!hasBlinkitAdBadge(el)) return false;
    return productCardScore(el) >= 5;
  }

  function pushCard(el, reason) {
    if (!el || seen.has(el)) return;
    seen.add(el);
    const id = `adscraper-${results.length + 1}-${Date.now()}`;
    el.setAttribute("data-adscraper-capture-id", id);
    const rect = el.getBoundingClientRect();
    const hrefs = Array.from(el.querySelectorAll("a")).map(a => a.getAttribute("href") || "").join(" ");
    const imgs = Array.from(el.querySelectorAll("img")).map(img => img.getAttribute("src") || img.getAttribute("srcset") || "").join(" ");
    const enrichedText = cleanText(el) + " " + hrefs + " " + imgs;
    results.push({
      id,
      reason,
      resultSlot: visibleResultSlotFor(el),
      text: enrichedText.slice(0, 2000),
      rect: {
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        width: Math.round(rect.width),
        height: Math.round(rect.height)
      }
    });
  }

  Array.from(document.querySelectorAll("body *"))
    .filter((el) => isVisible(el) && labelMatches(el))
    .forEach((el) => pushCard(closestCard(el), "text"));

  if (platformKey === "blinkit") {
    Array.from(document.querySelectorAll("body *"))
      .filter(isBlinkitSponsoredCard)
      .slice(0, 12)
      .forEach((el) => pushCard(el, "blinkit_ad_badge"));
  }

  if (!requireVisibleAdTag && results.length === 0) {
    Array.from(document.querySelectorAll("body *"))
      .filter((el) => {
        const attrs = attrsFor(el);
        return isVisible(el) && classRegex.test(attrs) && productCardScore(el) >= 3;
      })
      .slice(0, 8)
      .forEach((el) => pushCard(el, "css"));
  }

  if (!requireVisibleAdTag && allowPositionFallback && results.length === 0) {
    const candidates = Array.from(document.querySelectorAll("article, li, [role='listitem'], [data-testid], div"))
      .filter((el) => {
        const rect = el.getBoundingClientRect();
        return isVisible(el) && rect.top >= 0 && rect.top <= Math.min(360, viewportHeight * 0.45) &&
          productCardScore(el) >= 4;
      })
      .sort((a, b) => {
        const ar = a.getBoundingClientRect();
        const br = b.getBoundingClientRect();
        return ar.top - br.top || ar.left - br.left;
      })
      .slice(0, 4);
    candidates.forEach((el) => pushCard(el, "position"));
  }

  results
    .sort((a, b) => a.rect.y - b.rect.y || a.rect.x - b.rect.x)
    .forEach((result, index) => {
      result.adSlot = index + 1;
    });

  return results;
}
"""


async def detect_ad_cards(
    page: Any,
    allow_position_fallback: bool = False,
    platform: str = "",
    require_visible_ad_tag: bool = True,
) -> list[dict[str, Any]]:
    return await page.evaluate(
        DETECTION_SCRIPT,
        {
            "allowPositionFallback": allow_position_fallback,
            "platform": platform,
            "requireVisibleAdTag": require_visible_ad_tag,
        },
    )
