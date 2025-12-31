import os
import re
import pandas as pd
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from tempfile import TemporaryDirectory

# -------------------------------
# CONFIGURACIÓN
# -------------------------------
CARPETA_PDF = r"C:\Users\andres.guerra.d\Downloads\scripts\extraer informacion DNDA\DNDA"
SALIDA_EXCEL = r"C:\Users\andres.guerra.d\Downloads\scripts\extraer informacion DNDA\autores_DNDA.xlsx"

# -------------------------------
# FUNCIONES AUXILIARES
# -------------------------------
def limpiar_texto(txt):
    """Limpia saltos, espacios dobles y texto pegado."""
    if not txt:
        return ""
    txt = re.sub(r"([a-z])([A-ZÁÉÍÓÚÑ])", r"\1 \2", txt)
    txt = txt.replace("\n", " ")
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()


def extraer_texto(pdf_path):
    """Extrae texto con pdfplumber o, si falla, con OCR."""
    texto = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                texto += page.extract_text() or ""
    except Exception as e:
        print(f"⚠️ Error leyendo {pdf_path}: {e}")

    if len(texto.strip()) < 50:
        print(f"🧠 Aplicando OCR en {os.path.basename(pdf_path)}...")
        with TemporaryDirectory() as tmpdir:
            images = convert_from_path(pdf_path, dpi=200, output_folder=tmpdir)
            ocr_texts = [pytesseract.image_to_string(img, lang="spa") for img in images]
            texto = "\n".join(ocr_texts)

    return limpiar_texto(texto)


def extraer_datos(pdf_path):
    """Extrae información estructurada desde un certificado DNDA."""
    texto = extraer_texto(pdf_path)

    # -------------------------------
    # DATOS DE LA OBRA
    # -------------------------------
    obra = re.search(r"T[ií]tulo\s+Original\s+(.+?)\s+Año\s+de\s+Creaci[oó]n", texto)
    obra = obra.group(1).strip() if obra else ""

    anio = re.search(r"Año\s+de\s+Creaci[oó]n\s+(\d{4})", texto)
    anio = anio.group(1) if anio else ""

    ambito = re.search(r"AMBITO\s+([A-ZÁÉÍÓÚÑa-z\s\-\–]+)", texto)
    ambito = ambito.group(1).strip() if ambito else ""

    autores = []

    # --- NUEVO patrón general robusto (multi-autor)
    patron_general = re.findall(
        r"AUTOR[\s\-]*Nombres\s*y\s*Apellidos\s*([A-ZÁÉÍÓÚÑ\s]+?)\s*No\s*de\s*identificaci[oó]n\s*(?:C\.?C\.?|C[eé]dula)\s*:?(\d+)"
        r".*?Nacional\s*de\s*([A-ZÁÉÍÓÚÑa-z]+).*?Ciudad[:\s\-]*([A-ZÁÉÍÓÚÑa-z\.\s\-]*)",
        texto, flags=re.DOTALL
    )

    # --- Patrón adicional sin palabra AUTOR
    patron_sin_autor = re.findall(
        r"Nombres\s*y\s*Apellidos\s*([A-ZÁÉÍÓÚÑ\s]+?)\s*No\s*de\s*identificaci[oó]n\s*(?:C\.?C\.?|C[eé]dula)\s*:?(\d+)"
        r".*?Nacional\s*de\s*([A-ZÁÉÍÓÚÑa-z]+).*?Ciudad[:\s\-]*([A-ZÁÉÍÓÚÑa-z\.\s\-]*)",
        texto, flags=re.DOTALL
    )

    # Combinar resultados
    for patron in [patron_general, patron_sin_autor]:
        for a in patron:
            nombre, identificacion, nacionalidad, ciudad = a
            autores.append({
                "Obra": limpiar_texto(obra),
                "Nombre completo": limpiar_texto(nombre),
                "Identificación": "CC " + limpiar_texto(identificacion),
                "Nacionalidad": limpiar_texto(nacionalidad),
                "Ciudad": limpiar_texto(ciudad),
                "Año": limpiar_texto(anio),
                "Ámbito": limpiar_texto(ambito)
            })

    return autores


# -------------------------------
# PROCESAMIENTO MASIVO
# -------------------------------
todos_autores = []

for archivo in os.listdir(CARPETA_PDF):
    if archivo.lower().endswith(".pdf"):
        ruta = os.path.join(CARPETA_PDF, archivo)
        try:
            datos = extraer_datos(ruta)
            todos_autores.extend(datos)
            print(f"✅ Procesado: {archivo} ({len(datos)} autores)")
        except Exception as e:
            print(f"⚠️ Error procesando {archivo}: {e}")

# -------------------------------
# EXPORTAR RESULTADOS
# -------------------------------
if todos_autores:
    df = pd.DataFrame(todos_autores)
    columnas = ["Obra", "Nombre completo", "Identificación", "Nacionalidad", "Ciudad", "Año", "Ámbito"]
    df = df[columnas]
    df.to_excel(SALIDA_EXCEL, index=False)
    print(f"\n📘 Archivo generado correctamente:\n{SALIDA_EXCEL}")
else:
    print("\n⚠️ No se detectaron autores en ningún PDF.")
