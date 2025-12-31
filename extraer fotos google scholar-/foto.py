import pandas as pd
import requests
import time
import os
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")

def download_image_with_cookies(driver, url, filename, folder="fotos"):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)

    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://scholar.google.com/"
    }

    response = session.get(url, headers=headers)

    if response.status_code == 200:
        with open(path, "wb") as f:
            f.write(response.content)
        return path

    return None


# -------------------------------------------------
# Configurar Selenium
# -------------------------------------------------

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)


# -------------------------------------------------
# Leer Excel
# -------------------------------------------------

df = pd.read_excel("urls.xlsx")
df["foto_archivo"] = ""


# -------------------------------------------------
# Procesar cada perfil
# -------------------------------------------------

for idx, row in df.iterrows():
    url = row["Google Scholar"]
    cedula = str(row["Cédula"]).strip()

    print(f"Procesando: {url}")

    try:
        driver.get(url)
        time.sleep(3)

        nombre = driver.find_element(By.CSS_SELECTOR, "#gsc_prf_in").text
        print("Nombre detectado:", nombre)

        foto_element = driver.find_element(By.CSS_SELECTOR, "#gsc_prf_pup-img")
        foto_url = foto_element.get_attribute("src")
        print("Foto encontrada:", foto_url)

        # Guardar la foto usando la CÉDULA, no el nombre
        file_name = f"{cedula}.jpg"

        saved_path = download_image_with_cookies(driver, foto_url, file_name)

        if saved_path:
            print("Foto guardada como:", file_name)
            df.at[idx, "foto_archivo"] = file_name
        else:
            print("No se pudo descargar la foto")

    except Exception as e:
        print("Error procesando URL:", e)
        continue


# -------------------------------------------------
# Guardar Excel actualizado
# -------------------------------------------------

output_path = "urls_con_fotos.xlsx"
df.to_excel(output_path, index=False)

print("Proceso completado.")
print("Archivo final:", output_path)
