from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import psycopg2
from psycopg2.extras import RealDictCursor

import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# ============================
# PRODUCT MAP
# ============================
PRODUCT_MAP = {
    "https://em.hdc.gov.mn/productMap/113": "Аминовит",
    "https://em.hdc.gov.mn/productMap/1155": "Урокер",
    "https://em.hdc.gov.mn/productMap/2017": "Панпирин Кю",
    "https://em.hdc.gov.mn/productMap/2344": "Альбуман",
}

# ======================
# ENV
# ======================
load_dotenv()

# ======================
# APP
# ======================
app = FastAPI(
    title="Эмийн үнийн мониторинг API",
    description="Эмийн сангийн үнэ, жагсаалт",
    version="1.0.0"
)

# ======================
# CORS
# ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# PATHS
# ======================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")

app.mount("/static", StaticFiles(directory=DASHBOARD_DIR), name="static")

# ======================
# DATABASE
# ======================
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

def fetch_all(sql, params=None):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(sql, params or [])
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# ======================
# DASHBOARD
# ======================
@app.get("/")
def serve_dashboard():
    return FileResponse(os.path.join(DASHBOARD_DIR, "index.html"))

# ======================
# API ENDPOINTS
# ======================

@app.get("/products")
def get_products():
    return [
        {"product_url": k, "product_name": v}
        for k, v in PRODUCT_MAP.items()
    ]

@app.get("/pharmacies")
def get_pharmacies(product_url: str = Query(...)):
    return fetch_all("""
        SELECT
            pharmacy,
            price,
            address,
            phone
        FROM price_history
        WHERE product_url = %s
        ORDER BY price ASC
    """, [product_url])

# ======================
# EXCEL EXPORT
# ======================
from datetime import datetime

@app.get("/export/excel")
def export_excel(
    product_url: str,
    start_date: str,
    end_date: str
):
    rows = fetch_all("""
        SELECT
            scraped_date,
            last_date,
            pharmacy,
            price,
            address,
            phone
        FROM price_history
        WHERE product_url = %s
          AND scraped_date BETWEEN %s AND %s
        ORDER BY scraped_date, price
    """, [product_url, start_date, end_date])

    if not rows:
        return {"error": "Мэдээлэл олдсонгүй"}

    df = pd.DataFrame(rows)

    # Эмийн нэр
    df.insert(0, "Эмийн нэр", PRODUCT_MAP.get(product_url, product_url))

    # Монгол багана
    df.rename(columns={
        "scraped_date": "Татсан огноо",
        "last_date": "Сүүлд борлуулсан огноо",
        "pharmacy": "Эмийн сан",
        "price": "Үнэ (₮)",
        "address": "Хаяг",
        "phone": "Утас"
    }, inplace=True)

    filename = f"em_price_{datetime.now().strftime('%Y%m%d')}.xlsx"
    filepath = f"/tmp/{filename}"

    df.to_excel(filepath, index=False)

    return FileResponse(
    path=filepath,
    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    filename=filename,
    headers={
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
)
