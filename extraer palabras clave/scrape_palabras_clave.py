import pandas as pd
import time
import random
import os
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# ========== CONFIG ==========
INPUT_FILE = "Palabras Clave.xlsx"
OUTPUT_FILE = "Palabras_Claves_Completas.xlsx"
URL_COLUMN = " URL repositorio"   # cuidado con espacio inicial
SLEEP_MIN, SLEEP_MAX = 1.5, 3.5
SAVE_EVERY = 10
# =============================

def iniciar_driver():
    """Inicia Chrome en modo headless (sin ventana visible)."""
    chrome_opts = Options()
    chrome_opts.add_argument("--headless=new")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    chrome_opts.add_argument("--window-size=1920,1080")
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--log-level=3")
    return webdriver.Chrome(options=chrome_opts)


def extraer_datos(driver, url):
    """Extrae Palabras clave y DOI desde una página del repositorio UNIMINUTO."""
    try:
        driver.get(url)
        time.sleep(4)  # esperar a que Angular cargue el contenido

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # ====== PALABRAS CLAVE ======
        header_palabras = soup.find("h2", string=lambda s: s and "palabras clave" in s.lower())
        palabras = "No encontradas"
        if header_palabras:
            body = header_palabras.find_next("div", class_="simple-view-element-body")
            if body:
                spans = body.find_all("span", class_="dont-break-out preserve-line-breaks ng-star-inserted")
                lista = [s.get_text(strip=True) for s in spans if s.get_text(strip=True)]
                if lista:
                    palabras = ", ".join(lista)

        # ====== DOI ======
        header_uri = soup.find("h2", string=lambda s: s and "uri" in s.lower())
        doi = "No encontrado"
        if header_uri:
            body_uri = header_uri.find_next("div", class_="simple-view-element-body")
            if body_uri:
                enlaces = body_uri.find_all("a", href=True)
                for a in enlaces:
                    href = a["href"].strip()
                    if "doi.org" in href:
                        doi = href
                        break

        return palabras, doi

    except Exception as e:
        return f"Error: {e}", "Error"


def main():
    print("🔍 Cargando archivo Excel...")
    df = pd.read_excel(INPUT_FILE)

    # Añadir columnas si no existen
    if "Palabras Clave Scrapeadas" not in df.columns:
        df["Palabras Clave Scrapeadas"] = ""
    if "DOI" not in df.columns:
        df["DOI"] = ""

    # Si ya hay archivo previo, retomamos el progreso
    if os.path.exists(OUTPUT_FILE):
        print("♻️ Retomando progreso anterior...")
        df_out = pd.read_excel(OUTPUT_FILE)
        for col in ["Palabras Clave Scrapeadas", "DOI"]:
            if col in df_out.columns:
                df[col] = df_out[col]

    driver = iniciar_driver()
    print("🚀 Iniciando Selenium scraping...\n")

    for i, row in tqdm(df.iterrows(), total=len(df)):
        # Saltar si ya está completado
        if pd.notna(row.get("Palabras Clave Scrapeadas")) and str(row["Palabras Clave Scrapeadas"]).strip() not in ["", "No encontradas"]:
            continue

        url = str(row[URL_COLUMN]).strip()
        if not url.startswith("http"):
            df.at[i, "Palabras Clave Scrapeadas"] = "URL inválida"
            df.at[i, "DOI"] = "URL inválida"
            continue

        palabras, doi = extraer_datos(driver, url)
        df.at[i, "Palabras Clave Scrapeadas"] = palabras
        df.at[i, "DOI"] = doi

        # Guardado incremental
        if (i + 1) % SAVE_EVERY == 0:
            df.to_excel(OUTPUT_FILE, index=False)
            print(f"💾 Guardado parcial en fila {i + 1}")

        time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))

    driver.quit()
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\n✅ Proceso completado. Archivo guardado como: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
