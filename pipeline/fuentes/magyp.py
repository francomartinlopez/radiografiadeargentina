"""Ministerio de Economía (ganadería): stock bovino al 31 de diciembre por categoría, desde 2007.

Planilla "Serie stock Bovino por provincia al 31-12 (2007-<año>)": una hoja por año con las
existencias por provincia y categoría (datos del SIGSA del SENASA). Se lee la fila "Total".
El nombre del archivo cambia con cada cierre, así que se busca el enlace en la página de informes.
definicion: {fuente: magyp, campo: <categoría o suma de categorías separadas por "+">}
"""
from __future__ import annotations

import io
import re
from functools import lru_cache
from urllib.parse import quote

import pandas as pd

from . import pedir

BASE = "https://www.magyp.gob.ar/sitio/areas/bovinos/informacion_interes/informes/"
CATEGORIAS = ["vacas", "vaquillonas", "novillos", "novillitos", "terneros", "terneras", "toros", "toritos", "bueyes"]


def leer(hojas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """DataFrame año x categoría con el total nacional."""
    filas = {}
    for nombre, df in hojas.items():
        if not re.fullmatch(r"\d{4}", str(nombre).strip()):
            continue
        texto = df.astype(str).apply(lambda c: c.str.strip().str.lower())
        enc = next((i for i in range(len(df)) if texto.iat[i, 0].startswith("provincia")), None)
        if enc is None:
            continue
        tot = next((i for i in range(enc + 1, len(df)) if texto.iat[i, 0].startswith("total")), None)
        if tot is None:
            continue
        cols = {}
        for j in range(1, df.shape[1]):
            for c in CATEGORIAS:
                if texto.iat[enc, j].startswith(c.rstrip("s")) and c not in cols:
                    cols[c] = j
        filas[int(nombre)] = {c: float(pd.to_numeric(df.iat[tot, cols[c]], errors="coerce")) for c in CATEGORIAS if c in cols}
    if not filas:
        raise RuntimeError("La planilla de stock bovino no tiene hojas por año con fila Total")
    tabla = pd.DataFrame(filas).T.sort_index()
    tabla.index = pd.to_datetime(tabla.index.astype(str) + "-01-01")
    return tabla


@lru_cache(maxsize=1)
def tabla() -> pd.DataFrame:
    pagina = pedir(BASE + "index.php").text
    rutas = re.findall(r"_archivos/+000001=[^\"'<>]*Serie stock Bovino por provincia[^\"'<>]*\.xlsx", pagina)
    if not rutas:
        raise RuntimeError("No se encontró la serie de stock bovino por provincia")
    ruta = sorted(set(rutas))[-1].replace("//", "/")
    contenido = pedir(BASE + quote(ruta, safe="/=()_-.")).content
    return leer(pd.read_excel(io.BytesIO(contenido), sheet_name=None, header=None))


def extraer(definicion: dict) -> pd.Series:
    t = tabla()
    return sum(t[c.strip()] for c in definicion["campo"].split("+")).dropna().astype(float)
