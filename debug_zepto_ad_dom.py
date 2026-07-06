import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="msedge",
            headless=True,
        )
        context = await browser.new_context(
            viewport={"width": 412, "height": 915},
            is_mobile=True,
            has_touch=True,
            user_agent="Mozilla/5.0 (Linux; Android 10; SM-G988B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112 Mobile Safari/537.36"
        )
        page = await context.new_page()
        
        print("Navigating to Zepto...")
        await page.goto("https://www.zeptonow.com", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # Click search trigger on home page
        print("Clicking search trigger...")
        search_trig = page.locator("a[aria-label*='search' i]").first
        if await search_trig.count() > 0:
            await search_trig.click()
            await page.wait_for_timeout(2000)
            
            # Now find search input
            search_input = page.locator("input[placeholder*='search' i]").first
            if await search_input.count() > 0:
                print("Filling search input...")
                await search_input.click()
                await search_input.fill("Shampoo")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(5000)
                
                print("Inspecting DOM of cards on search results page...")
                res = await page.evaluate("""
                    () => {
                        // Find all elements that look like product cards
                        // We look for elements containing the product titles or structured similarly
                        const cardNodes = Array.from(document.querySelectorAll('a[href*="/p/"]'));
                        
                        const details = [];
                        cardNodes.forEach((node, index) => {
                            // Find all child elements of this card
                            const children = Array.from(node.querySelectorAll('*'));
                            const elements = children.map(el => {
                                const text = (el.innerText || el.textContent || "").trim();
                                const tag = el.tagName;
                                const className = el.className || "";
                                const attrs = {};
                                for (const attr of el.attributes) {
                                    attrs[attr.name] = attr.value;
                                }
                                return { tag, className, text, attrs };
                            }).filter(el => el.text.length > 0 && el.text.length < 200);
                            
                            details.push({
                                index,
                                outerHTML: node.outerHTML.slice(0, 300),
                                elements
                            });
                        });
                        return details;
                    }
                """)
                
                print(f"Found {len(res)} cards.")
                for card in res[:10]: # Print first 10 cards
                    print(f"\n--- CARD {card['index']} ---")
                    print("Outer HTML:", card['outerHTML'][:150])
                    for el in card['elements']:
                        text_safe = el['text'].encode('ascii', errors='ignore').decode('ascii').strip()
                        # Highlight if it has "ad" or is very short (could be the Ad badge)
                        if len(text_safe) <= 10 or 'ad' in text_safe.lower() or 'ad' in el['className'].lower():
                            print(f"  {el['tag']} | class='{el['className']}' | text='{text_safe}' | attrs={el['attrs']}")
            else:
                print("Search input NOT found on search page!")
        else:
            print("Search trigger NOT found on home page!")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
