"""Sondeo de fuentes que no se pueden consultar desde fuera de GitHub (corre en GitHub Actions).

Prueba gráficos de Our World in Data y deja un resumen en data/sondeo/resultado.md y los CSV
completos en data/sondeo/, para revisar qué columnas y países traen antes de cargar las series.
Se corre empujando a la rama "sondeo" (ver .github/workflows/sondeo.yml).
"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import requests

CARPETA = Path(__file__).resolve().parents[1] / "data" / "sondeo"
CANDIDATOS = [
    # Series históricas largas (desde 1800-1850) para las comparaciones entre países
    "cross-country-literacy-rates", "literacy-rate-adult-total", "literate-and-illiterate-world-population",
    "urbanization-last-500-years", "share-of-population-urban", "urban-population-share-2050",
    "crude-birth-rate", "birth-rate-vs-death-rate", "children-born-per-woman",
    "homicide-rate-unodc", "homicide-rate-in-europe-over-long-term", "homicide-rate",
    "mean-years-of-schooling-long-run", "share-of-the-population-with-completed-tertiary-education",
    "primary-school-enrollment-rate", "gross-enrollment-ratio-in-secondary-education",
    "life-expectancy", "child-mortality", "prevalence-of-undernourishment", "share-of-children-who-are-stunted",
    "share-of-the-population-with-access-to-electricity", "motor-vehicles-per-1000-people", "cars-per-1000-people",
    "nobel-laureates-per-capita", "nobel-prizes-by-country", "gdp-per-capita-maddison-project-database",
    "real-wages-in-manufacturing", "average-years-of-schooling",
]
CANDIDATOS_AHORA: list[str] = []
URLS_EXTRA = [
    "https://psl.noaa.gov/data/correlation/oni.data",
    "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
    "https://api.worldbank.org/v2/country/ARG/indicator/NY.GDP.PCAP.PP.KD?format=json&per_page=3",
    "https://www.imf.org/external/datamapper/api/v1/GGXWDG_NGDP/ARG",
    "https://api.worldbank.org/v2/country/ARG/indicator/SH.DYN.0509?format=json&per_page=4",
    "https://api.worldbank.org/v2/country/ARG/indicator/SH.DYN.1014?format=json&per_page=4",
    "https://api.worldbank.org/v2/country/ARG/indicator/SH.DYN.1519?format=json&per_page=4",
]


DEIS = {
    "def_05_22": "http://datos.salud.gob.ar/dataset/27c588e8-43d0-411a-a40c-7ecc563c2c9f/resource/ccf688f4-db38-4b0f-86f3-c99341ac52ad/download/defunciones-ocurridas-y-registradas-en-la-republica-argentina-entre-los-anos-2005-2022.csv",
    "def_23": "http://datos.salud.gob.ar/dataset/27c588e8-43d0-411a-a40c-7ecc563c2c9f/resource/e71b36a0-a68b-4bb5-a969-0a25929785bb/download/defuncion2023.csv",
    "def_m_15_22": "http://datos.salud.gob.ar/dataset/c1643775-18e1-40fd-9e7f-0cebb5b1abe6/resource/5b21a088-3c04-4fdd-8741-82ab6add2730/download/arg_def_m_15_22.csv",
    "def_m_23": "http://datos.salud.gob.ar/dataset/c1643775-18e1-40fd-9e7f-0cebb5b1abe6/resource/615c454b-c02c-4011-b55a-86e8a28167bf/download/base_def_23_men.csv",
    "def_hist": "http://datos.salud.gob.ar/dataset/76ce7d19-921d-4d17-bb20-73c1fe55f07e/resource/a4d3c1c7-63c3-4ad6-91e7-ffef6198c8c0/download/serie-historica-ocurrida-argentina-jurisdiccion-1914-2023.csv",
}


def sondear_deis() -> list[str]:
    """Muestra estructura de las bases de defunciones de la DEIS (no se alcanzan desde fuera de GitHub)."""
    lineas = ["# Bases de defunciones DEIS", ""]
    for nombre, url in DEIS.items():
        try:
            r = requests.get(url, timeout=300, headers={"User-Agent": "radiografia-argentina/1.0"})
            lineas.append(f"## {nombre}: HTTP {r.status_code}, {len(r.content)} bytes")
            if not r.ok:
                continue
            texto = None
            for enc in ("utf-8", "latin-1"):
                try:
                    texto = r.content.decode(enc); break
                except UnicodeDecodeError:
                    pass
            sep = ";" if texto.splitlines()[0].count(";") > texto.splitlines()[0].count(",") else ","
            df = pd.read_csv(io.StringIO(texto), sep=sep, dtype=str, low_memory=False)
            lineas += [f"- separador {sep!r}, filas {len(df)}", "```", texto[:800], "```"]
            for c in df.columns:
                vc = df[c].value_counts()
                muestra = "; ".join(f"{k} ({v})" for k, v in vc.head(40).items())
                lineas.append(f"- **{c}** ({vc.size} valores): {muestra[:1500]}")
        except Exception as e:
            lineas.append(f"## {nombre}: error {e}")
        lineas.append("")
    return lineas


def sondear_presupuesto() -> list[str]:
    """Estructura de las bases de ejecución presupuestaria (dgsiaf-repo.mecon.gob.ar)."""
    import zipfile
    lineas = ["# Ejecución presupuestaria por servicio (crédito mensual)", ""]
    base = "https://dgsiaf-repo.mecon.gob.ar/repository/pa/datasets/{a}/credito-mensual-{a}.zip"
    for anio in (1995, 2001, 2004, 2008, 2013, 2019, 2026):
        url = base.format(a=anio)
        try:
            r = requests.get(url, timeout=600, headers={"User-Agent": "radiografia-argentina/1.0"})
            lineas.append(f"## {anio}: HTTP {r.status_code}, {len(r.content)} bytes")
            if not r.ok:
                continue
            z = zipfile.ZipFile(io.BytesIO(r.content))
            lineas.append("- archivos: " + ", ".join(f"{i.filename} ({i.file_size})" for i in z.infolist()))
            nombre = z.namelist()[0]
            crudo = z.read(nombre)
            texto = crudo.decode("utf-8", errors="replace")
            lineas += ["```", texto[:700], "```"]
            if anio in (2001, 2026):
                sep = ";" if texto[:500].count(";") > texto[:500].count(",") else ","
                df = pd.read_csv(io.StringIO(texto), sep=sep, dtype=str, low_memory=False)
                lineas.append(f"- columnas: {', '.join(df.columns)}; filas {len(df)}")
                cs = [c for c in df.columns if "servicio" in c.lower()]
                for c in cs:
                    lineas.append(f"- **{c}**: " + "; ".join(sorted(df[c].dropna().unique())[:400])[:9000])
        except Exception as e:
            lineas.append(f"## {anio}: error {e}")
        lineas.append("")
    return lineas


def resumir_presupuesto() -> list[str]:
    """Resume la ejecución por servicio de todos los años (para copiar a data/crudos/presupuesto)."""
    from pipeline.fuentes import presupuesto
    presupuesto.CARPETA = CARPETA / "presupuesto"
    df = presupuesto.tabla()
    df["anio"] = df["fecha"].dt.year
    lineas = ["# Servicios por año (devengado anual, millones de pesos corrientes)", "",
              "Errores: " + " | ".join(getattr(presupuesto.tabla, "errores", [])), ""]
    for sid, g in df.groupby("servicio_id"):
        anios = g.groupby("anio")["devengado"].sum()
        nombres = " / ".join(dict.fromkeys(g["servicio_desc"].astype(str)))
        lineas.append(f"- **{sid}** {nombres[:300]} | {anios.index.min()}-{anios.index.max()} | "
                      f"{anios.get(2001, 0):.0f} / {anios.get(2015, 0):.0f} / {anios.get(2025, 0):.0f}")
    return lineas


PAGINAS = [  # (url, patrón de enlaces a listar)
    ("https://www.bcra.gob.ar/listado-informe-de-pagos-minoristas/", r"(?i)xls|pdf"),
    ("https://www.bcra.gob.ar/en/means-payment-2/", r"(?i)xls|cheq|check"),
]
ARCHIVOS: list[str] = []
_ARCHIVOS_VIEJOS = [
    "https://datos.magyp.gob.ar/dataset/c19a5875-fb39-48b6-b0b2-234382722afb/resource/52e72aec-4ab6-4d60-8c95-47de21e46eec/download/existencias-bovinas-2008-2019.csv",
]


def sondear_paginas() -> list[str]:
    import re
    lineas = ["# Páginas y archivos", ""]
    for url, patron in PAGINAS:
        try:
            r = requests.get(url, timeout=120, headers={"User-Agent": "Mozilla/5.0 radiografia-argentina"})
            enlaces = sorted(set(re.findall(r'(?:href|url)["=:\s]+"?([^"\'\s<>]+)', r.text)))
            enlaces = [e for e in enlaces if re.search(patron, e)]
            lineas += [f"## {url}: HTTP {r.status_code}, {len(r.text)} car."] + [f"- {e}" for e in enlaces[:120]]
        except Exception as e:
            lineas.append(f"## {url}: error {e}")
        lineas.append("")
    for url in ARCHIVOS:
        try:
            r = requests.get(url, timeout=120, headers={"User-Agent": "Mozilla/5.0 radiografia-argentina"})
            lineas += [f"## {url}: HTTP {r.status_code}", "```", r.content.decode("utf-8", "replace")[:3000], "```", ""]
        except Exception as e:
            lineas.append(f"## {url}: error {e}")
    return lineas


def sondear_magyp() -> list[str]:
    import re
    r = requests.get("https://www.magyp.gob.ar/sitio/areas/bovinos/informacion_interes/informes/index.php",
                     timeout=120, headers={"User-Agent": "Mozilla/5.0 radiografia-argentina"})
    rutas = sorted(set(m.group(0) for m in re.finditer(r"[^\"'<>]{0,200}[Ss]tock[^\"'<>]{0,200}", r.text)))
    lineas = ["# Informes de bovinos (MAGyP)", ""] + [f"- {x.strip()}" for x in rutas][:300]
    lineas += ["", "## Otras carpetas"] + sorted({f"- {x.split('/')[1]}" for x in rutas if "/" in x})[:80]
    return lineas


def sondear_xlsx_stock() -> list[str]:
    url = ("https://www.magyp.gob.ar/sitio/areas/bovinos/informacion_interes/informes/_archivos/"
           "000001=Series%20de%20stock%20bovino%20y%20mapas/000000_Stock/"
           "251231_Serie%20stock%20Bovino%20por%20provincia%20al%2031-12%20(2007-2025).xlsx")
    r = requests.get(url, timeout=180, headers={"User-Agent": "Mozilla/5.0 radiografia-argentina"})
    lineas = [f"# Serie stock bovino: HTTP {r.status_code}, {len(r.content)} bytes", ""]
    h = pd.read_excel(io.BytesIO(r.content), sheet_name=None, header=None)
    lineas.append("Hojas: " + ", ".join(f"{k} {v.shape}" for k, v in h.items()))
    for k, df in list(h.items())[:4]:
        lineas += [f"## {k}", "```", df.head(40).to_string(max_cols=14, max_colwidth=22), "```"]
    return lineas


def main() -> None:
    CARPETA.mkdir(parents=True, exist_ok=True)
    lineas = ["# Sondeo de Our World in Data", ""]
    for slug in CANDIDATOS_AHORA:
        url = f"https://ourworldindata.org/grapher/{slug}.csv"
        try:
            r = requests.get(url, params={"v": 1, "csvType": "full", "useColumnShortNames": "true"},
                             timeout=120, headers={"User-Agent": "radiografia-argentina/1.0"})
            lineas.append(f"## {slug}: HTTP {r.status_code}")
            if r.ok:
                df = pd.read_csv(io.StringIO(r.text))
                (CARPETA / f"{slug}.csv").write_text(r.text, encoding="utf-8")
                paises = ["ARG", "BRA", "CHL", "URY", "MEX", "ESP", "ITA", "USA", "GBR", "AUS", "FRA", "DEU", "JPN", "CAN"]
                if "code" in df:
                    cob = df[df["code"].isin(paises)].groupby("code")["year"].agg(["min", "max", "count"])
                    lineas.append("- cobertura: " + "; ".join(f"{c} {r['min']}-{r['max']} ({r['count']})" for c, r in cob.iterrows()))
                arg = df[df.get("code", pd.Series(dtype=str)) == "ARG"] if "code" in df else df.head(0)
                lineas += [f"- columnas: {', '.join(df.columns)}", f"- filas: {len(df)}, años: {df['year'].min()}–{df['year'].max()}",
                           f"- Argentina: {len(arg)} filas, desde {arg['year'].min() if len(arg) else '-'}"]
        except Exception as e:
            lineas.append(f"## {slug}: error {e}")
        lineas.append("")
    for url in URLS_EXTRA:
        try:
            r = requests.get(url, timeout=120, headers={"User-Agent": "radiografia-argentina/1.0"})
            lineas += [f"## {url}: HTTP {r.status_code}", "```", r.text[:600], "```", ""]
        except Exception as e:
            lineas += [f"## {url}: error {e}", ""]
    lineas = ["# OWID salud"]
    for slug in ["share-of-children-younger-than-5-who-suffer-from-stunting", "stunting-prevalence-jme", "share-of-children-with-a-height-too-low-for-their-age",
                 "children-stunted", "prevalence-of-stunting-in-children-under-5", "share-of-children-who-are-wasted", "share-of-children-with-a-weight-too-low-for-their-height",
                 "new-cases-of-hiv-infection", "number-of-new-hiv-infections"]:
        try:
            r = requests.get(f"https://ourworldindata.org/grapher/{slug}.csv", params={"v": 1, "csvType": "full", "useColumnShortNames": "true"}, timeout=120, headers={"User-Agent": "radiografia-argentina/1.0"})
            linea = f"- {slug}: HTTP {r.status_code}"
            if r.ok:
                df = pd.read_csv(io.StringIO(r.text))
                arg = df[df["code"] == "ARG"]
                linea += f" cols={list(df.columns)} ARG {arg['year'].min()}-{arg['year'].max()} ({len(arg)})"
            lineas.append(linea)
        except Exception as e:
            lineas.append(f"- {slug}: error {e}")
    (CARPETA / "resultado.md").write_text("\n".join(lineas), encoding="utf-8")
    print("\n".join(lineas))


if __name__ == "__main__":
    main()
