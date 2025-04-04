
# Dubizzle Crawler (All Emirates)

This Python crawler scrapes used car listings from all emirates on Dubizzle and pushes them to a Supabase database.

## 🧰 Tech Stack

- Python 3.11
- Playwright (headless browser automation)
- Supabase (PostgreSQL backend)
- Render.com (deployment + cron job scheduling)

---

## ✅ Render Deployment Instructions

### 🔧 1. Build Command

Make sure your **Worker Service** has the following build command set in Render:

```bash
pip install -r requirements.txt && .venv/bin/python -m playwright install
```

This ensures that:
- Your dependencies are installed
- The **Chromium browser** is properly downloaded inside the virtual environment

### 🚀 2. Start Command

Your start command for the worker or cron job should be:

```bash
python3 dubizzle_crawler_all_emirates.py
```

### 📅 3. Cron Job (Optional)

To schedule regular scraping:
- Create a separate **Cron Job service** on Render
- Point it to the same repo
- Use the same **start command** above

---

## 💾 Supabase Table Structure

You should have a table called `listings` with the following columns:

| Column        | Type    |
|---------------|---------|
| id            | UUID (auto-generated) |
| listing_id    | Text    |
| title         | Text    |
| current_price | Integer |
| url           | Text    |
| last_seen     | Timestamp |
| price_history | JSONB   |

---

## 🧪 Local Development

To run this crawler locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python dubizzle_crawler_all_emirates.py
```

Happy crawling! 🕵️‍♂️🚗
