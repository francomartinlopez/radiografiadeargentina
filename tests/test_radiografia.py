import pandas as pd

from pipeline import radiografia as r


def catalogo_base():
    base, cat = r.cargar()
    return base, cat


def test_catalogo_real_sin_errores():
    base, cat = catalogo_base()
    assert r.validar(cat, base) == []


def test_validar_detecta_errores():
    base, cat = catalogo_base()
    malo = {**cat, "graficos": [
        {"id": "x", "tema": 99, "titulo": "X", "tipo": "torta", "fuentes": [{"nombre": "A", "nivel": "otra"}],
         "series": [{"serie": "no_existe"}], "tramos": [{"tipo": "inventado"}]},
        {"id": "x", "tema": 1, "titulo": "Y", "tipo": "lineas", "fuentes": [{"nombre": "B", "nivel": "primaria"}], "series": [{"serie": "ipc"}]},
    ]}
    errores = " | ".join(r.validar(malo, base))
    for texto in ("tipo 'torta'", "tema 99", "sin nivel válido", "no_existe", "tramo con tipo", "id repetido"):
        assert texto in errores


def test_dependencias_incluye_empalmes():
    base, _ = catalogo_base()
    dep = r.dependencias("ipc", base)
    assert {"ipc", "ipc_gba_historico", "ipc_nacional"} <= dep


def test_subconfig_solo_lo_necesario_y_deflactor():
    base, cat = catalogo_base()
    sub = r.subconfig(base, cat)
    assert "recaudacion" in sub["series"] and "ipc_nacional" in sub["series"]
    assert "litio" not in sub["series"]


def test_tramo_por_fecha_y_serie():
    tramos = [{"desde": "2020-01", "hasta": "2020-12", "tipo": "estimado"}, {"serie": "b", "desde": "2024", "tipo": "proyectado"}]
    assert r.tramo_de(pd.Timestamp("2020-06-01"), tramos, "a") == "estimado"
    assert r.tramo_de(pd.Timestamp("2025-06-01"), tramos, "a") is None
    assert r.tramo_de(pd.Timestamp("2025-06-01"), tramos, "b") == "proyectado"


def test_agregar_por_gobierno():
    _, cat = catalogo_base()
    meses = pd.date_range("2019-01-01", "2024-12-01", freq="MS")
    s = pd.Series(1.0, index=meses)
    s[s.index >= "2020-01-01"] = 3.0
    cats = {c["categoria"]: c for c in r.agregar_por_gobierno(s, cat["gobiernos"], "promedio")}
    assert cats["Macri"]["valor"] == 1.0 and cats["Macri"]["n"] == 11  # dic-2019 ya es de A. Fernández
    assert abs(cats["A. Fernández"]["valor"] - (1 + 3 * 47) / 48) < 1e-6
    assert cats["Milei"]["n"] == 13  # de diciembre de 2023 a diciembre de 2024


def test_construir_grafico_con_tramos_y_previo():
    _, cat = catalogo_base()
    meses = pd.date_range("1995-01-01", "2024-12-01", freq="MS")
    m = {"s": pd.Series(range(len(meses)), index=meses, dtype=float)}
    g = {"id": "t", "tema": 1, "titulo": "T", "tipo": "lineas", "frecuencia": "M", "desde": "2001-01", "unidad": "u",
         "series": [{"serie": "s", "nombre": "S"}], "fuentes": [{"nombre": "F", "nivel": "estimacion"}],
         "tramos": [{"desde": "2024-01", "tipo": "proyectado"}]}
    out, alertas = r.construir_grafico(g, m, cat)
    assert alertas == [] and out["alerta"] is True
    puntos = out["series"][0]["puntos"]
    assert puntos[0][0] == "1999-01-01"  # 24 meses antes del inicio, para interanual y acumulado
    assert out["desde"] == "2001-01-01"
    assert puntos[-1][2] == "proyectado" and len(puntos[-13]) == 2
    csv = r.csv_de(out)
    assert csv["fecha"].min() == "2001-01-01" and set(csv["tramo"]) == {"observado", "proyectado"}


