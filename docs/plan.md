# Radiografía de la Argentina: plan de la web de gráficos

## 1. Qué es
Una web hermana de **Datos de Argentina**, con una estética parecida pero no igual, llamada **Radiografía de la Argentina**. Tiene los gráficos del documento rehechos desde datos reales y actualizados al último dato que se encuentre.

Solo importan los datos y el gráfico. Se descartan banderas, fotos, íconos, fondos y todo el decorado de las imágenes originales.

## 2. Decisiones tomadas
- **Período:** cada gráfico conserva el período de su original, que puede ser más corto, igual o más largo que 2001–hoy (hay series desde 1850).
- **Vistas:**
  - Período original completo.
  - Último mandato, desde el 10/12/2023.
  - Interanual.
  - Acumulado de 12 meses, en flujos como recaudación, gasto o exportaciones.
  - Variación elegible: %, puntos o diferencia.
  - En series anuales, variación anual.
- **Gobiernos:** en los gráficos de línea, franjas de color con una línea vertical en cada asunción. En barras, burbujas y comparaciones entre países no van. Cuando el dato es un promedio por mandato, una barra por gobierno.
- **Comparaciones entre países:** serie completa por país, en la medida en que haya datos, en lugar de un año de crisis distinto para cada uno.
- **Estimaciones:** se publican, pero con el símbolo ⚠, el método, los datos de base y de dónde sale cada uno. Si solo una parte de la serie es estimada, interpolada o proyectada, esa parte va punteada y con ⚠.
- **Fuentes:** cada gráfico dice si la fuente es primaria oficial, secundaria, terciaria o una estimación propia. Si no hay fuente primaria se usa la mejor disponible y se aclara.
- **Temas sensibles** (víctimas 1973–1983, homicidios por identidad de género, procesados, suicidios, consumos): cada dato con su aclaración de fuente, nivel y alcance.

## 3. Qué se reutiliza de Datos de Argentina
El sitio que mandaste ya tiene casi todo el mecanismo:
- Un catálogo de indicadores (`indicadores.yaml`, con 303 indicadores y 372 series).
- Descargas automáticas de datos.gob.ar, la API del INDEC, el BCRA, FRED, Our World in Data y otras, más la carga manual en CSV con el enlace de origen.
- IPC empalmado y moneda constante.
- Vistas interanual, de gestión y acumulado de 12 meses.
- Actualización mensual con revisión antes de publicar (GitHub Actions).

Hay unos **100 gráficos de la Radiografía cuyas series ya están en Datos de Argentina**: inflación, EMAE, salarios, recaudación, deuda, reservas, crédito y mora, consumo de carne, confianza UTDT, entre otros. Son el primer lote.

Lo que hay que agregarle al motor:
- Inicio libre por gráfico (no fijo en 2003), frecuencia anual y series largas.
- Tipo de tramo por dato (observado, estimado, interpolado o proyectado) y el símbolo ⚠.
- Tipos de gráfico: áreas apiladas, barras, barras por gobierno, líneas por país y burbujas.
- Franjas de gobierno desde De la Rúa.
- Ficha con el nivel de la fuente y el método.

## 4. Cómo avanzar
Primero un trabajo **horizontal**, que se hace una sola vez: el motor y el prototipo. Después se avanza **por lotes según la fuente de los datos**, no por tema, porque una misma fuente (por ejemplo, el INDEC) sirve para gráficos de muchos temas, y bajarla una vez rinde para todos.

Dentro de cada lote, el trabajo es **vertical**: cada gráfico se termina completo antes de pasar al siguiente. Se trabaja en tandas de 15 a 25 gráficos por sesión.

| Paso | Qué | Gráficos |
| --- | --- | --- |
| 0 | Plan cerrado: revisás Decisión, Fuente para reconstruir y Lote en el Excel | 479 |
| 1 | Motor: copia de Datos de Argentina con las extensiones de arriba, estética y secciones por tema | — |
| 2 | Prototipo: 10 gráficos, uno de cada tipo, para validar diseño, vistas, franjas y fichas | 10 |
| 3 | L1: series que ya están en Datos de Argentina | 98 |
| 4 | L2: oficiales con API o descarga (INDEC, BCRA, Economía, ARCA, SIPA, ANSES, CAMMESA, ENARGAS, Energía) | 115 |
| 5 | L3: oficiales en archivos o informes (DEIS, SNIC, ANSV, DNRPA, SENASA, Educación, censos, presupuesto) | 46 |
| 6 | L4: internacionales y series largas, con las comparaciones entre países como serie completa | 70 |
| 7 | L5: fuentes privadas y académicas (UTDT, UCA, cámaras, mercados, encuestas) | 54 |
| 8 | L6: estimaciones con método y ⚠ | 65 |
| 9 | L7: temas sensibles, con aclaración por dato | 17 |
| 10 | Revisión cruzada, publicación y actualización mensual automática | — |

Además, 14 gráficos son duplicados o variantes y se cierran junto con el gráfico al que remiten.

**Pasos de cada gráfico:**
1. Bajar o cargar el dato con su fuente.
2. Aplicar las transformaciones (deflactar, dividir por población o por PBI, etc.).
3. Marcar los tramos estimados o proyectados.
4. Armar la ficha: qué muestra, fuente, nivel, método y período.
5. Configurar el gráfico, las vistas y los gobiernos.
6. Controlarlo contra el original y contra el último dato disponible.
7. Actualizar el Estado de avance en el Excel.

**Publicación:** el sitio queda en vista previa hasta terminar los pasos 3 a 5, que son la base oficial. Ahí se publica, y los lotes 6 a 9 se suman a medida que se revisan.

## 5. El Excel
`Inventario_graficos_Radiografia.xlsx`:
- **Plan web**: una fila por gráfico. Incluye lote, serie equivalente en Datos de Argentina, gráfico propuesto, período, vistas, gobiernos, fuente y su nivel, reconstrucción, cálculos, tramos, alerta ⚠, tema sensible y estado de avance.
- **Pasos**: los pasos de la tabla de arriba, con conteos automáticos.
- **Resumen, Gobiernos, Fuentes y Diccionario.**
- **Las fichas originales**, en las pestañas del PDF y de los 29 gráficos que no están en él.

La correspondencia con Datos de Argentina y la asignación a lotes son automáticas: se confirman gráfico por gráfico al trabajar cada lote.

## 6. Publicación
Repositorio: github.com/francomartinlopez/radiografiadeargentina (rama main). Se publica en Netlify (`netlify.toml` publica `sitio/public`, sin compilar). Primer commit subido el 6/11: la base copiada de Datos de Argentina con la marca nueva, los gobiernos desde 1999, el plan y el inventario en `docs/`. Siguiente: paso 1 (motor).
