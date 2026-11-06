"""Extractores: uno por tipo de fuente.

Cada extractor devuelve un pandas.Series con índice de fechas (Timestamp) y valores float,
ordenado y sin duplicados. La agregación a frecuencia mensual se hace después, en
pipeline.transformar.
"""
from __future__ import annotations

import time

import requests

TIMEOUT = (20, 90)
REINTENTOS = 3
CABECERAS = {"User-Agent": "datos-argentina/1.0 (+https://github.com)"}


_HOSTS_CAIDOS: set[str] = set()


def pedir(url: str, params: dict | None = None, verify: bool = True) -> requests.Response:
    """GET con reintentos y espera creciente. Lanza la última excepción si todos fallan.

    Si un sitio no responde ni siquiera a la conexión, no se vuelve a intentar en esta corrida
    (evita minutos de esperas cuando una fuente está caída o bloqueada)."""
    from urllib.parse import urlparse
    host = urlparse(url).netloc
    if host in _HOSTS_CAIDOS:
        raise RuntimeError(f"No se pudo descargar {url}: {host} no respondió antes en esta corrida")
    ultimo_error: Exception | None = None
    for intento in range(REINTENTOS):
        try:
            r = requests.get(url, params=params, timeout=TIMEOUT, headers=CABECERAS, verify=verify)
            r.raise_for_status()
            return r
        except requests.RequestException as e:  # red, 5xx, 4xx
            ultimo_error = e
            time.sleep(2 ** intento)
    # Si los tres intentos fallaron al conectar, por tiempo de espera o porque el sitio niega el
    # acceso (403), no se insiste con ese sitio en el resto de la corrida
    negado = isinstance(ultimo_error, requests.HTTPError) and ultimo_error.response is not None \
        and ultimo_error.response.status_code == 403
    if isinstance(ultimo_error, (requests.ConnectionError, requests.Timeout)) or negado:
        _HOSTS_CAIDOS.add(host)
    raise RuntimeError(f"No se pudo descargar {url}: {ultimo_error}")


def extraer(definicion: dict):
    """Despacha según el campo 'fuente' de la definición de la serie."""
    from . import archivos, argentinadatos, bcra, csv_url, datosgobar, encuestas, fred, imf, indec_api, manual, noaa, owid, worldbank, yahoo

    fuentes = {
        "datosgobar": datosgobar.extraer,
        "bcra": bcra.extraer,
        "argentinadatos": argentinadatos.extraer,
        "fred": fred.extraer,
        "manual": manual.extraer,
        "archivo": archivos.extraer,
        "yahoo": yahoo.extraer,
        "owid": owid.extraer,
        "csv_url": csv_url.extraer,
        "encuestas": encuestas.extraer,
        "indec_api": indec_api.extraer,
        "worldbank": worldbank.extraer,
        "imf": imf.extraer,
        "noaa": noaa.extraer,
    }
    tipo = definicion["fuente"]
    if tipo not in fuentes:
        raise ValueError(f"Fuente desconocida: {tipo}")
    return fuentes[tipo](definicion)
