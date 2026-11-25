"""Arma sitio/public/datos-informe.json para la web de informes de Plexum (especificación v1.2).

Toma el último valor de cada indicador listado en pipeline/datos_informe.yaml de los gráficos que el sitio
acaba de publicar. No calcula datos nuevos: solo el último valor, su fecha real y, si existe, la comparación
con un período anterior de la misma serie. Lo que no se pudo publicar va a "faltantes".
"""
from __future__ import annotations

import calendar
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import yaml

RAIZ = Path(__file__).resolve().parents[1]
CONFIG = RAIZ / "pipeline" / "datos_informe.yaml"
SALIDA = RAIZ / "sitio" / "public" / "datos-informe.json"
PROVINCIAS = ["Buenos Aires", "CABA", "Catamarca", "Chaco", "Chubut", "Córdoba", "Corrientes", "Entre Ríos", "Formosa",
              "Jujuy", "La Pampa", "La Rioja", "Mendoza", "Misiones", "Neuquén", "Río Negro", "Salta", "San Juan",
              "San Luis", "Santa Cruz", "Santa Fe", "Santiago del Estero", "Tierra del Fuego", "Tucumán"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]
PASOS = {"M": 1, "T": 3, "S": 6, "A": 12}  # meses entre dos datos de la serie


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def alcance(provincia: str = "") -> dict:
    return {"nivel": "provincia" if provincia else "nacional", "provincia": provincia, "localidad": "", "pais": "Argentina"}


def fin_de_periodo(inicio: pd.Timestamp, frecuencia: str) -> pd.Timestamp:
    """Los puntos se fechan al inicio del período; fecha_dato es el último día del período."""
    fin = inicio + pd.DateOffset(months=PASOS.get(frecuencia, 1) - 1)
    return fin.replace(day=calendar.monthrange(fin.year, fin.month)[1])


def periodo(inicio: pd.Timestamp, frecuencia: str) -> str | None:
    if frecuencia == "M":
        return inicio.strftime("%Y-%m")
    if frecuencia == "T":
        return f"{inicio.year}-T{(inicio.month - 1) // 3 + 1}"
    return None


def nombre_periodo(f: pd.Timestamp, frecuencia: str) -> str:
    if frecuencia == "M":
        return f"{MESES[f.month - 1]} de {f.year}"
    if frecuencia == "T":
        return f"{(f.month - 1) // 3 + 1}.º trimestre de {f.year}"
    if frecuencia == "S":
        return f"{'1.er' if f.month <= 6 else '2.º'} semestre de {f.year}"
    return str(f.year)


FRECUENCIAS = {"M": "mensual", "T": "trimestral", "S": "semestral", "A": "anual"}
LARGO_SERIE = {"M": 25, "T": 9, "S": 5, "A": 6}  # puntos que se publican en "serie" (versión 1.3)


def tipo_valor(e: dict) -> str:
    return "tasa" if e.get("variacion", "").endswith("_pp") or e["unidad"].startswith("%") else "nivel"


def serie_publicada(puntos: list, frecuencia: str) -> list[dict]:
    """Últimos valores de la serie, del más viejo al más nuevo, fechados al fin de cada período."""
    pts = [p for p in puntos if p[1] is not None][-LARGO_SERIE.get(frecuencia, 25):]
    return [{"fecha": fin_de_periodo(pd.Timestamp(f), frecuencia).strftime("%Y-%m-%d"), "valor": redondear(p[1])} for p in pts for f in [p[0]]]


def comparar(e: dict, serie: list[dict], frecuencia: str) -> list[str]:
    """Interanual si hay al menos un año de historia; mensual solo en series mensuales que la admiten."""
    if len(serie) < 2:
        return []
    anio = pd.Timestamp(serie[-1]["fecha"]) - pd.DateOffset(years=1)
    con_anio = any(abs((pd.Timestamp(x["fecha"]) - anio).days) <= 3 for x in serie)
    salida = []
    if frecuencia == "M" and not e.get("sin_mensual"):
        salida.append("mensual")
    if con_anio:
        salida.append("interanual")
    return salida


