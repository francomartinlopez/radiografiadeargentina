# Radiografía de la Argentina

Gráficos económicos y sociales de la Argentina con datos públicos. Cada gráfico conserva el período de su versión original (de 1850 a hoy, según el caso), dice de dónde sale cada dato y de qué nivel es la fuente (primaria oficial, secundaria, terciaria o estimación propia) y marca con ⚠ los tramos estimados, interpolados o proyectados.

Vistas: período original completo, último mandato, interanual, acumulado de 12 meses y variación a elección. En los gráficos de línea, franjas de color por gobierno desde 1999.

El plan de trabajo está en `docs/plan.md` y el inventario de los 479 gráficos (fichas, lotes y estado de avance) en `docs/Inventario_graficos_Radiografia.xlsx`.

Base técnica: el sistema de [Datos de Argentina](https://github.com/francomartinlopez/datosargentina), extendido. Publicación: Netlify (`netlify.toml` publica `sitio/public`).

---

## Cómo funciona

1. `indicadores.yaml` es la base de series (de dónde se baja cada dato, empalmes y cálculos), compartida con Datos de Argentina.
2. `graficos.yaml` es el catálogo de Radiografía: un gráfico por entrada, con tema, tipo, período original, series, fuentes con su nivel, método y tramos estimados. El formato está explicado al principio del archivo y en `docs/como-cargar.md`.
3. `python -m pipeline.radiografia` baja solo las series que usan los gráficos, las procesa y escribe en `sitio/public/datos/`:
   - un JSON y un CSV por gráfico en `datos/graficos/`;
   - `radiografia.json`, con los temas, los gobiernos y la lista de gráficos.

   El resumen de la corrida queda en `data/informe.md`.
4. El sitio (`sitio/public`) calcula las medidas a partir del nivel de cada serie: variación, interanual, acumulado de 12 meses y base 100. También permite elegir entre el período completo y el último mandato, y mostrar u ocultar las franjas de gobierno.
5. El día 20 de cada mes, GitHub Actions corre el proceso y abre un pull request con los cambios y las alertas. Al aprobarlo, Netlify publica la versión nueva.

## Uso local

```bash
pip install -r requirements.txt
python -m pytest -q
python -m pipeline.radiografia            # descarga y procesa
python -m pipeline.radiografia --offline  # reprocesa con los datos ya bajados (data/crudos)
cd sitio/public && python -m http.server  # ver el sitio en http://localhost:8000
```

## Metodología común

- **IPC empalmado:** se usan cuatro fuentes según el período y se encadenan sus variaciones mensuales.
  - IPC-GBA del INDEC hasta diciembre de 2006.
  - IPC de San Luis de 2007 a julio de 2012.
  - IPC de la Ciudad de Buenos Aires hasta diciembre de 2016.
  - IPC nacional del INDEC desde entonces.
- **Moneda constante:** los pesos se deflactan con el IPC empalmado y los dólares con el IPC de Estados Unidos. Ambos se llevan al último mes con dato.
- **Tasas y saldos:** las variaciones se expresan en puntos o en diferencia, no en porcentaje.
- **Tramos no observados:** los datos estimados, interpolados o proyectados se dibujan con línea punteada y ⚠, y en el CSV llevan la columna `tramo`.
- **Gobiernos:** las franjas arrancan con De la Rúa (10/12/1999). El mes de una asunción se asigna a quien gobernó la mayor parte de ese mes.

El sistema de Datos de Argentina (`pipeline/construir.py` y sus módulos) sigue en el repositorio como base de las descargas.
