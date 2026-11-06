"""NOAA PSL: tablas de índices climáticos en texto (una fila por año, doce columnas mensuales).

Se usa para el Índice Oceánico de El Niño (ONI): https://psl.noaa.gov/data/correlation/oni.data
definicion: {fuente: noaa, url: <tabla>}. Los valores faltantes vienen como -99.9 o -99.99.
"""
from __future__ import annotations

import pandas as pd

from . import pedir


def parsear(texto: str) -> pd.Series:
    datos = {}
    for linea in texto.splitlines():
        partes = linea.split()
        if len(partes) == 13 and partes[0].isdigit() and len(partes[0]) == 4:
            anio = int(partes[0])
            for mes, v in enumerate(partes[1:], start=1):
                try:
                    x = float(v)
                except ValueError:
                    continue
                if x > -90:
                    datos[pd.Timestamp(anio, mes, 1)] = x
    return pd.Series(datos, dtype=float).sort_index()


def extraer(definicion: dict) -> pd.Series:
    return parsear(pedir(definicion["url"]).text)
