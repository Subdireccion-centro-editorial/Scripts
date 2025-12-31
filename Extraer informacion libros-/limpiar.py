import os
import re

# --- CONFIGURACIÓN ---
carpeta = r"C:\Users\andres.guerra.d\Downloads\scripts\Extraer informacion libros\pdfs"

for archivo in os.listdir(carpeta):
    if archivo.lower().endswith(".pdf") or ".pdf " in archivo.lower():
        ruta_vieja = os.path.join(carpeta, archivo)

        # Quitar lo que venga después de ".pdf"
        nuevo_nombre = re.sub(r"\.pdf.*", ".pdf", archivo, flags=re.IGNORECASE).strip()

        ruta_nueva = os.path.join(carpeta, nuevo_nombre)

        if ruta_vieja != ruta_nueva:
            os.rename(ruta_vieja, ruta_nueva)
            print(f"✅ Renombrado: {archivo} → {nuevo_nombre}")

print("\nProceso terminado.")
