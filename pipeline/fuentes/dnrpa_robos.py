"""DNRPA: denuncias de robo o hurto y comunicaciones de recupero de automotores, por mes.

El Ministerio de Justicia publica un archivo por trámite (un registro por vehículo) en un zip
por año desde 2018, más el mes recién cerrado. Se cuentan los trámites por mes y tipo, y los
años cerrados se guardan resumidos en data/crudos/dnrpa_robos/<año>.csv para no volver a
bajarlos. definicion: {fuente: dnrpa_robos, tipo: robo | recupero}
"""
from __future__ import annotations

import io
import zipfile
from functools import lru_cache
from pathlib import Path

import pandas as pd

from . import pedir

API = "https://datos.gob.ar/api/3/action/package_show"
PAQUETE = "justicia-robos-recuperos-autos"
CARPETA = Path(__file__).resolve().parents[2] / "data" / "crudos" / "dnrpa_robos"
TIPOS = {"robo": "DENUNCIA DE ROBO", "recupero": "RECUPERO"}


def contar(texto: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(texto), usecols=["tramite_tipo", "tramite_fecha"], dtype=str)
    df["fecha"] = pd.to_datetime(df["tramite_fecha"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    df["tipo"] = None
    for clave, patron in TIPOS.items():
        df.loc[df["tramite_tipo"].str.upper().str.contains(patron, na=False), "tipo"] = clave
    return df.dropna(subset=["fecha", "tipo"]).groupby(["fecha", "tipo"]).size().rename("cantidad").reset_index()


def _textos(contenido: bytes, url: str) -> list[str]:
    if url.lower().endswith(".zip"):
        z = zipfile.ZipFile(io.BytesIO(contenido))
        return [z.read(n).decode("utf-8-sig") for n in z.namelist() if n.lower().endswith(".csv")]
    return [contenido.decode("utf-8-sig")]


@lru_cache(maxsize=1)
def tabla() -> pd.DataFrame:
    recursos = pedir(API, {"id": PAQUETE}).json()["result"]["resources"]
    hoy = pd.Timestamp.today()
    partes = []
    for r in recursos:
        nombre = r["name"].strip()
        anio = nombre[-4:]
        cerrado = anio.isdigit() and int(anio) < hoy.year
        cache = CARPETA / f"{anio}.csv"
        if cerrado and cache.exists():
            partes.append(pd.read_csv(cache, parse_dates=["fecha"]))
            continue
        df = pd.concat([contar(t) for t in _textos(pedir(r["url"]).content, r["url"])])
        if cerrado:
            CARPETA.mkdir(parents=True, exist_ok=True)
            df.to_csv(cache, index=False, date_format="%Y-%m-%d")
        partes.append(df)
    df = pd.concat(partes)
    # El archivo del último mes puede repetir meses del zip anual: se queda el mayor conteo
    return df.groupby(["fecha", "tipo"])["cantidad"].max().reset_index()


def extraer(definicion: dict) -> pd.Series:
    df = tabla()
    s = df[df["tipo"] == definicion["tipo"]].set_index("fecha")["cantidad"].sort_index().astype(float)
    return s[s.index < pd.Timestamp.today().normalize().replace(day=1)]
