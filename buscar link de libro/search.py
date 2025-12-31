import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from difflib import SequenceMatcher

# --- 1. Cargar Excel ---
df = pd.read_excel("links.xlsx")
df.columns = df.columns.str.strip()

# --- 2. Configuración de Selenium ---
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def buscar_libro(titulo):
    try:
        # Ir a Google
        driver.get("https://www.google.com/")
        time.sleep(2)

        # Escribir búsqueda "<nombre del libro> repositorio uniminuto"
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(f'"{titulo}" repositorio uniminuto')
        search_box.send_keys(Keys.RETURN)
        time.sleep(3)

        # Probar varios resultados de Google
        resultados = driver.find_elements(By.CSS_SELECTOR, "a")
        for r in resultados:
            href = r.get_attribute("href")
            if href and "repository.uniminuto.edu" in href:
                driver.get(href)
                time.sleep(3)

                # Intentar extraer el título del repositorio (h1 en DSpace)
                try:
                    titulo_repo = driver.find_element(By.TAG_NAME, "h1").text
                    score = similar(titulo, titulo_repo)
                    print(f"🔎 Comparando: {titulo} ↔ {titulo_repo} (score {score:.2f})")

                    if score > 0.7:  # umbral de similitud
                        return driver.current_url
                except:
                    continue
        return "no encontrado"
    except Exception as e:
        print(f"❌ Error con {titulo}: {e}")
        return "no encontrado"

# --- 3. Iterar libros ---
for idx, row in df.iterrows():
    if pd.isna(row["URL repositorio"]) or row["URL repositorio"] == "":
        titulo = row["Título del libro"]
        print(f"🔎 Buscando: {titulo}")
        url = buscar_libro(titulo)
        df.at[idx, "URL repositorio"] = url
        print(f"✅ {titulo} -> {url}")

# --- 4. Guardar resultados ---
df.to_excel("links_actualizados.xlsx", index=False)

driver.quit()
