"""Sondeo: baja los archivos de la Secretaría de Minería (SIACAM) y los guarda como texto en data/sondeo/."""
import io
from pathlib import Path

import pandas as pd
import requests

SAL = Path(__file__).resolve().parents[1] / "data" / "sondeo"
CAB = {"User-Agent": "radiografia-argentina/1.0"}
B = "https://www.mecon.gob.ar/dataset/"
URLS = {
    "expo_minerales": B + "Comercio/expominerales-siacam.csv",
    "expo_sector": B + "Comercio/expo-mineria-por-sector.csv",
    "expo_provincia": B + "Comercio/expo-mineria-por-provincia.csv",
    "expo_productos": B + "Comercio/principales-productos-mineros-exportados.csv",
    "balanza_minera": B + "Comercio/balanza-comercial-mineria.csv",
    "empleo_rubro_prov": B + "Empleo-rubro-prov.csv",
    "empleo_rubro_genero_prov": B + "Empleo-rubro-genero-prov.csv",
    "vbp_mineria": B + "VBP-VAP-Mineria.csv",
    "ipi_minero_series": B + "ipi-minero/ipi-minero-series.csv",
    "ipi_minero_ramas": B + "ipi-minero/ipi-minero-ramas-actividad.csv",
    "ipi_minero_litio": B + "ipi-minero/ipi-minero-produccion-litio.csv",
    "expo_litio": B + "Tablero-Litio/Exportaciones-litio.csv",
    "cartera_metaliferos": B + "Cartera-de-Proyectos-Mineros-Metaliferos-y-Litio-del-SIACAM.xlsx",
}


def main():
    SAL.mkdir(parents=True, exist_ok=True)
    informe = []
    for k, u in URLS.items():
        try:
            r = requests.get(u, headers=CAB, timeout=90)
            informe.append(f"{k}: HTTP {r.status_code}, {len(r.content)} bytes")
            if r.status_code != 200:
                continue
            if u.endswith(".xlsx"):
                for hoja, df in pd.read_excel(io.BytesIO(r.content), sheet_name=None, header=None).items():
                    (SAL / f"{k}__{hoja[:30].replace('/', '_')}.txt").write_text(df.to_csv(index=False), encoding="utf-8")
            else:
                (SAL / f"{k}.txt").write_bytes(r.content)
        except Exception as e:
            informe.append(f"{k}: error {e}")
    (SAL / "resultado.md").write_text("\n".join(informe) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
