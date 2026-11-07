"""DBnomics (API pública que redistribuye bases del FMI, OCDE, Eurostat y otros).

definicion: {fuente: dbnomics, serie: <proveedor/base/código>, hasta_anio: opcional}
Ejemplos: IMF/HPDD/A.AR.GGXWDG_GDP (deuda pública histórica del FMI) o
IMF/WEO:latest/ARG.GGXWDG_NGDP.pcent_gdp (World Economic Outlook). El WEO trae proyecciones:
por defecto se descartan los años posteriores al anterior al actual.
Series anuales, fechadas el 1 de enero de cada año.
"""
from __future__ import annotations

from datetime import date
from functools import lru_cache

import pandas as pd

from . import pedir

URL = "https://api.db.nomics.world/v22/series/{serie}"


@lru_cache(maxsize=128)
def _bajar(serie: str) -> dict:
    return pedir(URL.format(serie=serie), {"observations": 1}).json()


def parsear(js: dict, hasta_anio: int | None = None) -> pd.Series:
    docs = (js.get("series") or {}).get("docs") or []
    if not docs:
        return pd.Series(dtype=float)
    d = docs[0]
    tope = hasta_anio or date.today().year - 1
    datos = {}
    for p, v in zip(d.get("period", []), d.get("value", [])):
        anio = int(str(p)[:4])
        if anio <= tope and v not in (None, "NA") and pd.notna(v):
            datos[anio] = float(v)
    if not datos:
        return pd.Series(dtype=float)
    s = pd.Series(datos, dtype=float)
    s.index = pd.to_datetime([f"{a}-01-01" for a in s.index])
    return s.sort_index()


def extraer(definicion: dict) -> pd.Series:
    return parsear(_bajar(definicion["serie"]), definicion.get("hasta_anio"))