def redondear(v: float) -> float | int:
    a = abs(v)
    r = round(v, 0 if a >= 10000 else 1 if a >= 100 else 2)
    return int(r) if float(r).is_integer() else r


def variacion(puntos: list, frecuencia: str, tipo: str | None) -> dict | None:
    if not tipo or len(puntos) < 2:
        return None
    s = pd.Series({pd.Timestamp(p[0]): p[1] for p in puntos}).sort_index()
    ultimo, valor = s.index[-1], s.iloc[-1]
    if tipo == "anterior_pp":
        previo = ultimo - pd.DateOffset(months=PASOS.get(frecuencia, 1))
    else:
        previo = ultimo - pd.DateOffset(years=1)
    if previo not in s.index or pd.isna(s[previo]):
        return None
    contra = ("período anterior" if tipo == "anterior_pp" else "mismo período del año anterior") + \
        f" ({nombre_periodo(previo, frecuencia)})"
    if tipo == "interanual":
        if s[previo] == 0:
            return None
        return {"valor": round((valor / s[previo] - 1) * 100, 1), "unidad": "%", "contra": contra}
    return {"valor": round(valor - s[previo], 1), "unidad": "p. p.", "contra": contra}


def registro(e: dict, cfg: dict, g: dict, valor, fecha: pd.Timestamp, frecuencia: str, var: dict | None,
             provincia: str = "", nombre: str | None = None, ident: str | None = None, url_fuente: str = "",
             puntos: list | None = None) -> dict:
    r = {"id": ident or e["id"], "nombre": nombre or e["nombre"], "valor": valor, "unidad": e["unidad"]}
    if var:
        r["variacion"] = var
    serie = serie_publicada(puntos, frecuencia) if puntos else []
    r["tipo_valor"] = tipo_valor(e)
    r["frecuencia"] = e.get("frecuencia") or FRECUENCIAS.get(frecuencia, "mensual")
    r["comparar"] = comparar(e, serie, frecuencia)
    if len(serie) >= 2:
        r["serie"] = serie
    r["fecha_dato"] = fin_de_periodo(fecha, frecuencia).strftime("%Y-%m-%d")
    p = periodo(fecha, frecuencia)
    if p:
        r["periodo"] = p
    r.update({"fuente_original": e["fuente"], "eje": cfg["eje"], "alcance": alcance(provincia),
              "rubros": e.get("rubros", []), "subrubros": e.get("subrubros", []), "exposicion": e.get("exposicion", []),
              "url": f"{cfg['sitio']}/#{g['id']}"})
    return r


