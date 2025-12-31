import pdfplumber
import re
import os
import pandas as pd

# --- CONFIGURACIÓN ---
carpeta_pdfs = r"C:\Users\andres.guerra.d\Downloads\scripts\Extraer informacion libros\pdfs"
salida_excel = r"C:\Users\andres.guerra.d\Downloads\scripts\Extraer informacion libros\catalografia.xlsx"

# --- FUNCIÓN DE EXTRACCIÓN ---
def extraer_info(texto):
    # Normalizar espacios
    texto = re.sub(r"\s+", " ", texto)

    data = {
        "ISBN": None,
        "e-ISBN": None,
        "Palabras clave": None,
        "Proyecto": None,
        "Código Proyecto": None,
        "Financiador": None,
        "Grupo de investigación": None,
    }

    # --- Captura todos los posibles ISBNs en el texto ---
    isbn_matches = re.findall(r"(?:e-ISBN|ISBN(?: electrónico)?)[:\s-]*([\d\- ]{10,20})", texto, re.IGNORECASE)

    if isbn_matches:
        # Limpiar números (quitar espacios internos)
        isbn_matches = [num.replace(" ", "") for num in isbn_matches]

        if len(isbn_matches) >= 1:
            data["ISBN"] = isbn_matches[0]
        if len(isbn_matches) >= 2:
            data["e-ISBN"] = isbn_matches[1]

    # Palabras clave (líneas numeradas tipo 1., 2., etc.)
    claves = re.findall(r"\d+\.\s*([^0-9]+?)(?=\s*\d+\.|$)", texto)
    if claves:
        data["Palabras clave"] = " | ".join([c.strip(" -:;") for c in claves])

    # Proyecto (con o sin comillas)
    proyecto_match = re.search(
        r"resultado de la investigaci[oó]n\s*(“([^”]+)”|([^.,]+))",
        texto,
        re.IGNORECASE
    )
    if proyecto_match:
        data["Proyecto"] = proyecto_match.group(2) or proyecto_match.group(3)

    # Código
    codigo_match = re.search(r"c[oó]digo[:\s]*([A-Z0-9\-]+)", texto, re.IGNORECASE)
    if codigo_match:
        data["Código Proyecto"] = codigo_match.group(1)

    # Financiador (financiado / financiada por)
    financiador_match = re.search(r"financiad[ao] por\s*([^.,]+)", texto, re.IGNORECASE)
    if financiador_match:
        data["Financiador"] = financiador_match.group(1).strip()

    # Grupo de investigación
    grupo_match = re.search(r"(grupo[s]? de investigaci[oó]n[^.,]+)", texto, re.IGNORECASE)
    if grupo_match:
        data["Grupo de investigación"] = grupo_match.group(1).strip()

    return data

# --- PROCESAR TODOS LOS PDFs ---
registros = []

for archivo in os.listdir(carpeta_pdfs):
    if archivo.lower().endswith(".pdf"):
        ruta = os.path.join(carpeta_pdfs, archivo)
        print(f"\n📖 Procesando: {archivo}")

        try:
            texto_total = ""
            with pdfplumber.open(ruta) as pdf:
                for page in pdf.pages[:10]:  # primeras 10 páginas
                    texto_total += page.extract_text() or ""

            info = extraer_info(texto_total)
            info["Archivo"] = archivo
            registros.append(info)

        except Exception as e:
            print(f"⚠️ Error leyendo {archivo}: {e}")

# --- EXPORTAR A EXCEL ---
df = pd.DataFrame(registros)
df.to_excel(salida_excel, index=False)

print(f"\n✅ Proceso terminado. Archivo generado en: {salida_excel}")
