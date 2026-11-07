"""Ejecución presupuestaria de la Administración Pública Nacional por servicio (SAF).

Fuente: Ministerio de Economía, Secretaría de Hacienda, "Presupuesto de gastos y su ejecución
detallada - agrupación mensual" (dgsiaf-repo.mecon.gob.ar), un archivo por año desde 1995.

Cada archivo pesa cientos de megabytes, así que se resume una sola vez por año en
data/crudos/presupuesto/credito_<año>.csv (gasto devengado por servicio y mes, en millones de
pesos corrientes). En cada corrida solo se vuelven a bajar el año en curso y el anterior.

definicion: {fuente: presupuesto, id: [<servicio_id>, ...]}  (varios códigos se suman: sirve
para organismos que cambiaron de código o se fusionaron)
"""
from __future__ import annotations

import io
import time
import zipfile
from functools import lru_cache
from pathlib import Path

import pandas as pd

from . import pedir

URL = "https://dgsiaf-repo.mecon.gob.ar/repository/pa/datasets/{a}/credito-mensual-{a}.zip"
CARPETA = Path(__file__).resolve().parents[2] / "data" / "crudos" / "presupuesto"
DESDE = 2001
COLUMNAS = ["impacto_presupuestario_anio", "impacto_presupuestario_mes", "servicio_id", "servicio_desc", "credito_devengado"]


def resumir(fuente) -> pd.DataFrame:
    """Suma el devengado por servicio y mes de un CSV de crédito mensual (archivo o texto)."""
    partes = []
    for trozo in pd.read_csv(fuente, usecols=COLUMNAS, dtype=str, chunksize=200_000, encoding="utf-8-sig"):
        trozo["credito_devengado"] = pd.to_numeric(trozo["credito_devengado"].str.replace(",", ".", regex=False),
                                                   errors="coerce")
        partes.append(trozo.groupby(COLUMNAS[:4], dropna=False)["credito_devengado"].sum().reset_index())
    df = pd.concat(partes).groupby(COLUMNAS[:4], dropna=False)["credito_devengado"].sum().reset_index()
    df["fecha"] = pd.to_datetime(df["impacto_presupuestario_anio"].str.strip() + "-"
                                 + df["impacto_presupuestario_mes"].str.strip().str.zfill(2) + "-01", errors="coerce")
    df = df.dropna(subset=["fecha"])
    df["servicio_id"] = pd.to_numeric(df["servicio_id"], errors="coerce").astype("Int64")
    df = df.groupby(["fecha", "servicio_id"], as_index=False).agg(
        servicio_desc=("servicio_desc", "last"), devengado=("credito_devengado", "sum"))
    return df[["fecha", "servicio_id", "servicio_desc", "devengado"]].sort_values(["servicio_id", "fecha"])


def _actualizar_anio(anio: int) -> None:
    destino = CARPETA / f"credito_{anio}.csv"
    hoy = pd.Timestamp.today()
    if destino.exists() and anio < hoy.year - 1:
        return
    time.sleep(15)  # el servidor corta la conexión si se le piden muchos archivos seguidos
    try:
        r = pedir(URL.format(a=anio))
    except RuntimeError:
        if destino.exists():
            return  # se usa lo guardado
        raise
    z = zipfile.ZipFile(io.BytesIO(r.content))
    nombre = next(n for n in z.namelist() if n.endswith(".csv"))
    with z.open(nombre) as f:
        df = resumir(io.TextIOWrapper(f, encoding="utf-8-sig"))
    CARPETA.mkdir(parents=True, exist_ok=True)
    df.to_csv(destino, index=False, date_format="%Y-%m-%d")


@lru_cache(maxsize=1)
def tabla() -> pd.DataFrame:
    errores = []
    for anio in range(DESDE, pd.Timestamp.today().year + 1):
        try:
            _actualizar_anio(anio)
        except Exception as e:  # un año que no se pudo bajar no frena al resto
            errores.append(f"{anio}: {e}")
    tabla.errores = errores
    archivos = sorted(CARPETA.glob("credito_*.csv"))
    if not archivos:
        raise RuntimeError("Sin datos de ejecución presupuestaria: " + "; ".join(errores[:3]))
    return pd.concat(pd.read_csv(a, parse_dates=["fecha"]) for a in archivos)


def extraer(definicion: dict) -> pd.Series:
    ids = definicion["id"] if isinstance(definicion["id"], list) else [definicion["id"]]
    df = tabla()
    df = df[df["servicio_id"].isin([int(i) for i in ids])]
    if df.empty:
        raise RuntimeError(f"Sin ejecución para los servicios {ids}")
    s = df.groupby("fecha")["devengado"].sum().sort_index()
    # Rellena con 0 los meses sin gasto dentro del período del organismo
    idx = pd.date_range(s.index.min(), s.index.max(), freq="MS")
    return s.reindex(idx, fill_value=0.0).astype(float)
