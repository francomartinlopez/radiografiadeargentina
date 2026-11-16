"""Cambios de empleo e ingresos con el panel de la Encuesta Permanente de Hogares (INDEC).

La EPH entrevista a cada hogar dos trimestres seguidos, lo deja dos y vuelve dos más: la mitad de
las personas de un trimestre se vuelve a encontrar un año después. Acá se las sigue (vivienda,
hogar y número de miembro, con el mismo sexo y hasta 2 años más de edad) para ver qué pasó con
quienes tenían un empleo privado registrado y con quienes trabajaban en negro o por cuenta propia,
y cuánto cambió su ingreso real.

El resultado se guarda en data/crudos/eph_transiciones.json. Solo se recalcula (bajando todos los
microdatos desde 2016) cuando INDEC publica un trimestre nuevo.
"""
from __future__ import annotations

import io
import json
import zipfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
CACHE = RAIZ / "data" / "crudos" / "eph_transiciones.json"
CRUDOS = RAIZ / "data" / "crudos"
DESDE = (2016, 2)        # nuevo diseño de la muestra y ponderador de ingresos con imputación
MANDATO = (2024, 1)      # "Último mandato": comparaciones que empiezan desde el 1.er trimestre de 2024
MIN_CASOS = 100          # menos casos: se marca con ⚠
COLUMNAS = ["CODUSU", "NRO_HOGAR", "COMPONENTE", "ANO4", "TRIMESTRE", "CH04", "CH06", "ESTADO", "CAT_OCUP",
            "PP04A", "PP07H", "P21", "PONDIIO", "PONDERA", "P47T", "PONDII"]

# destinos (para quienes tenían empleo formal): código, nombre, ingreso total en lugar de laboral
SALIDAS = [("F", "Siguió formal", False), ("PUB", "Pasó al sector público", False),
           ("NR", "Pasó a empleo en negro", False), ("CP", "Pasó a cuenta propia", False),
           ("DES", "Quedó desocupado", True), ("INA", "Salió del mercado laboral", True)]
# entradas: origen, destino, nombre
ENTRADAS = [("NR", "F", "De en negro a formal"), ("NR", "NR", "Siguió en negro"),
            ("CP", "F", "De cuenta propia a formal"), ("CP", "CP", "Siguió por cuenta propia")]
SITUACIONES = [("NR", "Empleo en negro"), ("PUB", "Sector público"), ("CP", "Cuenta propia"),
               ("DES", "Desocupación"), ("INA", "Inactividad"), ("OTRO", "Patrón u otro")]


