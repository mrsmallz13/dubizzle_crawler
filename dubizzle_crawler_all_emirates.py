
import asyncio
import time
from playwright.async_api import async_playwright
import requests
from datetime import datetime

SUPABASE_URL = "https://xkwvubeppqmzhurelcrp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

MAX_PAGES = 500
PAGE_DELAY_SECONDS = 1.5
EMIRATES = ["dubai", "abudhabi", "sharjah", "ajman", "rak", "fujairah", "uaq", "alain"]

def save_to_supabase(listing):
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/listings",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        },
        json=listing
    )
    print(f"📤 [{listing['emirate']}] Sent listing {listing['listing_id']} to Supabase | Status: {response.status_code}")

async def scrape_dubizzle():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for emirate in EMIRATES:
            print(f"🌍 Starting listings for {emirate.upper()}")
            for page_num in range(1, MAX_PAGES + 1):
                url = f"https://{emirate}.dubizzle.com/motors/used-cars/?page={page_num}"
                print(f"🌐 {emirate.upper()} Page {page_num}: {url}")
                try:
                    await page.goto(url, timeout=60000)
                    await page.wait_for_selector("a[data-testid^='listing-']", timeout=20000)
                except Exception:
                    print(f"⚠️ No listings found or timeout on {emirate} page {page_num}.")
                    break

                listings = await page.query_selector_all("a[data-testid^='listing-']")
                if not listings:
                    print(f"🚫 No listings found on {emirate} page {page_num}.")
                    break

                print(f"✅ {len(listings)} listings found on {emirate} page {page_num}")

                for card in listings:
                    try:
                        url_path = await card.get_attribute("href")
                        url_full = f"https://{emirate}.dubizzle.com" + url_path

                        title_el = await card.query_selector("[data-testid='subheading-text']")
                        price_el = await card.query_selector("[data-testid='listing-price']")

                        title = await title_el.inner_text() if title_el else "Unknown"
                        price = await price_el.inner_text() if price_el else "Unknown"
                        listing_id = url_full.split("/")[-2]
                        now = datetime.utcnow().isoformat()

                        listing = {
                            "listing_id": listing_id,
                            "title": title,
                            "current_price": price,
                            "url": url_full,
                            "last_seen": now,
                            "emirate": emirate,
                            "price_history": [{"price": price, "date": now}]
                        }

                        save_to_supabase(listing)
                    except Exception as e:
                        print(f"⚠️ Error on {emirate} listing: {e}")

                print(f"⏳ Waiting {PAGE_DELAY_SECONDS} seconds...")
                time.sleep(PAGE_DELAY_SECONDS)

        await browser.close()
        print("🏁 All emirate listings scraped.")

if __name__ == "__main__":
    asyncio.run(scrape_dubizzle())
