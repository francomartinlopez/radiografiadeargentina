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
import io
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
# Datos de Argentina se actualiza el día 20; Radiografía, el 21. Las series que comparten se toman
# de su repositorio (ya bajadas y revisadas) y solo se descarga directo lo que no está allá.
DATOSARGENTINA = "https://raw.githubusercontent.com/francomartinlopez/datosargentina/main/"


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
    conocidas = (set(base.get("series", {})) | set(base.get("empalmes", {})) | set(base.get("calculos", {}))
                 | set(catalogo.get("calculos") or {}))
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
        if g.get("burbujas"):
            for b in g["burbujas"]:
                for k in ("x", "y"):
                    if b.get(k) not in conocidas:
                        errores.append(f"{gid}: la serie '{b.get(k)}' no está en indicadores.yaml")
        elif g.get("categorias"):
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


def insumos_propios(nombre: str, catalogo: dict) -> list[str]:
    """Series de indicadores.yaml que necesita una serie (si es un cálculo propio, sus insumos)."""
    c = (catalogo.get("calculos") or {}).get(nombre)
    if not c:
        return [nombre]
    salida = []
    for t in c.get("tramos", []):
        salida += insumos_propios(t["serie"], catalogo)
    for k in ("a", "b", "puente"):
        if c.get(k):
            salida += insumos_propios(c[k], catalogo)
    return salida


def subconfig(base: dict, catalogo: dict) -> dict:
    """indicadores.yaml reducido a las series que usan los gráficos (y sus deflactores)."""
    necesarias = set()
    for g in catalogo.get("graficos", []):
        for sd in g.get("series", []):
            for n in insumos_propios(sd["serie"], catalogo):
                dependencias(n, base, necesarias)
        for b in g.get("burbujas", []):
            dependencias(b["x"], base, necesarias)
            dependencias(b["y"], base, necesarias)
        if g.get("moneda"):
            dependencias(DEFLACTORES[g["moneda"]], base, necesarias)
    calc_orden = [n for n in base.get("calculos", {}) if n in necesarias]
    return {
        **base,
        "series": {n: d for n, d in base["series"].items() if n in necesarias},
        "empalmes": {n: d for n, d in base.get("empalmes", {}).items() if n in necesarias},
        "calculos": {n: base["calculos"][n] for n in calc_orden},
    }


# ---------- Cálculos propios de Radiografía (graficos.yaml, sección "calculos") ----------

def empalme_con_puente(tramos: list[pd.Series], hastas: list, puente: pd.Series | None,
                       modo: str = "mensual") -> tuple[pd.Series, list[pd.Timestamp]]:
    """Encadena por variaciones como transformar.empalmar, pero los meses sin variación en ninguna
    fuente (p. ej. cuando el INDEC no publicó) se completan con la variación de la serie puente.
    Con modo="interanual" el hueco se completa con la variación interanual del puente aplicada al
    mismo mes del año anterior (sirve cuando la serie es desestacionalizada y el puente no).
    Devuelve la serie y las fechas completadas (que se marcan como tramo interpolado)."""
    variaciones, desde = [], None
    for serie, hasta in zip(tramos, hastas):
        v = serie.sort_index().pct_change().dropna()
        if desde is not None:
            v = v[v.index > desde]
        if hasta is not None:
            v = v[v.index <= pd.Timestamp(str(hasta))]
            desde = pd.Timestamp(str(hasta))
        variaciones.append(v)
    var = pd.concat(variaciones)
    var = var[~var.index.duplicated(keep="last")].sort_index()
    esperado = pd.date_range(var.index[0], var.index[-1], freq="MS")
    faltan = list(esperado.difference(var.index))
    if faltan:
        if puente is None:
            raise ValueError(f"empalme con huecos ({faltan[0]:%Y-%m}) y sin serie puente")
        if modo == "interanual":
            p = puente.sort_index()
            nivel_rel = {var.index[0] - pd.DateOffset(months=1): 1.0}
            for m in esperado:
                previo = nivel_rel[m - pd.DateOffset(months=1)]
                if m in var.index:
                    nivel_rel[m] = previo * (1 + var[m])
                else:
                    hace12 = m - pd.DateOffset(months=12)
                    nivel_rel[m] = nivel_rel[hace12] * p[m] / p[hace12]
            vp = pd.Series({m: nivel_rel[m] / nivel_rel[m - pd.DateOffset(months=1)] - 1 for m in faltan})
        else:
            vp = puente.sort_index().pct_change().reindex(faltan)
        var = pd.concat([var, vp]).sort_index()
        if var.isna().any():
            raise ValueError("la serie puente no cubre los huecos")
    ultimo = tramos[-1].sort_index().dropna()
    factores = (1 + var).cumprod()
    nivel = factores / factores.iloc[-1] * ultimo.iloc[-1]
    nivel.loc[var.index[0] - pd.DateOffset(months=1)] = nivel.iloc[0] / (1 + var.iloc[0])
    return nivel.sort_index(), faltan


