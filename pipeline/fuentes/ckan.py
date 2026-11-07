"""Recursos CSV del portal datos.gob.ar cuya dirección cambia en cada publicación.

Se busca el recurso por nombre dentro del paquete (API de CKAN) y se suma una columna por
año y mes. definicion:
  {fuente: ckan, paquete: <nombre del paquete>, recurso: <parte del nombre del recurso>,
   anio: <columna del año>, mes: <columna del mes>, valor: <columna a sumar>,
   filtro: {<columna>: <valor>}}   (filtro opcional)
"""
from __future__ import annotations

import io
from functools import lru_cache

import pandas as pd

from . import pedir

API = "https://datos.gob.ar/api/3/action/package_show"


@lru_cache(maxsize=16)
def _recurso(paquete: str, recurso: str) -> str:
    datos = pedir(API, {"id": paquete}).json()["result"]
    for r in datos["resources"]:
        if recurso.lower() in r["name"].lower() and r["url"].lower().endswith(".csv"):
            return pedir(r["url"]).content.decode("utf-8-sig")
    raise RuntimeError(f"No hay un recurso '{recurso}' en {paquete}")


def parsear(texto: str, anio: str, mes: str, valor: str, filtro: dict | None = None) -> pd.Series:
    df = pd.read_csv(io.StringIO(texto))
    for col, val in (filtro or {}).items():
        df = df[df[col].astype(str) == str(val)]
    df[valor] = pd.to_numeric(df[valor], errors="coerce")
    fechas = pd.to_datetime(df[anio].astype(int).astype(str) + "-" + df[mes].astype(int).astype(str).str.zfill(2) + "-01")
    return df.groupby(fechas)[valor].sum().sort_index().astype(float)


def extraer(definicion: dict) -> pd.Series:
    texto = _recurso(definicion["paquete"], definicion["recurso"])
    return parsear(texto, definicion["anio"], definicion["mes"], definicion["valor"], definicion.get("filtro"))
