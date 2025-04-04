
import asyncio
import time
from datetime import datetime
from playwright.async_api import async_playwright
import requests
import json

# Configuration
SUPABASE_URL = "https://xkwvubeppqmzhurelcrp.supabase.co/rest/v1/listings"
SUPABASE_API_KEY = "YOUR_SUPABASE_API_KEY"  # Replace with your real key
HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}
LOCATIONS = ["dubai", "sharjah", "ajman", "abu-dhabi", "al-ain", "ras-al-khaimah", "fujairah", "umm-al-quwain"]

async def scrape_dubizzle():
    async with async_playwright() as p:
        # No need for executable_path — let Playwright handle it
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for location in LOCATIONS:
            page_number = 1
            while True:
                url = f"https://{location}.dubizzle.com/motors/used-cars/?page={page_number}"
                print(f"🌍 Navigating to page {page_number}: {url}")
                await page.goto(url, timeout=60000)

                await page.wait_for_timeout(1500)

                listings = await page.query_selector_all("[data-testid='listing-card']")
                print(f"✅ Found {len(listings)} listings on page {page_number}")

                if not listings:
                    break

                for listing in listings:
                    href = await listing.get_attribute("href")
                    title = await listing.inner_text("h2[data-testid='subheading-text']")
                    price_text = await listing.inner_text("div[data-testid='listing-price']")
                    price = int("".join(filter(str.isdigit, price_text)))
                    full_url = f"https://{location}.dubizzle.com{href}"
                    listing_id = href.split("/")[-2] if href else "unknown"

                    payload = {
                        "listing_id": listing_id,
                        "title": title,
                        "current_price": price,
                        "url": full_url,
                        "last_seen": datetime.now().isoformat(),
                        "price_history": json.dumps([{
                            "price": price,
                            "timestamp": datetime.now().isoformat()
                        }])
                    }

                    response = requests.post(SUPABASE_URL, headers=HEADERS, data=json.dumps(payload))
                    print(f"📤 Sent listing to Supabase | Status: {response.status_code}")

                page_number += 1
                time.sleep(1.5)

        await browser.close()
        print("🏁 Finished scraping all available pages.")

if __name__ == "__main__":
    asyncio.run(scrape_dubizzle())
