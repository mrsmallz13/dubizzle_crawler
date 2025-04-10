import asyncio
from datetime import datetime
import re
import os
import json
import requests
from playwright.async_api import async_playwright

SUPABASE_URL = "https://xkwvubeppqmzhurelcrp.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhrd3Z1YmVwcHFtemh1cmVsY3JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MzY2OTczNiwiZXhwIjoyMDU5MjQ1NzM2fQ.uiQ48x9hlyVuc9kMdA5ohKOviySZ4obFoojjv8PaAPk"

async def scrape_dubizzle():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        base_url = "https://uae.dubizzle.com/motors/used-cars/"
        page_number = 1
        listings_found = True

        while listings_found:
            print(f"🌍 Navigating to page {page_number}: {base_url}?page={page_number}")
            await page.goto(f"{base_url}?page={page_number}", timeout=60000)
            await page.wait_for_timeout(5000)

            anchors = await page.query_selector_all('a[data-testid="listing-1"]')
            listings_found = len(anchors) > 0
            print(f"✅ Found {len(anchors)} listings on page {page_number}")

            for anchor in anchors:
                try:
                    href = await anchor.get_attribute("href")
                    url = f"https://uae.dubizzle.com{href}"

                    title_elem = await anchor.query_selector('h2[data-testid="subheading-text"]')
                    title = await title_elem.inner_text() if title_elem else "No title"

                    price_elem = await anchor.query_selector('div[data-testid="listing-price"]')
                    price_raw = await price_elem.inner_text() if price_elem else "0"
                    current_price = int(re.sub(r"[^\d]", "", price_raw))

                    location_elem = await anchor.query_selector('h4[class*="MuiTypography"]')
                    location = await location_elem.inner_text() if location_elem else "Unknown"

                    emirate = location.split(",")[1].strip() if "," in location else location.strip()
                    listing_id = href.strip("/").split("-")[-1]

                    last_seen = datetime.utcnow().isoformat()

                    listing_data = {
                        "listing_id": listing_id,
                        "title": title,
                        "url": url,
                        "current_price": current_price,
                        "last_seen": last_seen,
                        "emirate": emirate,
                        "price_history": [{"price": current_price, "timestamp": last_seen}]
                    }

                    await upload_to_supabase(listing_data)

                except Exception as e:
                    print(f"❌ Error parsing a listing: {e}")

            page_number += 1

        await browser.close()
        print("🏁 Finished scraping all available pages.")

async def upload_to_supabase(listing):
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/listings",
        headers=headers,
        data=json.dumps(listing)
    )

    if response.status_code in [200, 201]:
        print(f"✅ Uploaded {listing['listing_id']}")
    else:
        print(f"❌ Failed to upload {listing['listing_id']}: {response.text}")

if __name__ == "__main__":
    asyncio.run(scrape_dubizzle())
