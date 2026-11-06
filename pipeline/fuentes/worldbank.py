"""Banco Mundial, World Development Indicators (API pública, sin clave).

definicion: {fuente: worldbank, id: <código del indicador>, pais: <ISO3>}
Se baja el indicador una sola vez para todos los países (caché) y se filtra por país.
Series anuales, fechadas el 1 de enero de cada año.
"""
from __future__ import annotations

from functools import lru_cache

import pandas as pd

from . import pedir

URL = "https://api.worldbank.org/v2/country/all/indicator/{indicador}"


@lru_cache(maxsize=64)
def _bajar(indicador: str) -> tuple:
    filas, pagina, paginas = [], 1, 1
    while pagina <= paginas:
        r = pedir(URL.format(indicador=indicador), {"format": "json", "per_page": 20000, "page": pagina})
        meta, datos = r.json()
        paginas = meta.get("pages", 1)
        filas += [(d["countryiso3code"], d["date"], d["value"]) for d in (datos or [])]
        pagina += 1
    return tuple(filas)


def parsear(filas, pais: str) -> pd.Series:
    datos = [(int(a), v) for p, a, v in filas if p == pais and v is not None and str(a).isdigit()]
    if not datos:
        return pd.Series(dtype=float)
    s = pd.Series([v for _, v in datos], index=pd.to_datetime([f"{a}-01-01" for a, _ in datos]), dtype=float)
    return s[~s.index.duplicated()].sort_index()


def extraer(definicion: dict) -> pd.Series:
    return parsear(_bajar(definicion["id"]), definicion["pais"])
