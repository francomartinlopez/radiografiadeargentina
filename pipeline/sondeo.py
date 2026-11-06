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
URLS_EXTRA = [
    "https://psl.noaa.gov/data/correlation/oni.data",
    "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
    "https://api.worldbank.org/v2/country/ARG/indicator/NY.GDP.PCAP.PP.KD?format=json&per_page=3",
    "https://www.imf.org/external/datamapper/api/v1/GGXWDG_NGDP/ARG",
    "https://fred.stlouisfed.org/graph/fredgraph.csv?id=PSOYBUSDM",
]


def main() -> None:
    CARPETA.mkdir(parents=True, exist_ok=True)
    lineas = ["# Sondeo de Our World in Data", ""]
    for slug in CANDIDATOS:
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
    (CARPETA / "resultado.md").write_text("\n".join(lineas), encoding="utf-8")
    print("\n".join(lineas))


if __name__ == "__main__":
    main()
