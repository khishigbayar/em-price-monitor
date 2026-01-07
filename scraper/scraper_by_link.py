import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
from dotenv import load_dotenv

load_dotenv()
from datetime import date
import psycopg2

URLS = [
    "https://em.hdc.gov.mn/productMap/2344",
    "https://em.hdc.gov.mn/productMap/2017",
    "https://em.hdc.gov.mn/productMap/1155",
    "https://em.hdc.gov.mn/productMap/113",
]

HEADERS = {"User-Agent": "Mozilla/5.0"}

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

def parse_page(url):
    res = requests.get(url, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(res.text, "html.parser")

    rows = []
    cards = soup.select(".pharmacy-card")

    for card in cards:
        name = card.select_one(".pharmacy-name span")
        address = card.select_one(".address")
        phone = card.select_one(".phone")

        price_raw = card.get("data-price") or ""
        price = int(re.sub(r"[^\d]", "", price_raw)) if price_raw else None

        rows.append({
            "product_url": url,
            "pharmacy": name.text.strip() if name else None,
            "address": address.text.strip() if address else None,
            "phone": phone.text.strip() if phone else None,
            "price": price,
            "scraped_date": date.today(),
        })

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
        print(f"Processing: {url}")
        rows = parse_page(url)
        print(f"  Found {len(rows)} pharmacies")
        all_rows.extend(rows)

    save_to_db(all_rows)
    print("Saved to PostgreSQL ✅")

    # Excel (optional)
    df = pd.DataFrame(all_rows)
    df.to_excel("pharmacy_today.xlsx", index=False)

if __name__ == "__main__":
    main()