def calculos_propios(catalogo: dict, mensuales: dict) -> tuple[dict, list[str]]:
    """Aplica catalogo['calculos'] sobre las series mensuales. Devuelve tramos automáticos por serie."""
    tramos_auto, alertas = {}, []
    for nombre, c in (catalogo.get("calculos") or {}).items():
        try:
            op = c["operacion"]
            if op == "empalme":
                series = [mensuales[t["serie"]] for t in c["tramos"]]
                s, faltan = empalme_con_puente(series, [t.get("hasta") for t in c["tramos"]], mensuales.get(c.get("puente")), c.get("modo_puente", "mensual"))
                mensuales[nombre] = s
                if faltan:
                    nota = c.get("nota_puente", f"Mes sin dato en la fuente; se usa la variación de {c.get('puente')}.")
                    bloques = []  # meses consecutivos en un solo tramo
                    for f in sorted(faltan):
                        if bloques and (f.year - bloques[-1][1].year) * 12 + f.month - bloques[-1][1].month == 1:
                            bloques[-1][1] = f
                        else:
                            bloques.append([f, f])
                    tramos_auto[nombre] = [{"desde": a.strftime("%Y-%m"), "hasta": b.strftime("%Y-%m"), "tipo": "interpolado", "nota": nota}
                                           for a, b in bloques]
            elif op in ("cociente", "resta", "suma", "producto", "brecha"):
                a, b = mensuales[c["a"]], mensuales[c["b"]]
                # Si una es trimestral (un dato cada 3 meses), la otra se promedia por trimestre
                for x, y in (("a", "b"), ("b", "a")):
                    sx, sy = (a, b) if x == "a" else (b, a)
                    if len(sx) > 2 and sx.index.to_series().diff().dt.days.median() > 80 and sy.index.to_series().diff().dt.days.median() < 40:
                        sy = sy.resample("QS").mean()
                        a, b = (sx, sy) if x == "a" else (sy, sx)
                a, b = a.align(b, join="inner")
                mensuales[nombre] = {"cociente": a / b, "resta": a - b, "suma": a + b, "producto": a * b, "brecha": (a / b - 1) * 100}[op].dropna() * c.get("factor", 1)
            elif op == "escala":
                mensuales[nombre] = mensuales[c["a"]] * c["factor"]
            else:
                alertas.append(f"{nombre}: operación '{op}' desconocida")
        except KeyError as e:
            alertas.append(f"{nombre}: falta la serie {e}, no se calcula")
        except Exception as e:
            alertas.append(f"{nombre}: error ({e}), no se calcula")
    return tramos_auto, alertas


# ---------- Series compartidas con Datos de Argentina ----------

def traer_de_datosargentina(sub: dict) -> tuple[set, list[str]]:
    """Copia a data/crudos las series que Datos de Argentina define igual. Devuelve cuáles trajo."""
    import requests
    alertas, traidas = [], set()
    try:
        r = requests.get(DATOSARGENTINA + "indicadores.yaml", timeout=60)
        r.raise_for_status()
        remotas = yaml.safe_load(r.text).get("series", {})
    except Exception as e:
        return traidas, [f"Datos de Argentina no disponible ({e}); se descarga todo directo"]
    for nombre, definicion in sub["series"].items():
        if remotas.get(nombre) != definicion:
            continue
        try:
            r = requests.get(f"{DATOSARGENTINA}data/crudos/{nombre}.csv", timeout=60)
            r.raise_for_status()
            df = pd.read_csv(io.StringIO(r.text), parse_dates=["fecha"])
            if df.empty:
                raise ValueError("vacía")
            nueva = pd.Series(df["valor"].values, index=df["fecha"], dtype=float)
            anterior = construir.leer_crudo(nombre)
            if anterior is not None and nueva.index.max() < anterior.index.max():
                alertas.append(f"{nombre}: Datos de Argentina tiene un dato más viejo que el guardado; se conserva el guardado")
            else:
                construir.guardar_crudo(nombre, nueva)
            traidas.add(nombre)
        except Exception as e:
            alertas.append(f"{nombre}: no se pudo traer de Datos de Argentina ({e}); se descarga directo")
    return traidas, alertas


