from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import psycopg2
from psycopg2.extras import RealDictCursor

import os
from dotenv import load_dotenv

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

# dashboard доторх static файлууд (js, css)
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
    """
    http://SERVER:8000/
    """
    return FileResponse(os.path.join(DASHBOARD_DIR, "index.html"))

# ======================
# API ENDPOINTS
# ======================

# 🔹 БҮХ ЭМ (product_url list)
@app.get("/products")
def get_products():
    return fetch_all("""
        SELECT DISTINCT product_url
        FROM price_history
        ORDER BY product_url
    """)

# 🔹 СОНГОСОН ЭМИЙН БҮХ ЭМИЙН САН
@app.get("/pharmacies")
def get_pharmacies(
    product_url: str = Query(..., description="productMap URL")
):
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
# 🔹 ЭМИЙН ЖАГСААЛТ (нэр + url)
@app.get("/products")
def get_products():
    return [
        {
            "product_url": "https://em.hdc.gov.mn/productMap/113",
            "product_name": "Аминовит"
        },
        {
            "product_url": "https://em.hdc.gov.mn/productMap/1155",
            "product_name": "Урокер"
        },
        {
            "product_url": "https://em.hdc.gov.mn/productMap/2017",
            "product_name": "Панпирин Кю"
        },
        {
            "product_url": "https://em.hdc.gov.mn/productMap/2344",
            "product_name": "Альбуман"
        }
    ]

