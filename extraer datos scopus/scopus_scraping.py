import pandas as pd
import requests
import re
import time

# ===============================
# CREDENCIALES SCOPUS (INSTITUCIONAL)
# ===============================
API_KEY = "c2ed9a2046ec9b78394c0647780a46f4"
INST_TOKEN = "87453dca35793144e15c757c9d486db5"

# ===============================
# ARCHIVOS
# ===============================
EXCEL_IN = "scopus.xlsx"
EXCEL_OUT = "scopus_completo_api.xlsx"


# ===============================
# UTILIDADES
# ===============================
def extraer_author_id(url):
    if pd.isna(url):
        return None
    m = re.search(r"authorId=(\d+)", str(url))
    return m.group(1) if m else None


def consultar_autor_scopus(author_id):
    url = f"https://api.elsevier.com/content/author/author_id/{author_id}"

    headers = {
        "X-ELS-APIKey": API_KEY,
        "X-ELS-Insttoken": INST_TOKEN,
        "Accept": "application/json"
    }

    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()

    data = r.json()["author-retrieval-response"][0]["coredata"]

    documentos = int(data.get("document-count", 0))
    citaciones = int(data.get("citation-count", 0))

    return documentos, citaciones


# ===============================
# PROCESO PRINCIPAL
# ===============================
def main():
    df = pd.read_excel(EXCEL_IN)

    if "Citaciones en Scopus" not in df.columns:
        df["Citaciones en Scopus"] = ""

    if "Número de documentos en Scopus con citaciones" not in df.columns:
        df["Número de documentos en Scopus con citaciones"] = ""

    if "Índice H Scopus" not in df.columns:
        df["Índice H Scopus"] = "NO DISPONIBLE (API SCOPUS)"

    for i, row in df.iterrows():
        nombre = row.get("Nombre Apellido", f"Fila {i}")
        author_id = extraer_author_id(row.get("Scopus"))

        if not author_id:
            print(f"⏭️ {nombre} — sin authorId")
            continue

        try:
            docs, cites = consultar_autor_scopus(author_id)

            df.at[i, "Número de documentos en Scopus con citaciones"] = docs
            df.at[i, "Citaciones en Scopus"] = cites

            print(f"✔ {nombre} → Docs: {docs} | Citas: {cites}")
            time.sleep(1)

        except Exception as e:
            print(f"❌ ERROR {nombre}: {e}")

    df.to_excel(EXCEL_OUT, index=False)
    print("\n✅ Archivo generado:", EXCEL_OUT)


if __name__ == "__main__":
    main()