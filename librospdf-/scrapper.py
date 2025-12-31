from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests, os, time

# ---------------- CONFIG ----------------
USER = "8001162172"
PASSWORD = "lib2017"
LOGIN_URL = "https://isbn.camlibro.com.co/index.php"
LISTADO_URL = "https://isbn.camlibro.com.co/user.php?mode=listado_titulos&currentPage=1"
# ----------------------------------------

# Configurar navegador
options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # si quieres que no se vea la ventana
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

wait = WebDriverWait(driver, 15)

# 1. Abrir página
print("👉 Abriendo página...")
driver.get(LOGIN_URL)

# 2. Click en "Iniciar sesión"
print("👉 Buscando botón de login...")
login_btn = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Iniciar sesión")))
login_btn.click()

# 3. Esperar a que aparezca el formulario
print("👉 Esperando formulario...")
usuario_input = wait.until(EC.visibility_of_element_located((By.NAME, "usuario")))
contrasena_input = wait.until(EC.visibility_of_element_located((By.NAME, "contrasena")))

# 4. Enviar credenciales
print("👉 Enviando credenciales...")
usuario_input.send_keys(USER)
contrasena_input.send_keys(PASSWORD + Keys.RETURN)

# 5. Ir al listado
print("👉 Esperando login exitoso...")
wait.until(EC.url_changes(LOGIN_URL))
driver.get(LISTADO_URL)
time.sleep(3)

pdf_links = set()
page = 1

# 6. Recorrer todas las páginas
while True:
    time.sleep(2)

    # capturar íconos con onclick=pdfTitulo(ID)
    icons = driver.find_elements(By.CSS_SELECTOR, "a[onclick^='pdfTitulo']")
    for icon in icons:
        onclick_value = icon.get_attribute("onclick")  # ej: "pdfTitulo(481905)"
        book_id = onclick_value.split("(")[1].split(")")[0]
        link = f"https://isbn.camlibro.com.co/pdfisbn.php?idTitulo={book_id}&numShow=0"
        pdf_links.add(link)

    print(f"✅ Página {page} procesada, total acumulado: {len(pdf_links)} PDFs")
    page += 1

    try:
        next_btn = driver.find_element(By.LINK_TEXT, "›")
        next_btn.click()
    except:
        break

driver.quit()

print(f"🔎 Se encontraron {len(pdf_links)} PDFs en total")

# 7. Descargar PDFs
os.makedirs("pdfs", exist_ok=True)

for link in pdf_links:
    try:
        book_id = link.split("idTitulo=")[1].split("&")[0]
        print(f"⬇️ Descargando {book_id} ...")
        r = requests.get(link, timeout=20)
        if r.status_code == 200:
            with open(f"pdfs/{book_id}.pdf", "wb") as f:
                f.write(r.content)
            print(f"✅ {book_id} descargado")
        else:
            print(f"❌ Error con {link}")
    except Exception as e:
        print(f"⚠️ Falló {link}: {e}")
