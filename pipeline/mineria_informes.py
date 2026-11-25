"""Actualiza las barras de minería (data/categorias/mineria_*.csv) con los informes mensuales en PDF de la
Secretaría de Minería que se publican en argentina.gob.ar:

- Empleo minero en Argentina: puestos de trabajo por provincia y por rubro.
- Origen provincial de las exportaciones mineras: exportaciones acumuladas del año por provincia y peso de la
  minería en las exportaciones de cada provincia.

Se busca el informe más reciente (mes actual hacia atrás). Si un informe no se puede leer completo, se conserva
el archivo anterior y se deja una alerta: nunca se escribe una tabla a medias.
"""
from __future__ import annotations

import csv
import io
import re
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from .fuentes.archivos import CABECERAS, MESES_NUM, TIMEOUT

CATEGORIAS = Path(__file__).resolve().parents[1] / "data" / "categorias"
PDF = "https://www.argentina.gob.ar/sites/default/files/{AAAA}.{MM}_{nombre}.pdf"
NOMBRES_EMPLEO = ["empleo_minero_en_argentina"]
NOMBRES_EXPO = ["origen_provincial_de_las_exportaciones_mineras", "origen_provincias_de_las_exportaciones_mineras"]
NOMBRE_PROV = {"Cordoba": "Córdoba", "Resto": "Resto del país", "Rio Negro": "Río Negro", "Tucuman": "Tucumán", "Neuquen": "Neuquén"}
RUBROS = [  # (nombre en el sitio, expresión en el texto del informe)
    ("Metalíferos (oro, plata, cobre)", r"([\d.]+) puestos de trabajo vinculados a metal[ií]feros"),
    ("Servicios mineros", r"servicios y actividades relacionadas con la miner[ií]a, que explic[oó] un total de ([\d.]+) puestos"),
    ("Litio", r"litio con ([\d.]+) puestos"),
    ("Rocas de aplicación", r"rocas de aplicaci[oó]n con ([\d.]+) puestos"),
    ("Minerales no metalíferos", r"minerales no metal[ií]feros con ([\d.]+) puestos"),
    ("Minerales combustibles", r"minerales combustibles con ([\d.]+) puestos"),
    ("Otros minerales", r"minerales no clasificados previamente con ([\d.]+) puestos"),
]


def _num(x: str) -> float:
    return float(x.replace(".", "").replace(",", "."))


def _texto(contenido: bytes) -> list[str]:
    from pypdf import PdfReader
    return [p.extract_text() or "" for p in PdfReader(io.BytesIO(contenido)).pages]


def buscar_informe(nombres: list[str], meses: int = 6) -> tuple[str, bytes] | None:
    """El PDF más reciente, probando desde el mes actual hacia atrás."""
    hoy = pd.Timestamp(date.today()).replace(day=1)
    for k in range(meses):
        pub = hoy - pd.DateOffset(months=k)
        for nombre in nombres:
            url = PDF.format(AAAA=pub.year, MM=f"{pub.month:02d}", nombre=nombre)
            try:
                r = requests.get(url, headers=CABECERAS, timeout=TIMEOUT)
            except requests.RequestException:
                continue
            if r.status_code == 200 and r.content[:4] == b"%PDF":
                return url, r.content
    return None


def leer_empleo(paginas: list[str]) -> dict:
    """Mes de referencia, puestos por provincia (gráfico de barras de la página de provincias) y por rubro."""
    t = re.sub(r"\s+", " ", " ".join(paginas))
    m = re.search(r"Durante (?:el mes de )?(\w+) de (\d{4}),? el empleo minero en Argentina alcanz[oó] los ([\d.]+)", t)
    if not m or m.group(1).lower() not in MESES_NUM:
        raise ValueError("empleo minero: no se encontró el mes de referencia")
    fecha = pd.Timestamp(int(m.group(2)), MESES_NUM[m.group(1).lower()], 1)
    total = _num(m.group(3))
    # Provincias: en la página del gráfico, los valores van antes del eje "0 2.000 4.000 ..." y los nombres
    # después, en el mismo orden.
    pag = next((p for p in paginas if "Empleo minero por provincia" in p), "")
    lineas = [l.strip() for l in pag.splitlines() if l.strip()]
    eje = next((i for i, l in enumerate(lineas) if re.fullmatch(r"0( [\d.]+){3,}", l)), None)
    if eje is None:
        raise ValueError("empleo minero: no se encontró el gráfico por provincia")
    valores = []
    for l in reversed(lineas[:eje]):
        if re.fullmatch(r"[\d.]+", l):
            valores.insert(0, _num(l))
        else:
            break
    nombres = []
    for l in lineas[eje + 1:]:
        if l.startswith("Metal") or l.startswith("Fuente"):
            break
        nombres.append(NOMBRE_PROV.get(l, l))
    if not valores or len(valores) != len(nombres) or abs(sum(valores) - total) > 0.02 * total:
        raise ValueError(f"empleo minero: provincias sin cuadrar ({len(valores)} valores, {len(nombres)} nombres)")
    provincias = dict(zip(nombres, valores))
    rubros = {}
    for nombre, rx in RUBROS:
        r = re.search(rx, t, flags=re.I)
        if not r:
            raise ValueError(f"empleo minero: no se encontró el rubro {nombre}")
        rubros[nombre] = _num(r.group(1))
    if abs(sum(rubros.values()) - total) > 0.02 * total:
        raise ValueError("empleo minero: los rubros no suman el total")
    return {"fecha": fecha, "provincias": provincias, "rubros": rubros}


