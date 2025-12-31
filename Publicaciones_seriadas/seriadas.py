#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor robusto para certificados ISSN (Biblioteca Nacional de Colombia).
Evita corrimientos validando cada campo por tipo antes de asignarlo.

- Procesa TODOS los PDFs en una carpeta (recursivo).
- No confía en posiciones fijas: valida formato de cada campo.
- Exporta a Excel (.xlsx) y opcionalmente JSON.
- Valida checksum del ISSN (issn_valido).

Uso:
  python seriadas.py                      # usa DEFAULT_DIR
  python seriadas.py --dir "C:/ruta"      # usa la carpeta indicada
  python seriadas.py --dir "C:/ruta" --out "salida.xlsx" --json
"""

import os, re, argparse
from typing import List, Dict, Iterable, Callable, Optional
from PyPDF2 import PdfReader
import pandas as pd

# 📂 Carpeta por defecto (ajusta a tu ruta)
DEFAULT_DIR = r"C:\Users\andres.guerra.d\Downloads\scripts\Publicaciones_seriadas\PDF's"

# -------------------- Catálogos y validadores --------------------

PERIODICIDAD = {
    "anual","semestral","trimestral","bimestral","mensual","quincenal","semanal","diario","irregular",
    "bienal","otro","desconocido"
}

def is_issn(s: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{3}[\dX]|\d{4}-\d{4}", s.strip()))

def issn_checksum_ok(issn: str) -> bool:
    s = issn.upper().replace("-", "").replace(" ", "")
    if not re.fullmatch(r"\d{7}[\dX]", s):
        return False
    total = 0
    for i, ch in enumerate(s[:7], start=1):  # pesos 8..2
        total += int(ch) * (9 - i)
    check = 10 if s[7] == "X" else int(s[7])
    total += check * 1
    return total % 11 == 0

def is_fecha_asignacion(s: str) -> bool:
    # ejemplos: 02/03/2023 12:00, 2/3/2023 0:00, 22/01/2015 12:00
    return bool(re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2,4}(?:\s+\d{1,2}:\d{2})?", s.strip()))

def is_periodicidad(s: str) -> bool:
    return s.strip().lower() in PERIODICIDAD

def is_soporte(s: str) -> bool:
    return bool(re.search(r"(electr|en\s+l[ií]nea|impreso|papel|otro soporte)", s, flags=re.IGNORECASE))

def is_titulo_abreviado(s: str) -> bool:
    # suele traer paréntesis o abreviaturas; evita líneas de un solo token en mayúsculas
    s2 = s.strip()
    if len(s2) < 3 or len(s2) > 120:
        return False
    if "(" in s2 and ")" in s2:
        return True
    # Si no tiene paréntesis, al menos que tenga un punto como abreviatura "Mem."
    return "." in s2 and not s2.isupper()

def is_editor(s: str) -> bool:
    # muchas veces todo en mayúscula y largo razonable
    s2 = s.strip()
    return len(s2) >= 6 and bool(re.search(r"[A-ZÁÉÍÓÚÑ]{3}", s2)) and (s2.isupper() or "UNIMINUTO" in s2.upper())

def is_titulo(s: str) -> bool:
    # título normal: varias palabras, no solo mayúsculas, 3..200 chars
    s2 = s.strip()
    if len(s2) < 3 or len(s2) > 200:
        return False
    # Evita capturar rótulos sueltos tipo "Título:" o textos largos del cuerpo
    if s2.endswith(":"):
        return False
    # No lineas que parecen URLs o correos
    if s2.startswith("http") or "mailto:" in s2:
        return False
    return True

# -------------------- Lectura y helpers --------------------

def extract_lines(path: str) -> List[str]:
    r = PdfReader(path)
    lines=[]
    for page in r.pages:
        t = page.extract_text() or ""
        for ln in t.replace("\r","\n").split("\n"):
            lines.append(ln.strip())
    return [ln for ln in lines]  # preserva vacías (para navegación), pero ya strip

def iter_pdfs(directory: str) -> Iterable[str]:
    for root, _, files in os.walk(directory):
        for fn in files:
            if fn.lower().endswith(".pdf"):
                yield os.path.join(root, fn)

def next_nonempty(lines: List[str], k: int) -> Optional[int]:
    n = len(lines)
    k += 1
    while k < n and lines[k].strip() == "":
        k += 1
    return k if k < n else None

# -------------------- Parser tolerante --------------------

def scan_forward(lines: List[str], start_idx: int, validator: Callable[[str], bool], max_lookahead: int = 8) -> Optional[str]:
    """
    Busca hacia adelante hasta max_lookahead líneas no vacías que cumplan el validador.
    Si no encuentra, devuelve None (no desplaza otros campos).
    """
    idx = start_idx
    steps = 0
    while steps < max_lookahead:
        idx = next_nonempty(lines, idx)
        if idx is None:
            return None
        cand = lines[idx].strip()
        # cortar si encontramos otro rótulo común del cuerpo que no son valores
        if cand.lower() in {"certifica:", "publicación seriada cuyos datos son:", "issn asignado:", "título:", "título abreviado:", "editor:", "periodicidad:", "soporte:", "fecha de asignación:"}:
            steps += 1
            continue
        if cand.startswith("http") or "mailto:" in cand:
            steps += 1
            continue
        if validator(cand):
            return cand
        steps += 1
    return None

def parse_certificate_date(lines: List[str]) -> str:
    # Busca "a los DD de MES de YYYY"
    joined = " ".join([ln for ln in lines if ln]).strip()
    m = re.search(r"a los\s+(\d{1,2})\s+de\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+de\s+(\d{4})", joined, flags=re.IGNORECASE)
    MONTHS = {
        "enero":"01","febrero":"02","marzo":"03","abril":"04","mayo":"05","junio":"06",
        "julio":"07","agosto":"08","septiembre":"09","setiembre":"09","octubre":"10",
        "noviembre":"11","diciembre":"12",
        "Enero":"01","Febrero":"02","Marzo":"03","Abril":"04","Mayo":"05","Junio":"06",
        "Julio":"07","Agosto":"08","Septiembre":"09","Setiembre":"09","Octubre":"10",
        "Noviembre":"11","Diciembre":"12"
    }
    if m:
        d, mon, y = m.groups()
        mn = MONTHS.get(mon, MONTHS.get(mon.lower(), ""))
        if mn:
            return f"{y}-{mn}-{int(d):02d}"
    # Fallback: “DD Mes” + “YYYY” en otro lado (toma los últimos)
    dm = None
    for ln in lines:
        m2 = re.search(r"\b(\d{1,2})\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\b", ln)
        if m2:
            d, mon = m2.groups()
            mn = MONTHS.get(mon, MONTHS.get(mon.lower(), ""))
            if mn:
                dm = (int(d), mn)
    y = None
    for ln in reversed(lines):
        m3 = re.search(r"\b(19|20)\d{2}\b", ln)
        if m3:
            y = m3.group(0); break
    if dm and y:
        return f"{y}-{dm[1]}-{dm[0]:02d}"
    return ""

def extract_from_pdf(path: str) -> Dict[str, str]:
    try:
        lines = extract_lines(path)

        # 1) ISSN (en cualquier parte)
        issn_idx = None
        issn_val = None
        for i, ln in enumerate(lines):
            if is_issn(ln):
                issn_idx = i
                issn_val = ln.strip()
        data: Dict[str, str] = {}
        if issn_val:
            data["ISSN asignado"] = issn_val
            data["issn_valido"] = issn_checksum_ok(issn_val)
        else:
            data["issn_valido"] = False  # seguirá vacío si no hay ISSN

        # 2) Desde ISSN (si existe) buscar cada campo con su validador individual
        start = issn_idx if issn_idx is not None else -1

        # Título
        titulo = scan_forward(lines, start, is_titulo, max_lookahead=10)
        if titulo: data["Título"] = titulo

        # Título abreviado
        tit_ab = scan_forward(lines, start if titulo is None else lines.index(titulo), is_titulo_abreviado, max_lookahead=10)
        if tit_ab: data["Título abreviado"] = tit_ab

        # Editor
        editor = scan_forward(lines, start if tit_ab is None else lines.index(tit_ab), is_editor, max_lookahead=12)
        if editor: data["Editor"] = editor

        # Periodicidad
        per = scan_forward(lines, start if editor is None else lines.index(editor), is_periodicidad, max_lookahead=12)
        if per: data["Periodicidad"] = per

        # Soporte
        sop = scan_forward(lines, start if per is None else lines.index(per), is_soporte, max_lookahead=12)
        if sop: data["Soporte"] = sop

        # Fecha de asignación
        f_asig = scan_forward(lines, start if sop is None else lines.index(sop), is_fecha_asignacion, max_lookahead=15)
        if f_asig: data["Fecha de asignación"] = f_asig

        # 3) Fecha del certificado (independiente)
        data["Fecha del certificado"] = parse_certificate_date(lines)

        # 4) Contexto
        data["archivo"] = os.path.basename(path)
        return data
    except Exception as e:
        return {"archivo": os.path.basename(path), "error": str(e)}

# -------------------- CLI --------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", help="Carpeta con PDFs (recursivo). Si se omite, usa DEFAULT_DIR.")
    ap.add_argument("--out", default="issn_certificados.xlsx", help="Ruta de salida Excel (.xlsx)")
    ap.add_argument("--json", action="store_true", help="Además del Excel, exporta JSON")
    args = ap.parse_args()

    target_dir = args.dir or DEFAULT_DIR
    if not os.path.isdir(target_dir):
        raise SystemExit(f"❌ Carpeta no encontrada: {target_dir}")

    pdfs = list(iter_pdfs(target_dir))
    if not pdfs:
        raise SystemExit(f"❌ No se encontraron PDFs en {target_dir}")

    print(f"Procesando {len(pdfs)} PDF(s) desde {target_dir}...\n")
    rows = [extract_from_pdf(p) for p in pdfs]

    df = pd.DataFrame(rows)
    ordered = ["archivo","ISSN asignado","issn_valido","Título","Título abreviado","Editor",
               "Periodicidad","Soporte","Fecha de asignación","Fecha del certificado","error"]
    cols = [c for c in ordered if c in df.columns] + [c for c in df.columns if c not in ordered]
    df = df[cols]
    df.to_excel(args.out, index=False)
    print(f"\n✅ Excel guardado en: {args.out}")

    if args.json:
        base, _ = os.path.splitext(args.out)
        df.to_json(base + ".json", force_ascii=False, orient="records", indent=2)
        print(f"✅ JSON guardado en: {base+'.json'}")

if __name__ == "__main__":
    main()