def obtener_series(sub: dict, offline: bool) -> tuple[dict, list[str]]:
    """Crudos de todas las series: de Datos de Argentina cuando se puede y, el resto, de su fuente."""
    if offline:
        return construir.descargar(sub, True)
    traidas, alertas = traer_de_datosargentina(sub)
    de_da, a1 = construir.descargar({**sub, "series": {n: d for n, d in sub["series"].items() if n in traidas}}, True)
    directas, a2 = construir.descargar({**sub, "series": {n: d for n, d in sub["series"].items() if n not in traidas}}, False)
    alertas.append(f"Series tomadas de Datos de Argentina: {len(de_da)}; bajadas directo: {len(directas)}")
    return {**de_da, **directas}, alertas + a1 + a2


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


def burbujas_de_series(g: dict, mensuales: dict) -> tuple[list[dict], list[str]]:
    """Burbujas a partir de pares de series (p. ej. actividad y empleo por sector).

    x: variación interanual promedio de los últimos `meses` meses de la serie x (actividad).
    y: participación de la serie y en la suma de todas las y (empleo), en el último mes común.
    tamano: nivel de y. grupo: según la variación interanual de y (creó / destruyó / sin cambios).
    """
    meses = int(g.get("meses", 6))
    umbral = float(g.get("umbral_grupo", 0.5))
    pares, alertas = [], []
    for b in g["burbujas"]:
        sx, sy = mensuales.get(b["x"]), mensuales.get(b["y"])
        if sx is None or sy is None:
            alertas.append(f"{g['id']}: falta {b['x'] if sx is None else b['y']}")
            continue
        pares.append((b, sx.dropna(), sy.dropna()))
    if not pares:
        return [], alertas
    fin = min(min(sx.index.max(), sy.index.max()) for _, sx, sy in pares)
    total_y = sum(float(sy.get(fin, float("nan"))) for _, _, sy in pares)
    salida = []
    for b, sx, sy in pares:
        ia = ((sx / sx.shift(12) - 1) * 100).dropna()
        ia = ia[ia.index <= fin].iloc[-meses:]
        y_fin, y_ant = sy.get(fin), sy.get(fin - pd.DateOffset(years=1))
        if len(ia) < meses or y_fin is None or y_ant is None or not total_y:
            alertas.append(f"{g['id']}: datos incompletos para {b['categoria']}")
            continue
        var_y = (y_fin / y_ant - 1) * 100
        grupo = "Creó empleo" if var_y > umbral else "Destruyó empleo" if var_y < -umbral else "Sin cambios"
        salida.append({"categoria": b["categoria"], "x": _f(ia.mean()), "y": _f(y_fin / total_y * 100),
                       "tamano": _f(y_fin), "var_y": _f(var_y), "grupo": grupo, "fecha": fin.strftime("%Y-%m-%d")})
    return salida, alertas


def construir_grafico(g: dict, mensuales: dict, catalogo: dict) -> tuple[dict | None, list[str]]:
    alertas = []
    gobiernos = catalogo["gobiernos"]
    auto = [dict(t, serie=sd["serie"]) for sd in g.get("series", [])
            for t in catalogo.get("_tramos_auto", {}).get(sd["serie"], [])]
    tramos = g.get("tramos", []) + auto
    salida = {
        k: g[k] for k in ("id", "tema", "titulo", "que_muestra", "original", "tipo", "unidad", "fuentes",
                          "metodo", "estimacion", "sensible", "nota", "eje_x", "eje_y") if g.get(k) is not None
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
        "medidas": g.get("medidas"),
        **({"tramos": tramos} if tramos else {}),
    })
    if g.get("burbujas"):
        salida["categorias"], al = burbujas_de_series(g, mensuales)
        salida["ultimo"] = salida["categorias"][0].get("fecha") if salida["categorias"] else None
        return (salida if salida["categorias"] else None), alertas + al
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
            if g.get("medida_por_gobierno") == "variacion":  # p. ej. inflación mensual a partir del índice
                s = ((s / s.shift(1) - 1) * 100).dropna()
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
    crudas, alertas = obtener_series(sub, args.offline)
    mensuales, alertas_proc = construir.procesar(sub, crudas)
    catalogo["_tramos_auto"], alertas_calc = calculos_propios(catalogo, mensuales)
    # Las series cerradas (bases viejas, ediciones fijas) no esperan datos nuevos
    cerradas = {n for n, d in sub["series"].items() if d.get("cerrada")}
    alertas += alertas_proc + alertas_calc
    alertas = [a for a in alertas if not (a.split(":")[0] in cerradas and "sin dato nuevo" in a)]
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
