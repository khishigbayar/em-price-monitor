import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
from dotenv import load_dotenv
from datetime import date
import psycopg2

load_dotenv()

URLS = [
    "https://em.hdc.gov.mn/productMap/2344",
    "https://em.hdc.gov.mn/productMap/2017",
    "https://em.hdc.gov.mn/productMap/1155",
    "https://em.hdc.gov.mn/productMap/113",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EM-Price-Bot/1.0)"
}

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

def parse_page(url):
    print(f"🔍 Fetching {url}")
    res = requests.get(url, headers=HEADERS, timeout=30)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")
    cards = soup.select(".pharmacy-card")

    rows = []

    for card in cards:
        name_el = card.select_one(".pharmacy-name span")
        address_el = card.select_one(".address")
        phone_el = card.select_one(".phone")

        price_raw = card.get("data-price")
        if not price_raw:
            continue

        price = int(re.sub(r"[^\d]", "", price_raw))

        rows.append({
            "product_url": url,
            "pharmacy": name_el.text.strip() if name_el else None,
            "address": address_el.text.strip() if address_el else None,
            "phone": phone_el.text.strip() if phone_el else None,
            "price": price,
            "scraped_date": date.today(),
        })

    print(f"  ✅ Found {len(rows)} pharmacies")
    return rows

def save_to_db(rows):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    for r in rows:
        cur.execute("""
            INSERT INTO price_history
            (product_url, pharmacy, address, phone, price, scraped_date)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            r["product_url"],
            r["pharmacy"],
            r["address"],
            r["phone"],
            r["price"],
            r["scraped_date"],
        ))

    conn.commit()
    cur.close()
    conn.close()

def main():
    all_rows = []

    for url in URLS:
        try:
            rows = parse_page(url)
            all_rows.extend(rows)
        except Exception as e:
            print(f"❌ Error on {url}: {e}")

    if not all_rows:
        print("⚠️ No data scraped")
        return

    save_to_db(all_rows)
    print("🗄 Saved to PostgreSQL ✅")

    df = pd.DataFrame(all_rows)
    df.to_excel("pharmacy_today.xlsx", index=False)
    print("📄 Excel saved")

if __name__ == "__main__":
    main()
