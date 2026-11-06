# Cómo cargar un gráfico

Cada gráfico se carga siguiendo estos pasos. Son los mismos de `docs/plan.md`.

1. **Dato.** Si la serie ya existe en `indicadores.yaml`, se usa. Si no, se agrega en `series:`:
   - Con una fuente automática (`datosgobar`, `indec_api`, `bcra`, `fred`, `owid`, etc.).
   - O como carga manual, en `data/manual/<serie>.csv` con columnas `fecha,valor,fuente_url`.
2. **Transformaciones.** Se agregan en `empalmes:` o `calculos:` de `indicadores.yaml`, o con `moneda: ARS|USD` y `escala:` en el gráfico.
3. **Gráfico.** Se agrega una entrada en `graficos.yaml`. El formato de cada campo está explicado al principio de ese archivo. Lo mínimo es:

```yaml
  - id: nombre_corto
    tema: 2
    titulo: "Título"
    que_muestra: "Qué datos muestra."
    original: {ficha: p25, imagen: 1031}
    tipo: lineas            # lineas | areas | barras | barras_gobierno | lineas_pais | burbujas
    frecuencia: M           # M | T | S | A
    desde: "2001-01"        # período del gráfico original
    unidad: "millones de pesos de hoy"
    tipo_valor: flujo       # indice | nivel | flujo | tasa | saldo
    moneda: ARS
    flujo: true             # habilita "Acumulado 12 meses"
    medida_inicial: acumulado_12m
    series:
      - {serie: recaudacion, nombre: "Recaudación"}
    fuentes:
      - {nombre: "Organismo, publicación", url: "https://…", nivel: primaria, desde: "2001-01", hasta: "2016-12"}
    metodo: "Cómo se armó."
    tramos:
      - {desde: "2026-05", tipo: proyectado, nota: "Por qué y con qué datos."}
    estimacion: "Solo si todo el gráfico es una estimación: método y datos de base."
    sensible: "Solo en temas sensibles: alcance y limitaciones de cada dato."
```

4. **Datos por categoría.** Para barras por país o por caso y para burbujas sin eje de tiempo, se usa `categorias: <archivo>`. El archivo va en `data/categorias/<archivo>.csv`, con las columnas `categoria, serie, valor, x, y, tamano, tramo, fuente_url`.
5. **Prueba.** Correr `python -m pytest -q` y `python -m pipeline.radiografia --offline`, y abrir el sitio local.
6. **Seguimiento.** En `docs/Inventario_graficos_Radiografia.xlsx`, pestaña **Plan web**, actualizar la columna **Estado de avance**.
