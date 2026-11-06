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
    "gdp-per-capita-maddison-project-database",
    "gdp-per-capita-maddison",
    "gdp-per-capita-maddison-2020",
    "inflation-of-consumer-prices",
    "inflation-consumer-prices",
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
                arg = df[df.get("code", pd.Series(dtype=str)) == "ARG"] if "code" in df else df.head(0)
                lineas += [f"- columnas: {', '.join(df.columns)}", f"- filas: {len(df)}, años: {df['year'].min()}–{df['year'].max()}",
                           f"- Argentina: {len(arg)} filas, desde {arg['year'].min() if len(arg) else '-'}"]
        except Exception as e:
            lineas.append(f"## {slug}: error {e}")
        lineas.append("")
    (CARPETA / "resultado.md").write_text("\n".join(lineas), encoding="utf-8")
    print("\n".join(lineas))


if __name__ == "__main__":
    main()
