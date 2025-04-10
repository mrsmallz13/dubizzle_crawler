import asyncio
import json
import re
from datetime import datetime

from playwright.async_api import async_playwright
from supabase import create_client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def scrape_dubizzle():
    base_url = "https://uae.dubizzle.com/motors/used-cars/"
    listing_selector = 'a[data-testid^="listing-"]'  # Updated selector

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        page_num = 1
        listings_seen = set()

        while True:
            url = f"{base_url}?page={page_num}"
            print(f"🌍 Navigating to page {page_num}: {url}")
            await page.goto(url)
            await page.wait_for_timeout(2000)

            listings = await page.query_selector_all(listing_selector)

            if not listings:
                print("🏁 Finished scraping all available pages.")
                break

            print(f"✅ Found {len(listings)} listings on page {page_num}")

            for listing in listings:
                href = await listing.get_attribute("href")
                if not href:
                    continue

                full_url = f"https://uae.dubizzle.com{href}"
                listing_id_match = re.search(r'/([^/]+)/?$', href)
                listing_id = listing_id_match.group(1) if listing_id_match else href

                if listing_id in listings_seen:
                    continue
                listings_seen.add(listing_id)

                title_el = await listing.query_selector('[data-testid="subheading-text"]')
                price_el = await listing.query_selector('[data-testid="listing-price"]')

                title = await title_el.inner_text() if title_el else "N/A"
                price_text = await price_el.inner_text() if price_el else "0"
                price = int(re.sub(r"[^\d]", "", price_text))

                now = datetime.utcnow().isoformat()
                data = {
                    "listing_id": listing_id,
                    "title": title,
                    "current_price": price,
                    "url": full_url,
                    "last_seen": now,
                    "price_history": json.dumps([{"price": price, "timestamp": now}]),
                }

                # Upsert listing to Supabase
                supabase.table("listings").upsert(data, on_conflict="listing_id").execute()

            page_num += 1

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_dubizzle())
