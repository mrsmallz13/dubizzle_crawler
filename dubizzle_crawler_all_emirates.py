
import asyncio
from playwright.async_api import async_playwright
import requests
import time

SUPABASE_URL = "https://xkwvubeppqmzhurelcrp.supabase.co"
SUPABASE_API_KEY = "YOUR_SUPABASE_API_KEY"

HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json"
}

cities = {
    "dubai": "dubai",
    "abu-dhabi": "abu-dhabi",
    "sharjah": "sharjah",
    "ajman": "ajman",
    "fujairah": "fujairah",
    "ras-al-khaimah": "ras-al-khaimah",
    "umm-al-quwain": "umm-al-quwain"
}

async def scrape_dubizzle():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for city_name, city_slug in cities.items():
            for page_num in range(1, 1001):
                url = f"https://www.dubizzle.com/motors/used-cars/?city={city_slug}&page={page_num}"
                print(f"🌍 Navigating to page {page_num}: {url}")
                try:
                    await page.goto(url, timeout=60000)
                except Exception as e:
                    print(f"Failed to load page {page_num} for {city_name}: {e}")
                    break

                listings = await page.query_selector_all('[data-testid^="listing-"]')
                print(f"✅ Found {len(listings)} listings on page {page_num}")
                if not listings:
                    break

                for listing in listings:
                    try:
                        anchor = await listing.query_selector("a")
                        href = await anchor.get_attribute("href")
                        title_elem = await listing.query_selector('[data-testid="heading-text-2"]')
                        title = await title_elem.inner_text() if title_elem else "No title"
                        price_elem = await listing.query_selector('[data-testid="listing-price"]')
                        price_text = await price_elem.inner_text() if price_elem else "0"
                        price = int("".join(filter(str.isdigit, price_text)))

                        full_url = f"https://www.dubizzle.com{href}"
                        payload = {
                            "listing_id": href,
                            "title": title,
                            "current_price": price,
                            "url": full_url,
                            "last_seen": time.strftime("%Y-%m-%dT%H:%M:%S"),
                            "price_history": [price]
                        }

                        response = requests.post(f"{SUPABASE_URL}/rest/v1/listings", headers=HEADERS, json=payload)
                        print(f"📤 Sent listing to Supabase | Status: {response.status_code}")
                    except Exception as e:
                        print(f"⚠️ Error processing listing: {e}")
                        continue

                print("⏳ Waiting 1.5 seconds before next page...")
                await asyncio.sleep(1.5)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_dubizzle())
