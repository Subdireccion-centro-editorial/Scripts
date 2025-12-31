import pandas as pd
import re

# Archivo de entrada y salida
input_file = "Formato_perfil_autores.xlsx"
output_file = "autores_consolidados_limpio.xlsx"

# Cargar el archivo original
excel = pd.ExcelFile(input_file)
autores = []

# Recorremos todas las hojas
for sheet in excel.sheet_names:
    try:
        df = excel.parse(sheet, header=None)

        # Buscar la fila que contiene 'Nombres'
        header_row = None
        for i, row in df.iterrows():
            if row.astype(str).str.contains("Nombres", case=False, na=False).any():
                header_row = i
                break

        if header_row is None:
            continue

        # Leer nuevamente la hoja desde esa fila como encabezado
        df = excel.parse(sheet, header=header_row)

        # Filtrar columnas relevantes
        columnas_clave = [
            "Nombres", "Apellidos", "Número de identificación",
            "Nacionalidad", "Correo electrónico", "Teléfono",
            "Rectoría", "Rol", "Filiación institucional (Si es autor externo)"
        ]
        df = df[[col for col in columnas_clave if col in df.columns]]

        # Agregar nombre de la hoja (capítulo)
        df["Hoja"] = sheet

        # --- LIMPIEZA ---
        # Quitar filas completamente vacías
        df = df.dropna(how="all")

        # Quitar textos que no son nombres válidos
        patrones_excluir = [
            "Huella digital", "Descripción", "CvLAC", "ORCID",
            "Google Scholar", "ResearchGate", "Código", "https://",
            "www.", "Autor", "autora"
        ]
        mask = df["Nombres"].astype(str).apply(
            lambda x: not any(re.search(pat, x, re.IGNORECASE) for pat in patrones_excluir)
        )
        df = df[mask]

        # Quitar filas donde Nombres o Apellidos estén vacíos
        df = df[df["Nombres"].notna() & df["Apellidos"].notna()]

        # Limpiar espacios
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        # Agregar al consolidado
        autores.append(df)

    except Exception as e:
        print(f"⚠️ Error en {sheet}: {e}")

# Unir todas las hojas
if autores:
    consolidado = pd.concat(autores, ignore_index=True)
    consolidado.to_excel(output_file, index=False)
    print(f"✅ Consolidado limpio generado: {output_file}")
else:
    print("No se encontraron autores válidos.")
