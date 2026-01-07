from playwright.sync_api import sync_playwright
import psycopg2
import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()

URLS = [
    "https://em.hdc.gov.mn/productMap/2344",
    "https://em.hdc.gov.mn/productMap/2017",
    "https://em.hdc.gov.mn/productMap/1155",
    "https://em.hdc.gov.mn/productMap/113",
]

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

def save_to_db(rows):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    for r in rows:
        cur.execute("""
            INSERT INTO price_history
            (product_url, pharmacy, address, phone, price, last_date, scraped_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            r["product_url"],
            r["pharmacy"],
            r["address"],
            r["phone"],
            r["price"],
            r["last_date"],
            date.today(),
        ))
    conn.commit()
    cur.close()
    conn.close()

def scrape():
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for url in URLS:
            print("Processing:", url)
            page.goto(url, timeout=60000)

            # JS бүрэн ачааллыг хүлээнэ
            page.wait_for_timeout(3000)

            locations = page.evaluate("locations")

            for l in locations:
                rows.append({
                    "product_url": url,
                    "pharmacy": l.get("hs_name"),
                    "address": l.get("hs_address"),
                    "phone": l.get("hs_phone"),
                    "price": l.get("last_price"),
                    "last_date": l.get("last_date"),
                })

        browser.close()

    return rows

def main():
    rows = scrape()
    save_to_db(rows)
    print(f"Saved {len(rows)} rows ✅")

if __name__ == "__main__":
    main()
