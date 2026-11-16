import numpy as np
import pandas as pd

from pipeline.fuentes import eph_panel


def persona(codusu, anio, trim, edad, estado, cat=np.nan, sector=np.nan, aporta=np.nan, p21=0, p47t=0, sexo=1):
    return {"CODUSU": codusu, "NRO_HOGAR": 1, "COMPONENTE": 1, "ANO4": anio, "TRIMESTRE": trim, "CH04": sexo, "CH06": edad,
            "ESTADO": estado, "CAT_OCUP": cat, "PP04A": sector, "PP07H": aporta, "P21": p21, "PONDIIO": 100,
            "PONDERA": 100, "P47T": p47t, "PONDII": 100}


def test_situacion():
    df = pd.DataFrame([persona("A", 2020, 1, 30, 1, 3, 2, 1), persona("B", 2020, 1, 30, 1, 3, 1, 2),
                       persona("C", 2020, 1, 30, 1, 3, 2, 2), persona("D", 2020, 1, 30, 1, 2),
                       persona("E", 2020, 1, 30, 2), persona("F", 2020, 1, 30, 3)])
    assert list(eph_panel.situacion(df)) == ["F", "PUB", "NR", "CP", "DES", "INA"]


def test_emparejar_y_cambio():
    ipc = pd.Series(100.0, index=pd.date_range("2019-01-01", "2022-12-01", freq="MS"))
    df = pd.DataFrame([
        persona("A", 2020, 1, 30, 1, 3, 2, 1, p21=1000),  # formal -> cuenta propia, ingreso a la mitad
        persona("A", 2021, 1, 31, 1, 2, p21=500),
        persona("B", 2020, 1, 40, 1, 3, 2, 1, p21=1000),  # otra persona en la misma vivienda: otra edad, se descarta
        persona("B", 2021, 1, 45, 1, 2, p21=500),
    ])
    m = eph_panel.emparejar(df, ipc)
    assert list(m.CODUSU) == ["A"]
    assert m.iloc[0]["cat"] == "F" and m.iloc[0]["cat_1"] == "CP"
    n, prom, med = eph_panel.cambio(pd.concat([m] * 5))
    assert n == 5 and prom == -50.0 and med == -50.0
