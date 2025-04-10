import asyncio
import uuid
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import stealth
import requests
import json

SUPABASE_URL = "https://xkwvubeppqmzhurelcrp.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhrd3Z1YmVwcHFtemh1cmVsY3JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MzY2OTczNiwiZXhwIjoyMDU5MjQ1NzM2fQ.uiQ48x9hlyVuc9kMdA5ohKOviySZ4obFoojjv8PaAPk"
SUPABASE_TABLE = "listings"

async def scrape_dubizzle():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await stealth(page)

        page_num = 1
        listings_found = True

        while listings_found:
            url = f"https://uae.dubizzle.com/motors/used-cars/?page={page_num}"
            print(f"🌍 Navigating to page {page_num}: {url}")
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(5000)

            listings = await page.locator('a[data-testid="listing-1"]').all()
            if not listings:
                print("✅ Found 0 listings on page", page_num)
                break

            print(f"✅ Found {len(listings)} listings on page {page_num}")

            for listing in listings:
                href = await listing.get_attribute("href")
                if not href:
                    continue

                full_url = f"https://uae.dubizzle.com{href}"
                title_el = listing.locator('[data-testid="subheading-text"]')
                price_el = listing.locator('[data-testid="listing-price"]')
                title = await title_el.inner_text() if await title_el.count() > 0 else "N/A"
                price = await price_el.inner_text() if await price_el.count() > 0 else "N/A"
                listing_id = href.strip("/").split("-")[-1]

                payload = {
                    "id": str(uuid.uuid4()),
                    "listing_id": listing_id,
                    "title": title,
                    "current_price": price,
                    "url": full_url,
                    "last_seen": datetime.utcnow().isoformat(),
                    "price_history": json.dumps([{
                        "price": price,
                        "timestamp": datetime.utcnow().isoformat()
                    }])
                }

                headers = {
                    "apikey": SUPABASE_API_KEY,
                    "Authorization": f"Bearer {SUPABASE_API_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates"
                }

                res = requests.post(
                    f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}",
                    headers=headers,
                    data=json.dumps(payload)
                )

                if res.status_code not in (200, 201):
                    print(f"❌ Failed to insert {listing_id}: {res.status_code} - {res.text}")
                else:
                    print(f"✅ Inserted {listing_id} successfully")

            page_num += 1

        print("🏁 Finished scraping all available pages.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_dubizzle())
