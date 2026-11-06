"""FMI, World Economic Outlook vía DataMapper (API pública, sin clave).

definicion: {fuente: imf, id: <indicador, p. ej. GGXWDG_NGDP>, pais: <ISO3>, hasta_anio: opcional}
Incluye proyecciones del FMI para los años futuros: por defecto se descartan los años
posteriores al actual (las proyecciones no son datos).
"""
from __future__ import annotations

from datetime import date
from functools import lru_cache

import pandas as pd

from . import pedir

URL = "https://www.imf.org/external/datamapper/api/v1/{indicador}"


@lru_cache(maxsize=64)
def _bajar(indicador: str) -> dict:
    return pedir(URL.format(indicador=indicador)).json()


def parsear(js: dict, indicador: str, pais: str, hasta_anio: int | None = None) -> pd.Series:
    valores = (js.get("values", {}).get(indicador, {}) or {}).get(pais, {}) or {}
    tope = hasta_anio or date.today().year - 1
    datos = {int(a): v for a, v in valores.items() if v is not None and int(a) <= tope}
    if not datos:
        return pd.Series(dtype=float)
    s = pd.Series(datos, dtype=float)
    s.index = pd.to_datetime([f"{a}-01-01" for a in s.index])
    return s.sort_index()


def extraer(definicion: dict) -> pd.Series:
    return parsear(_bajar(definicion["id"]), definicion["id"], definicion["pais"], definicion.get("hasta_anio"))
