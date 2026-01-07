from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import json

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service("/usr/bin/chromedriver"),
    options=options
)

url = "https://em.hdc.gov.mn/productMap/2344"
driver.get(url)

time.sleep(6)  # Angular бүрэн load болтол

# 1️⃣ window keys dump
keys = driver.execute_script("return Object.keys(window);")
print("\n=== WINDOW KEYS (filtered) ===")
for k in keys:
    if "location" in k.lower() or "pharm" in k.lower() or "map" in k.lower():
        print(k)

# 2️⃣ Angular debug context (байвал)
ng = driver.execute_script("return window.__ngContext__ || null;")
print("\n=== NG CONTEXT EXISTS? ===", bool(ng))

# 3️⃣ Page source дотор pharmacy / hs_ хайх
source = driver.page_source
hits = []
for kw in ["hs_", "pharmacy", "formatted_price", "last"]:
    if kw in source:
        hits.append(kw)

print("\n=== PAGE SOURCE KEYWORDS FOUND ===", hits)

driver.quit()