def leer_exportaciones(paginas: list[str]) -> dict:
    """Mes de referencia, exportaciones mineras acumuladas del año por provincia (millones de US$) y peso de la
    minería en las exportaciones de cada provincia (%, acumulado del año)."""
    t = re.sub(r"\s+", " ", " ".join(paginas))
    m = re.search(r"(?:Durante el mes de|En) (\w+) de (\d{4}),? el sector minero realizó exportaciones", t)
    if not m or m.group(1).lower() not in MESES_NUM:
        raise ValueError("exportaciones mineras: no se encontró el mes de referencia")
    fecha = pd.Timestamp(int(m.group(2)), MESES_NUM[m.group(1).lower()], 1)
    peso = {}
    p = re.search(r"en el acumulado [^:]*?porcentajes de ventas al exterior: (.+?)\.", t)
    if p:
        for prov, v in re.findall(r"([A-ZÁÉÍÓÚ][\wáéíóúñ ]+?) ([\d,]+)%", p.group(1)):
            peso[prov.replace(" y", "").strip()] = _num(v)
    # Exportaciones acumuladas: etiquetas del gráfico de torta ("Jujuy USD 1.467 (19,7%)"). Catamarca y Salta
    # no tienen etiqueta propia: salen del total de las provincias del NOA menos Jujuy.
    expo = {}
    for prov, v in re.findall(r"(?m)^([A-ZÁÉÍÓÚ][\wáéíóúñ ]+?) USD\s*([\d.]+)\s*\(", "\n".join(paginas)):
        expo[prov.strip()] = _num(v)
    noa = re.search(r"exportaciones mineras de estas provincias suman USD ([\d.,]+) millones", t)
    if noa and "Jujuy" in expo and "Catamarca" not in expo and "Salta" not in expo:
        expo["Catamarca y Salta"] = _num(noa.group(1)) - expo["Jujuy"]
    tot = re.search(r"las exportaciones mineras totalizaron USD ([\d.,]+) millones", t)
    if tot and expo and _num(tot.group(1)) - sum(expo.values()) > 0:
        expo["Resto del país"] = round(_num(tot.group(1)) - sum(expo.values()), 1)
    if len(expo) < 3 or len(peso) < 3:
        raise ValueError(f"exportaciones mineras: datos incompletos ({len(expo)} provincias, {len(peso)} pesos)")
    return {"fecha": fecha, "expo": expo, "peso": peso}


def _escribir(nombre: str, filas: dict, url: str, fecha: pd.Timestamp) -> None:
    with open(CATEGORIAS / f"{nombre}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(["categoria", "valor", "fuente_url", "fecha"])
        for k, v in filas.items():
            w.writerow([k, int(v) if float(v).is_integer() else v, url, fecha.strftime("%Y-%m-%d")])


def actualizar() -> list[str]:
    """Baja los informes y reescribe las barras. Devuelve alertas."""
    alertas = []
    inf = buscar_informe(NOMBRES_EMPLEO)
    if not inf:
        alertas.append("minería: no se encontró el informe de empleo minero de los últimos meses; se conservan las barras")
    else:
        try:
            d = leer_empleo(_texto(inf[1]))
            resto = d["provincias"].pop("Resto del país", None)
            prov = dict(sorted(d["provincias"].items(), key=lambda x: -x[1]))
            if resto is not None:
                prov["Resto del país"] = resto
            _escribir("mineria_empleo_provincias", prov, inf[0], d["fecha"])
            _escribir("mineria_empleo_rubros", dict(sorted(d["rubros"].items(), key=lambda x: -x[1])), inf[0], d["fecha"])
        except Exception as e:
            alertas.append(f"minería: no se pudo leer el informe de empleo ({e}); se conservan las barras")
    inf = buscar_informe(NOMBRES_EXPO)
    if not inf:
        alertas.append("minería: no se encontró el informe de exportaciones por provincia de los últimos meses; se conservan las barras")
    else:
        try:
            d = leer_exportaciones(_texto(inf[1]))
            resto = d["expo"].pop("Resto del país", None)
            expo = dict(sorted(d["expo"].items(), key=lambda x: -x[1]))
            if resto is not None:
                expo["Resto del país"] = resto
            _escribir("mineria_expo_provincias", expo, inf[0], d["fecha"])
            _escribir("mineria_peso_provincias", dict(sorted(d["peso"].items(), key=lambda x: -x[1])), inf[0], d["fecha"])
        except Exception as e:
            alertas.append(f"minería: no se pudo leer el informe de exportaciones ({e}); se conservan las barras")
    return alertas