def generar(graficos: list[dict], previo: dict | None = None) -> dict:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    por_id = {g["id"]: g for g in graficos}
    ipc = por_id.get("inflacion_minorista", {}).get("ultimo")
    base_ipc = nombre_periodo(pd.Timestamp(ipc), "M") if ipc else "hoy"
    anteriores = {i["id"]: i["fecha_dato"] for i in (previo or {}).get("indicadores", [])}
    anteriores.update({f["id"]: f.get("ultimo_dato") for f in (previo or {}).get("faltantes", []) if f.get("ultimo_dato")})
    indicadores, faltantes = [], []

    def falta(ident: str, nombre: str, motivo: str):
        faltantes.append({"id": ident, "nombre": nombre, "motivo": motivo, "ultimo_dato": anteriores.get(ident)})

    for e in cfg["indicadores"]:
        e = {**e, "unidad": e["unidad"].replace("{base_ipc}", base_ipc)}
        g = por_id.get(e["grafico"])
        if e.get("provincias"):
            if not g:
                falta(e["id"], e["nombre"], "El gráfico no se pudo armar en esta actualización")
                continue
            vistos = set()
            for s in g.get("series", []):
                prov = s["nombre"]
                if prov not in PROVINCIAS or prov in vistos:
                    continue
                vistos.add(prov)
                ident = f"{e['id']}-{slug(prov)}"
                nombre = f"{e['nombre']} en {prov}" + (e.get("nota_buenos_aires", "") if prov == "Buenos Aires" else "")
                pts = [p for p in s["puntos"] if p[1] is not None]
                if not pts:
                    falta(ident, nombre, "La fuente no tiene datos de la provincia")
                    continue
                f = pd.Timestamp(pts[-1][0])
                indicadores.append(registro(e, cfg, g, redondear(pts[-1][1]), f, g.get("frecuencia", "M"),
                                            variacion(pts, g.get("frecuencia", "M"), e.get("variacion")),
                                            provincia=prov, nombre=nombre, ident=ident, puntos=pts))
        elif e.get("categorias") is not None:
            cats = {c["categoria"]: c for c in (g or {}).get("categorias", [])}
            for prov in e["categorias"]:
                ident = f"{e['id']}-{slug(prov)}"
                nombre = f"{e['nombre']} en {prov}"
                c = cats.get(prov)
                if not c or not c.get("fecha"):
                    falta(ident, nombre, "La provincia no figura en el último informe de la fuente")
                    continue
                indicadores.append(registro(e, cfg, g, redondear(c["valor"]), pd.Timestamp(c["fecha"]), "M", None,
                                            provincia=prov, nombre=nombre, ident=ident, url_fuente=c.get("fuente_url", "")))
        elif e.get("categoria"):
            c = next((c for c in (g or {}).get("categorias", []) if c["categoria"] == e["categoria"]), None)
            if not c or not c.get("fecha"):
                falta(e["id"], e["nombre"], "El dato no está en esta actualización")
                continue
            indicadores.append(registro(e, cfg, g, redondear(c["valor"]), pd.Timestamp(c["fecha"]), "M", None,
                                        url_fuente=c.get("fuente_url", "")))
        else:
            s = next((s for s in (g or {}).get("series", []) if s["serie"] == e["serie"]), None)
            pts = [p for p in (s or {}).get("puntos", []) if p[1] is not None]
            if not pts:
                falta(e["id"], e["nombre"], "La fuente no respondió o cambió el formato en esta actualización")
                continue
            frec = g.get("frecuencia", "M")
            indicadores.append(registro(e, cfg, g, redondear(pts[-1][1]), pd.Timestamp(pts[-1][0]), frec,
                                        variacion(pts, frec, e.get("variacion")), puntos=pts))

    # Grupos por provincia (base de los mapas): mismo id, nombre y unidad, y la misma fecha_dato. Si una provincia
    # tiene un dato más viejo que el resto, queda afuera del grupo (sigue como indicador suelto).
    for e in cfg["indicadores"]:
        if not (e.get("provincias") or e.get("categorias")):
            continue
        miembros = [i for i in indicadores if i["id"].startswith(e["id"] + "-") and i["alcance"]["nivel"] == "provincia"
                    and i["id"][len(e["id"]) + 1:] in {slug(p) for p in PROVINCIAS}]
        if not miembros:
            continue
        fecha = max(i["fecha_dato"] for i in miembros)
        al_dia = [i for i in miembros if i["fecha_dato"] == fecha]
        if len(al_dia) >= 3:
            for i in al_dia:
                i["grupo"] = {"id": f"{e['id']}-por-provincia", "nombre": e["nombre"], "dimension": "provincia",
                              "clave": i["alcance"]["provincia"]}
    return {
        "web": cfg["web"],
        "version": cfg["version"],
        "generado": datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).isoformat(timespec="seconds"),
        "indicadores": indicadores,
        "novedades": [],
        "agenda": [],
        "faltantes": faltantes,
    }


def escribir(graficos: list[dict]) -> list[str]:
    """Escribe el archivo y devuelve alertas (indicadores faltantes)."""
    previo = None
    if SALIDA.exists():
        try:
            previo = json.loads(SALIDA.read_text(encoding="utf-8"))
        except ValueError:
            previo = None
    datos = generar(graficos, previo)
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    return [f"datos-informe: falta {f['nombre']} ({f['motivo']})" for f in datos["faltantes"]]
