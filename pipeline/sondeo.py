"""Sondeo: archivos de la Secretaría de Energía (producción por provincia y proyectos mineros).
Guarda un resumen y copias recortadas en data/sondeo/."""
import io
from pathlib import Path

import pandas as pd
import requests

SAL = Path(__file__).resolve().parents[1] / "data" / "sondeo"
CAB = {"User-Agent": "radiografia-argentina/1.0"}
D = "http://datos.energia.gob.ar/dataset/590d1284-fd6d-4686-afd8-b3da5d90a6e9/resource/"
URLS = {
    "petroleo_provincia": D + "86270da2-6292-4719-b7c1-20671ff9ae40/download/produccin-petrleo-sesco-tight-y-shale-captulo-iv-por-provincia.csv",
    "gas_provincia": D + "ad1b9472-a370-47e7-8de3-b742495ec7f1/download/produccin-gas-sesco-tight-y-shale-captulo-iv-por-provincia.csv",
    "petroleo_diaria_provincia": D + "a512fef1-e98e-44af-b940-76168a4bc523/download/produccin-de-petrleo-promedio-diaria-por-provincia.csv",
    "gas_diaria_provincia": D + "3d37d4f3-9b65-488e-9e64-bcd7483719fa/download/produccin-de-gas-promedio-diaria-por-provincia.csv",
    "proyectos_mineros": "http://datos.energia.gob.ar/dataset/05ceffb0-98f3-462b-98f9-96d655f76cef/resource/0c8317ac-eacb-4826-b7e7-8f0a15a62ac1/download/proyectos-mineros-ubicacin-aproximada-.csv",
}


def main():
    SAL.mkdir(parents=True, exist_ok=True)
    informe = []
    for k, u in URLS.items():
        try:
            r = requests.get(u, headers=CAB, timeout=180)
            informe.append(f"## {k}\nHTTP {r.status_code}, {len(r.content)} bytes")
            if r.status_code != 200:
                continue
            df = pd.read_csv(io.BytesIO(r.content), low_memory=False)
            informe.append(f"filas {len(df)}, columnas {list(df.columns)}")
            for c in df.columns:
                if df[c].dtype == object and df[c].nunique() <= 60:
                    informe.append(f"- {c}: {sorted(map(str, df[c].dropna().unique()))}")
            informe.append("```\n" + df.head(5).to_csv(index=False) + "...\n" + df.tail(5).to_csv(index=False) + "```")
            if k == "proyectos_mineros" or len(r.content) < 8_000_000:
                (SAL / f"{k}.csv").write_bytes(r.content)
        except Exception as e:
            informe.append(f"## {k}\nerror {e}")
    (SAL / "resultado.md").write_text("\n".join(informe) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
