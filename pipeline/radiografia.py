"""Construye los gráficos de Radiografía de la Argentina.

Usa la base de series de indicadores.yaml (descarga, empalmes y cálculos, igual que Datos de
Argentina) y el catálogo graficos.yaml. Por cada gráfico escribe un JSON con las series en nivel
(moneda constante si corresponde), los tramos estimados, las fuentes y el método. Las medidas
(variación, interanual, acumulado de 12 meses, base 100) las calcula el sitio a partir del nivel.

Uso:
    python -m pipeline.radiografia            # descarga solo las series que usan los gráficos
    python -m pipeline.radiografia --offline  # reprocesa con los datos ya bajados
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from . import construir, transformar

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "sitio" / "public" / "datos"
CATEGORIAS = RAIZ / "data" / "categorias"
DEFLACTORES = {"ARS": "ipc", "USD": "cpi_eeuu"}
PREVIO_MESES = 24  # meses antes del inicio que se publican para poder calcular interanual y acumulado
TIPOS = {"lineas", "areas", "barras", "barras_gobierno", "lineas_pais", "burbujas"}
NIVELES = {"primaria", "secundaria", "terciaria", "estimacion"}
TRAMOS = {"estimado", "interpolado", "proyectado"}


def cargar() -> tuple[dict, dict]:
    with open(RAIZ / "indicadores.yaml", encoding="utf-8") as f:
        base = yaml.safe_load(f)
    with open(RAIZ / "graficos.yaml", encoding="utf-8") as f:
        catalogo = yaml.safe_load(f)
    return base, catalogo


# ---------- Validación del catálogo ----------

def validar(catalogo: dict, base: dict) -> list[str]:
    """Errores de carga del catálogo: campos que faltan, valores no válidos o series inexistentes."""
    errores, ids = [], set()
    conocidas = set(base.get("series", {})) | set(base.get("empalmes", {})) | set(base.get("calculos", {}))
    for g in catalogo.get("graficos", []):
        gid = g.get("id", "?")
        if gid in ids:
            errores.append(f"{gid}: id repetido")
        ids.add(gid)
        for campo in ("tema", "titulo", "tipo", "fuentes"):
            if not g.get(campo):
                errores.append(f"{gid}: falta '{campo}'")
        if g.get("tipo") and g["tipo"] not in TIPOS:
            errores.append(f"{gid}: tipo '{g['tipo']}' no válido")
        if g.get("tema") and g["tema"] not in catalogo.get("temas", {}):
            errores.append(f"{gid}: tema {g['tema']} no existe")
        for fu in g.get("fuentes", []):
            if fu.get("nivel") not in NIVELES:
                errores.append(f"{gid}: fuente '{fu.get('nombre')}' sin nivel válido ({', '.join(sorted(NIVELES))})")
        for t in g.get("tramos", []):
            if t.get("tipo") not in TRAMOS:
                errores.append(f"{gid}: tramo con tipo '{t.get('tipo')}' no válido")
        if g.get("categorias"):
            if not (CATEGORIAS / f"{g['categorias']}.csv").exists():
                errores.append(f"{gid}: no existe data/categorias/{g['categorias']}.csv")
        else:
            for s in g.get("series", []):
                if s.get("serie") not in conocidas:
                    errores.append(f"{gid}: la serie '{s.get('serie')}' no está en indicadores.yaml")
            if not g.get("series"):
                errores.append(f"{gid}: sin series ni categorías")
    return errores


# ---------- Qué series hacen falta ----------

def dependencias(nombre: str, base: dict, vistas: set | None = None) -> set:
    """La serie y todo lo que necesita (tramos de empalmes, insumos de cálculos)."""
    vistas = set() if vistas is None else vistas
    if nombre in vistas:
        return vistas
    vistas.add(nombre)
    hijos = []
    if nombre in base.get("empalmes", {}):
        hijos = [t["serie"] for t in base["empalmes"][nombre]]
    elif nombre in base.get("calculos", {}):
        c = base["calculos"][nombre]
        for k, v in c.items():
            if k == "operacion":
                continue
            if isinstance(v, str):
                hijos.append(v)
            elif isinstance(v, list):
                hijos += [x for x in v if isinstance(x, str)]
            elif isinstance(v, dict) and k == "terminos":
                hijos += list(v)
    for h in hijos:
        if h in base.get("series", {}) or h in base.get("empalmes", {}) or h in base.get("calculos", {}):
            dependencias(h, base, vistas)
    return vistas


def subconfig(base: dict, catalogo: dict) -> dict:
    """indicadores.yaml reducido a las series que usan los gráficos (y sus deflactores)."""
    necesarias = set()
    for g in catalogo.get("graficos", []):
        for s in g.get("series", []):
            dependencias(s["serie"], base, necesarias)
        if g.get("moneda"):
            dependencias(DEFLACTORES[g["moneda"]], base, necesarias)
    calc_orden = [n for n in base.get("calculos", {}) if n in necesarias]
    return {
        **base,
        "series": {n: d for n, d in base["series"].items() if n in necesarias},
        "empalmes": {n: d for n, d in base.get("empalmes", {}).items() if n in necesarias},
        "calculos": {n: base["calculos"][n] for n in calc_orden},
    }


# ---------- Construcción de cada gráfico ----------

def _f(v) -> float | None:
    return round(float(v), 6) if v is not None and math.isfinite(float(v)) else None


def tramo_de(fecha: pd.Timestamp, tramos: list[dict], serie: str) -> str | None:
    for t in tramos:
        if t.get("serie") and t["serie"] != serie:
            continue
        desde = pd.Timestamp(str(t["desde"])) if t.get("desde") else pd.Timestamp.min
        hasta = pd.Timestamp(str(t["hasta"])) if t.get("hasta") else pd.Timestamp.max
        if desde <= fecha <= hasta:
            return t["tipo"]
    return None


def preparar_serie(s: pd.Series, g: dict, mensuales: dict) -> pd.Series | None:
    if s is None or s.empty:
        return None
    s = s.dropna().sort_index()
    if g.get("escala"):
        s = s * g["escala"]
    if g.get("moneda"):
        defl = mensuales.get(DEFLACTORES[g["moneda"]])
        if defl is None:
            return None
        s = transformar.a_moneda_constante(s, defl)
    s = s[s.index <= pd.Timestamp.today().normalize()]
    if g.get("desde"):
        desde = pd.Timestamp(str(g["desde"]))
        s = s[s.index >= desde - pd.DateOffset(months=PREVIO_MESES)]
    return None if s.empty else s


def gobierno_de(fecha: pd.Timestamp, gobiernos: list[dict]) -> str | None:
    """Gobierno a cargo a mitad del período (mes): el mes de una asunción se asigna a quien gobernó más días."""
    medio = fecha + pd.Timedelta(days=14)
    actual = None
    for g in gobiernos:
        if pd.Timestamp(g["desde"]) <= medio:
            actual = g["corto"]
    return actual


def agregar_por_gobierno(s: pd.Series, gobiernos: list[dict], modo: str = "promedio",
                         desde: pd.Timestamp | None = None) -> list[dict]:
    if desde is not None:
        s = s[s.index >= desde]
    grupos: dict[str, list[float]] = {}
    for f, v in s.dropna().items():
        g = gobierno_de(f, gobiernos)
        if g:
            grupos.setdefault(g, []).append(float(v))
    salida = []
    for gob in [x["corto"] for x in gobiernos]:
        vals = grupos.get(gob)
        if not vals:
            continue
        valor = {"promedio": sum(vals) / len(vals), "suma": sum(vals), "ultimo": vals[-1]}[modo]
        salida.append({"categoria": gob, "valor": _f(valor), "n": len(vals)})
    return salida


def leer_categorias(nombre: str) -> list[dict]:
    """data/categorias/<nombre>.csv: categoria, serie (opcional), valor, x, y, tamano, tramo, fuente_url."""
    df = pd.read_csv(CATEGORIAS / f"{nombre}.csv")
    filas = []
    for _, r in df.iterrows():
        fila = {"categoria": str(r["categoria"])}
        for c in ("serie", "tramo", "fuente_url"):
            if c in df.columns and pd.notna(r[c]):
                fila[c] = str(r[c])
        for c in ("valor", "x", "y", "tamano"):
            if c in df.columns and pd.notna(r[c]):
                fila[c] = _f(r[c])
        filas.append(fila)
    return filas


def construir_grafico(g: dict, mensuales: dict, catalogo: dict) -> tuple[dict | None, list[str]]:
    alertas = []
    gobiernos = catalogo["gobiernos"]
    tramos = g.get("tramos", [])
    salida = {
        k: g[k] for k in ("id", "tema", "titulo", "que_muestra", "original", "tipo", "unidad", "fuentes",
                          "metodo", "tramos", "estimacion", "sensible", "nota") if g.get(k) is not None
    }
    salida.update({
        "tema_nombre": catalogo["temas"][g["tema"]],
        "frecuencia": g.get("frecuencia", "M"),
        "tipo_valor": g.get("tipo_valor", "nivel"),
        "flujo": bool(g.get("flujo")),
        "medida_inicial": g.get("medida_inicial", "nivel"),
        "gobiernos": g.get("gobiernos", g["tipo"] in ("lineas", "areas")),
        "alerta": bool(g.get("estimacion") or tramos),
        "niveles_fuente": sorted({f["nivel"] for f in g.get("fuentes", [])}),
    })
    if g.get("categorias"):
        salida["categorias"] = leer_categorias(g["categorias"])
        salida["alerta"] = salida["alerta"] or any(c.get("tramo") for c in salida["categorias"])
        return salida, alertas

    series = []
    for sd in g["series"]:
        s = preparar_serie(mensuales.get(sd["serie"]), g, mensuales)
        if s is None:
            alertas.append(f"{g['id']}: sin datos para la serie {sd['serie']}")
            continue
        puntos = []
        for f, v in s.items():
            if not math.isfinite(v):
                continue
            t = tramo_de(f, tramos, sd["serie"])
            puntos.append([f.strftime("%Y-%m-%d"), _f(v)] + ([t] if t else []))
        series.append({"nombre": sd.get("nombre", sd["serie"]), "serie": sd["serie"],
                        **({"color": sd["color"]} if sd.get("color") else {}), "puntos": puntos})
    if not series:
        return None, alertas + [f"{g['id']}: sin datos, no se publica"]

    if g["tipo"] == "barras_gobierno":
        desde = pd.Timestamp(str(g["desde"])) if g.get("desde") else None
        cats = []
        for sd, ser in zip(g["series"], series):
            s = pd.Series({pd.Timestamp(p[0]): p[1] for p in ser["puntos"]})
            for c in agregar_por_gobierno(s, gobiernos, g.get("agregar_por_gobierno", "promedio"), desde):
                cats.append({**c, "serie": ser["nombre"]})
        salida["categorias"] = cats

    fechas = [p[0] for s in series for p in s["puntos"]]
    inicio = str(g["desde"]) if g.get("desde") else min(fechas)
    salida["desde"] = pd.Timestamp(inicio).strftime("%Y-%m-%d")
    salida["ultimo"] = max(fechas)
    salida["series"] = series
    return salida, alertas


def csv_de(graf: dict) -> pd.DataFrame:
    if graf.get("series"):
        filas = [{"serie": s["nombre"], "fecha": p[0], "valor": p[1], "tramo": p[2] if len(p) > 2 else "observado"}
                 for s in graf["series"] for p in s["puntos"] if p[0] >= graf["desde"]]
        return pd.DataFrame(filas, columns=["serie", "fecha", "valor", "tramo"])
    return pd.DataFrame(graf.get("categorias", []))


def escribir(graficos: list[dict], catalogo: dict, alertas: list[str]) -> None:
    carpeta = SALIDA / "graficos"
    carpeta.mkdir(parents=True, exist_ok=True)
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for g in graficos:
        g["actualizado"] = ahora
        (carpeta / f"{g['id']}.json").write_text(json.dumps(g, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        csv_de(g).to_csv(carpeta / f"{g['id']}.csv", index=False)
    indice = {
        "actualizado": ahora,
        "temas": [{"numero": n, "nombre": t} for n, t in catalogo["temas"].items()],
        "gobiernos": catalogo["gobiernos"],
        "base_ultimo_mandato": catalogo["parametros"]["base_ultimo_mandato"],
        "graficos": [{k: g.get(k) for k in ("id", "tema", "titulo", "tipo", "ultimo", "alerta", "niveles_fuente")}
                     for g in graficos],
    }
    (SALIDA / "radiografia.json").write_text(json.dumps(indice, ensure_ascii=False), encoding="utf-8")
    informe = [f"# Informe de actualización {ahora}", "", f"Gráficos publicados: {len(graficos)}", "",
               "## Alertas", ""] + ([f"- {a}" for a in alertas] or ["- Sin alertas"])
    (RAIZ / "data" / "informe.md").write_text("\n".join(informe) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="usar datos crudos guardados")
    args = parser.parse_args()
    base, catalogo = cargar()
    errores = validar(catalogo, base)
    if errores:
        raise SystemExit("Errores en graficos.yaml:\n- " + "\n- ".join(errores))
    sub = subconfig(base, catalogo)
    crudas, alertas = construir.descargar(sub, args.offline)
    mensuales, alertas_proc = construir.procesar(sub, crudas)
    alertas += alertas_proc
    graficos = []
    for g in catalogo["graficos"]:
        try:
            graf, al = construir_grafico(g, mensuales, catalogo)
        except Exception as e:  # un gráfico con problemas no frena el resto
            graf, al = None, [f"{g['id']}: error ({e}), no se publica"]
        alertas += al
        if graf:
            graficos.append(graf)
    escribir(graficos, catalogo, alertas)
    print(f"Listo: {len(graficos)} gráficos, {len(alertas)} alertas (ver data/informe.md)")


if __name__ == "__main__":
    main()
