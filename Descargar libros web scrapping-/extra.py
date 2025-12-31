import os
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuración ---
excel_file = r"C:\Users\andres.guerra.d\Downloads\scripts\Extraccion libros informacion\links.xlsx"
output_dir = "pdfs"

os.makedirs(output_dir, exist_ok=True)
df = pd.read_excel(excel_file)

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

for i, row in df.iterrows():
    titulo = row[" Título del libro"]
    url = row[" URL repositorio"].strip()
    print(f"🔎 Procesando [{i+1}/{len(df)}]: {titulo}")

    try:
        driver.get(url)

        # Esperar hasta 20s a que aparezcan links de bitstreams con download
        try:
            links = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//a[contains(@href, '/bitstreams/') and contains(@href, '/download')]")
                )
            )
        except:
            print(f"⚠️ No se encontró PDF en: {url}")
            continue

        for link in links:
            pdf_url = link.get_attribute("href")
            pdf_name = link.text.strip() or pdf_url.split("/")[-2] + ".pdf"
            pdf_path = os.path.join(output_dir, pdf_name)

            print(f"   ⬇️ Descargando: {pdf_name}")
            try:
                r = requests.get(pdf_url, timeout=30)
                r.raise_for_status()
                with open(pdf_path, "wb") as f:
                    f.write(r.content)
            except Exception as e:
                print(f"   ❌ Error al descargar {pdf_url}: {e}")

    except Exception as e:
        print(f"❌ Error con {url}: {e}")

driver.quit()
print("✅ Proceso terminado. PDFs guardados en:", output_dir)
