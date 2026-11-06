"""CSV publicado en una URL (por ejemplo, los conjuntos de Our World in Data en GitHub).

definicion: {fuente: csv_url, url: ..., filtro: {columna: valor}, fecha: <columna de año o fecha>, valor: <columna>}
Si la columna de fecha es un año (número), el dato se fecha el 1 de enero.
"""
from __future__ import annotations

import io
from functools import lru_cache

import pandas as pd

from . import pedir


@lru_cache(maxsize=8)
def _bajar(url: str) -> str:
    return pedir(url).text


def parsear(texto: str, definicion: dict) -> pd.Series:
    df = pd.read_csv(io.StringIO(texto))
    for col, val in (definicion.get("filtro") or {}).items():
        df = df[df[col] == val]
    fechas = df[definicion["fecha"]]
    if pd.api.types.is_numeric_dtype(fechas):
        df = df[fechas >= 1700]  # las fechas anteriores no entran en el rango de pandas
        fechas = df[definicion["fecha"]]
        idx = pd.to_datetime(fechas.astype(int).astype(str) + "-01-01", format="%Y-%m-%d")
    else:
        idx = pd.to_datetime(fechas)
    s = pd.Series(pd.to_numeric(df[definicion["valor"]], errors="coerce").values, index=idx, dtype=float).dropna()
    return s[~s.index.duplicated(keep="last")].sort_index()


def extraer(definicion: dict) -> pd.Series:
    return parsear(_bajar(definicion["url"]), definicion)
