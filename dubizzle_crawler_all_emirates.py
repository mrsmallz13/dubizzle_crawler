import asyncio
from playwright.async_api import async_playwright
import requests
import time
from datetime import datetime

SUPABASE_URL = "https://xkwvubeppqmzhurelcrp.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhrd3Z1YmVwcHFtemh1cmVsY3JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MzY2OTczNiwiZXhwIjoyMDU5MjQ1NzM2fQ.uiQ48x9hlyVuc9kMdA5ohKOviySZ4obFoojjv8PaAPk"

HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhrd3Z1YmVwcHFtemh1cmVsY3JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MzY2OTczNiwiZXhwIjoyMDU5MjQ1NzM2fQ.uiQ48x9hlyVuc9kMdA5ohKOviySZ4obFoojjv8PaAPk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhrd3Z1YmVwcHFtemh1cmVsY3JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MzY2OTczNiwiZXhwIjoyMDU5MjQ1NzM2fQ.uiQ48x9hlyVuc9kMdA5ohKOviySZ4obFoojjv8PaAPk",
    "Content-Type": "application/json"
}

async def scrape_dubizzle():
    base_url = "https://uae.dubizzle.com/motors/used-cars/?page={}"
    page_num = 1
    listings_found = True

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        while listings_found:
            url = base_url.format(page_num)
            print(f"🌍 Navigating to page {page_num}: {url}")
            try:
                await page.goto(url, timeout=60000)
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"⚠️ Failed to load page {page_num}: {e}")
                break

            listings = await page.query_selector_all('a[data-testid^="listing-"][href*="/motors/used-cars/"]')
            print(f"✅ Found {len(listings)} listings on page {page_num}")

            if not listings:
                listings_found = False
                break

            for listing in listings:
                try:
                    url_element = await listing.get_attribute("href")
                    title_element = await listing.query_selector('[data-testid="subheading-text"]')
                    title = await title_element.inner_text() if title_element else "N/A"
                    price_element = await listing.query_selector('[data-testid="listing-price"]')
                    price_text = await price_element.inner_text() if price_element else "0"
                    price = int(price_text.replace(",", "").replace("AED", "").strip())

                    listing_data = {
                        "listing_id": url_element.split("/")[-2] if url_element else "unknown",
                        "title": title,
                        "current_price": price,
                        "url": f"https://uae.dubizzle.com{url_element}",
                        "last_seen": datetime.utcnow().isoformat(),
                        "price_history": [{"price": price, "timestamp": datetime.utcnow().isoformat()}]
                    }

                    response = requests.post(f"{SUPABASE_URL}/rest/v1/listings", headers=HEADERS, json=listing_data)
                    print(f"📤 Sent listing to Supabase | Status: {response.status_code}")

                except Exception as inner_e:
                    print(f"❌ Error processing listing: {inner_e}")

            page_num += 1
            await page.wait_for_timeout(1500)

        await browser.close()
        print("🏁 Finished scraping all available pages.")

if __name__ == "__main__":
    asyncio.run(scrape_dubizzle())
