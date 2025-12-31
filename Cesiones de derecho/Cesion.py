import pdfplumber
import re
import pandas as pd
from pathlib import Path
import csv

# ======================================
# CONFIG
# ======================================
CARPETA_PDFS = Path("SESIONES DEDERECHO")
SALIDA_CSV = "sesiones_derecho_extraidas.csv"

# ======================================
# UTILIDADES
# ======================================
def limpiar_texto(valor):
    if not valor:
        return None
    return (
        valor
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("  ", " ")
        .strip()
    )


def extraer_texto(pdf_path):
    texto = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texto += t + " "
    return texto


def buscar(regex, texto, group=1):
    match = re.search(regex, texto, re.IGNORECASE | re.DOTALL)
    return limpiar_texto(match.group(group)) if match else None


def procesar_pdf(pdf_path):
    texto = extraer_texto(pdf_path)

    return {
        "archivo": pdf_path.name,
        "tipo_documento": buscar(r"(CONTRATO DE CESIÓN DE DERECHOS PATRIMONIALES)", texto),
        "fecha_documento": buscar(r"(\d{1,2}/[A-Za-z]+/\d{4})", texto),
        "institucion": buscar(r"(CORPORACIÓN UNIVERSITARIA MINUTO DE DIOS\s*–?\s*UNIMINUTO)", texto),
        "autor": buscar(r"por la otra,\s+([A-ZÁÉÍÓÚÑ\s]+),\s+mayor de edad", texto),
        "cedula_autor": buscar(r"c[eé]dula de ciudadanía No\.?\s*([\d\.]+)", texto),
        "titulo_obra": buscar(r"capítulo denominado\s+“([^”]+)”", texto),
        "libro": buscar(r"del libro\s+“([^”]+)”", texto),
        "derechos_patrimoniales": "Cedidos",
        "derechos_morales": "No cedidos",
        "exclusividad": "Sí",
        "ambito": "Internacional",
        "vigencia": buscar(
            r"VIGENCIA[:\s]+El presente contrato de cesión se extenderá por\s+([^\.]+)",
            texto
        )
    }

# ======================================
# PROCESO
# ======================================
registros = []

for pdf in CARPETA_PDFS.glob("*.pdf"):
    print(f"📄 Procesando {pdf.name}")
    registros.append(procesar_pdf(pdf))

df = pd.DataFrame(registros)

df.to_csv(
    SALIDA_CSV,
    index=False,
    encoding="utf-8-sig",
    quoting=csv.QUOTE_ALL
)

print(f"\n✅ CSV limpio y correcto generado: {SALIDA_CSV}")