def leer_trimestre(contenido: bytes) -> pd.DataFrame:
    z = zipfile.ZipFile(io.BytesIO(contenido))
    nombres = [n for n in z.namelist() if ("individual" in n.lower() or "personas" in n.lower()) and n.lower().endswith(".txt")]
    if not nombres:
        raise ValueError(f"sin archivo de personas en {z.namelist()[:6]}")
    df = pd.read_csv(z.open(nombres[0]), sep=";", decimal=",", low_memory=False, encoding="latin-1",
                     usecols=lambda c: c.upper() in COLUMNAS)
    df.columns = [c.upper() for c in df.columns]
    for c in COLUMNAS:
        if c not in df.columns:
            df[c] = np.nan
    df = df[COLUMNAS].copy()
    for c in COLUMNAS[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["CODUSU"] = df["CODUSU"].astype(str).str.strip()
    return df


def situacion(df: pd.DataFrame) -> np.ndarray:
    """F: asalariado privado registrado · PUB: asalariado público · NR: asalariado privado sin descuento
    jubilatorio · CP: cuenta propia · OTRO: patrón o familiar · DES: desocupado · INA: inactivo."""
    e, c, s, r = df.ESTADO, df.CAT_OCUP, df.PP04A, df.PP07H
    ocup, asal = e == 1, (e == 1) & (c == 3)
    return np.select([asal & (s == 1), asal & (r == 1), asal, ocup & (c == 2), ocup, e == 2, e == 3],
                     ["PUB", "F", "NR", "CP", "OTRO", "DES", "INA"], "NA")


def emparejar(df: pd.DataFrame, ipc: pd.Series) -> pd.DataFrame:
    """Cada persona con ella misma 4 trimestres después. Ingresos en moneda constante."""
    df = df.copy()
    df["cat"] = situacion(df)
    df["q"] = (df.ANO4 * 4 + df.TRIMESTRE - 1).astype(int)
    meses = pd.to_datetime({"year": df.ANO4.astype(int), "month": 3 * df.TRIMESTRE.astype(int) - 1, "day": 1})
    defl = ipc.reindex(meses).values
    df["y"] = np.where(df.P21 > 0, df.P21 / defl, np.nan)                 # ingreso de la ocupación principal
    df["yt"] = np.where(df.P47T >= 0, df.P47T / defl, np.nan)             # ingreso total individual
    k = ["CODUSU", "NRO_HOGAR", "COMPONENTE"]
    despues = df[k + ["q", "CH04", "CH06", "cat", "y", "yt"]].copy()
    despues["q"] -= 4
    m = df.merge(despues, on=k + ["q"], suffixes=("", "_1"))
    m = m[(m.CH04 == m.CH04_1) & (m.CH06_1 - m.CH06).between(0, 2)]
    return m.drop_duplicates(k + ["q"], keep=False)


def _mediana(x: np.ndarray, w: np.ndarray) -> float:
    o = np.argsort(x)
    x, c = x[o], np.cumsum(w[o])
    return float(x[np.searchsorted(c, c[-1] / 2)])


def cambio(g: pd.DataFrame, total: bool = False) -> tuple[int, float | None, float | None]:
    """(casos, % de cambio del ingreso promedio, % de cambio de la mediana). Con total=True se usa el
    ingreso total individual en ambos momentos (para quienes quedan sin trabajo)."""
    a, b, w = (g.yt, g.yt_1, g.PONDII) if total else (g.y, g.y_1, g.PONDIIO)
    ok = (a > 0) & (b >= 0 if total else b > 0) & (w > 0)
    a, b, w = a[ok].values, b[ok].values, w[ok].values
    if len(a) < 5:
        return len(a), None, None
    prom = (np.average(b, weights=w) / np.average(a, weights=w) - 1) * 100
    med = (_mediana(b, w) / _mediana(a, w) - 1) * 100
    return len(a), round(float(prom), 1), round(float(med), 1)


def _fecha(q: int) -> str:
    a, t = divmod(int(q), 4)
    return f"{a}-{3 * (t + 1) - 1:02d}-01"


def resultados(m: pd.DataFrame) -> dict:
    qs = sorted(m.q.unique())
    finales = [q for q in qs if q >= qs[0] + 3]       # cada punto junta 4 trimestres de primera entrevista
    ventana = lambda q: m[(m.q > q - 4) & (m.q <= q)]
    mandato = MANDATO[0] * 4 + MANDATO[1] - 1
    variantes = [("promedio", 1), ("mediana", 2)]

    def barras(grupos):
        out = []
        for per, d in (("completo", m), ("mandato", m[m.q >= mandato])):
            for origen, destino, nombre, total in grupos:
                n, *vals = cambio(d[(d.cat == origen) & (d.cat_1 == destino)], total)
                for (var, _), v in zip(variantes, vals):
                    if v is not None:
                        out.append({"categoria": nombre, "valor": v, "periodo": per, "variante": var, "casos": n,
                                    **({"tramo": "pocos_casos"} if n < MIN_CASOS else {})})
        return out

    def lineas(grupos, gris=None):
        series = []
        for var, i in variantes:
            for origen, destino, nombre, total in grupos:
                puntos = []
                for q in finales:
                    d = ventana(q)
                    r = cambio(d[(d.cat == origen) & (d.cat_1 == destino)], total)
                    if r[i] is not None:
                        puntos.append([_fecha(q), r[i]] + (["pocos_casos"] if r[0] < MIN_CASOS else []))
                if puntos:
                    series.append({"nombre": nombre, "serie": f"{nombre} ({var})", "variante": var, "puntos": puntos,
                                   **({"color": "gris"} if nombre == gris else {})})
        return series

    def composicion(salen: bool):
        S = {n: [] for _, n in SITUACIONES}
        for q in finales:
            d = ventana(q)
            d = d[(d.cat != "NA") & (d.cat_1 != "NA")]
            d = d[(d.cat == "F") & (d.cat_1 != "F")] if salen else d[(d.cat_1 == "F") & (d.cat != "F")]
            s = d.groupby("cat_1" if salen else "cat").PONDERA.sum()
            s = s / s.sum() * 100
            for c, n in SITUACIONES:
                S[n].append([_fecha(q), round(float(s.get(c, 0)), 1)])
        return [{"nombre": n, "serie": n, "puntos": p} for n, p in S.items()]

    salida, entrada = [], []
    for q in finales:
        d = ventana(q)
        d = d[d.cat_1 != "NA"]
        f = d[d.cat == "F"]
        salida.append([_fecha(q), round(float((f.cat_1.isin(["NR", "CP"]) * f.PONDERA).sum() / f.PONDERA.sum() * 100), 1)])
        i = d[d.cat.isin(["NR", "CP"])]
        entrada.append([_fecha(q), round(float(((i.cat_1 == "F") * i.PONDERA).sum() / i.PONDERA.sum() * 100), 1)])

    sal = [("F", d, n, t) for d, n, t in SALIDAS]
    ent = [(o, d, n, False) for o, d, n in ENTRADAS]
    return {
        "salida_ingreso": barras(sal),
        "salida_ingreso_anual": lineas(sal, gris="Siguió formal"),
        "salida_destino": composicion(True),
        "entrada_ingreso": barras(ent),
        "entrada_ingreso_anual": lineas(ent),
        "entrada_origen": composicion(False),
        "entradas_salidas": [{"nombre": "Salida: de formal a en negro o cuenta propia", "serie": "salida", "puntos": salida},
                             {"nombre": "Entrada: de en negro o cuenta propia a formal", "serie": "entrada", "puntos": entrada}],
        "desde_barras": _fecha(qs[0]), "desde": _fecha(finales[0]), "ultimo": _fecha(finales[-1]),
        "casos": int(len(m)),
    }


def ipc_empalmado() -> pd.Series:
    """IPC nacional (desde dic-2016) y, antes, el de la Ciudad de Buenos Aires llevado a la misma base."""
    leer = lambda n: pd.read_csv(CRUDOS / f"{n}.csv", parse_dates=["fecha"]).set_index("fecha")["valor"].sort_index()
    nac, caba = leer("ipc_nacional"), leer("ipc_caba_2012")
    base = nac.index[0]
    return pd.concat([caba[caba.index < base] * nac.iloc[0] / caba.loc[base], nac])


def _trimestres(hasta: tuple[int, int]) -> list[tuple[int, int]]:
    out, (a, t) = [], DESDE
    while (a, t) <= hasta:
        out.append((a, t))
        a, t = (a + 1, 1) if t == 4 else (a, t + 1)
    return out


def _siguiente(a: int, t: int) -> tuple[int, int]:
    return (a + 1, 1) if t == 4 else (a, t + 1)


@lru_cache(maxsize=None)
def datos(descargar: bool = True) -> dict:
    """Resultados guardados; si hay un trimestre nuevo en INDEC, se recalcula todo."""
    from .archivos import _eph_zip
    previo = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else None
    if not descargar:
        if previo is None:
            raise ValueError("EPH panel: no hay resultados guardados (correr sin --offline)")
        return previo
    if previo:
        a, t = map(int, previo["ultimo_trimestre"].split("-T"))
        nuevo = _eph_zip(*_siguiente(a, t))
        if nuevo is None:
            return previo
    from datetime import date
    hoy = date.today()
    tablas, ultimo = [], None
    for a, t in _trimestres((hoy.year, (hoy.month - 1) // 3 + 1)):
        contenido = _eph_zip(a, t)
        if contenido is None:
            continue
        tablas.append(leer_trimestre(contenido))
        ultimo = (a, t)
    if not tablas:
        if previo:
            return previo
        raise ValueError("EPH panel: no se pudo bajar ningún trimestre")
    m = emparejar(pd.concat(tablas, ignore_index=True), ipc_empalmado())
    res = resultados(m)
    res["ultimo_trimestre"] = f"{ultimo[0]}-T{ultimo[1]}"
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    return res