def test_series_largas_anuales():
    _, cat = catalogo_base()
    anios = pd.date_range("1850-01-01", "2020-01-01", freq="YS")
    m = {"s": pd.Series(1.0, index=anios)}
    g = {"id": "t", "tema": 19, "titulo": "T", "tipo": "lineas_pais", "frecuencia": "A", "series": [{"serie": "s"}],
         "fuentes": [{"nombre": "F", "nivel": "secundaria"}]}
    out, _ = r.construir_grafico(g, m, cat)
    assert out["desde"] == "1850-01-01" and out["gobiernos"] is False


def test_burbujas_de_series():
    meses = pd.date_range("2023-01-01", "2025-06-01", freq="MS")
    m = {"x1": pd.Series([100 * 1.01 ** i for i in range(len(meses))], index=meses),
         "y1": pd.Series([200 + i for i in range(len(meses))], index=meses, dtype=float),
         "x2": pd.Series(100.0, index=meses), "y2": pd.Series(100.0, index=meses)}
    g = {"id": "b", "meses": 6, "burbujas": [{"categoria": "A", "x": "x1", "y": "y1"}, {"categoria": "B", "x": "x2", "y": "y2"}]}
    cats, alertas = r.burbujas_de_series(g, m)
    a, b = cats
    assert alertas == [] and abs(a["x"] - (1.01 ** 12 - 1) * 100) < 1e-6 and b["x"] == 0
    assert abs(a["y"] + b["y"] - 100) < 1e-6
    assert a["grupo"] == "Creó empleo" and b["grupo"] == "Sin cambios"


def test_csv_url_parsea_anios_y_filtro():
    from pipeline.fuentes import csv_url
    texto = "Entity,Year,GDP per capita\nArgentina,1850,1994\nArgentina,1870,\nBrazil,1850,867\nArgentina,1900,2756\n"
    s = csv_url.parsear(texto, {"filtro": {"Entity": "Argentina"}, "fecha": "Year", "valor": "GDP per capita"})
    assert list(s.index.year) == [1850, 1900] and s.iloc[-1] == 2756


def test_empalme_puente_interanual():
    import pandas as pd
    from pipeline.radiografia import empalme_con_puente
    f = pd.date_range("2014-01-01", "2016-12-01", freq="MS")
    puente = pd.Series([100 * 1.01 ** i for i in range(len(f))], index=f)
    viejo = pd.Series(range(1, 22), index=f[:21], dtype=float)  # hasta 2015-09
    nuevo = pd.Series(range(50, 61), index=f[25:], dtype=float)  # desde 2016-02
    s, faltan = empalme_con_puente([viejo, nuevo], ["2015-09", None], puente, "interanual")
    assert [m.strftime("%Y-%m") for m in faltan] == ["2015-10", "2015-11", "2015-12", "2016-01", "2016-02"][:len(faltan)]
    oct15 = s[pd.Timestamp("2015-10-01")] / s[pd.Timestamp("2014-10-01")]
    assert abs(oct15 - 1.01 ** 12) < 1e-9


def test_worldbank_e_imf_parsean():
    from pipeline.fuentes import imf, worldbank
    filas = (("ARG", "2020", 10.5), ("ARG", "2021", None), ("BRA", "2020", 3.0), ("ARG", "2019", 9.0))
    s = worldbank.parsear(filas, "ARG")
    assert list(s.values) == [9.0, 10.5] and s.index[0].year == 2019
    js = {"values": {"GGXWDG_NGDP": {"ARG": {"2019": 88.7, "2020": 102.8, "2099": 50.0}}}}
    s = imf.parsear(js, "GGXWDG_NGDP", "ARG")
    assert list(s.values) == [88.7, 102.8]
