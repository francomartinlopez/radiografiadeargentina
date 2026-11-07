# Radiografía: pendientes, sin fuente y cosas a revisar

Actualizado el 7/11/2026. Inventario: 301 con gráfico, 178 sin fuente, 0 pendientes.

## 1. A revisar o corregir (hechos con datos parciales)

- **Cheques rechazados (p140, p141):** el BCRA publica el % de rechazo sin fondos solo en el Informe Mensual de Pagos Minoristas (PDF) y no está en su API de variables. Datos sueltos encontrados: 1,14% (promedio mar-2019/feb-2020), 6% (mayo 2020), 0,65% (mayo 2021), 0,7% (sep-2022), 2,2% (marzo y abril 2026). Haría falta bajar los ~80 informes mensuales para tener la serie.
- **Encuestas vs. resultados (p387):** no hay promedio de encuestas consolidado; se puede armar a mano elección por elección (2003-2023) si vale la pena.
- **Cartera de las AFJP 2008 (p448):** las cifras no coinciden entre fuentes (títulos públicos 55% a 60%). Falta un boletín de la SAFJP de septiembre/octubre de 2008 para fijarlas.
- **Aprender 6° grado (aprender_primaria):** falta el dato nacional de matemática 2021; 2023 tiene dos versiones (51,4 y 51,5).
- **Parque automotor (vehiculos_por_habitante):** faltan los informes AFAC 2012-2015; 2016 y 2017 están armados sumando el parque de hasta 20 años y el de más de 20.
- **Barrios populares (barrios_populares_region y _decada):** el archivo del RENABAP se bajó de una copia pública en GitHub porque el sitio oficial estaba en mantenimiento. Conviene volver a bajarlo del sitio oficial cuando vuelva, y ver si hay una actualización posterior a dic. 2023.
- **Premios Nobel (nobel_por_pais):** se carga a mano; hay que rehacerlo cada octubre. Criterio: país de nacimiento (Leloir queda en Francia; está aclarado).
- **Femicidios:** la serie arranca en 2017; el dato de 2014 está solo en la nota.
- **Hogares por tramo de ingreso (p157):** se podría hacer procesando microdatos de la EPH (trabajo largo).
- **Organismos sin cobertura en el original de p39/p100 (Lecaps, boncaps y simultáneas):** sin serie pública consolidada.
- **Funcionarios procesados/condenados (p396):** eliminado por decisión tuya.
- **Tasas sobre el parque automotor:** hechas como total (robos_por_vehiculo y siniestros_por_vehiculo). Por tipo de vehículo (p265, p267, p268, p270, p272-p274) no hay datos públicos.
- **Mortalidad de 5 a 17 años (p341):** marcada sin fuente, pero ya existe el gráfico mortalidad_5_19 (Banco Mundial, 5 a 19 años). Revisar si se la da por resuelta.

- **Pasivos remunerados del BCRA (base_y_pasivos_bcra, pasivos_sobre_base):** la serie del balance del BCRA en datos.gob.ar se cortó en octubre de 2025. La API del BCRA mide los pases con otro criterio (da cero desde noviembre de 2025), así que no sirve para continuarla; queda esperar que vuelva a publicarse o buscar el balance semanal en la web del BCRA.
- **Seguro de desempleo y AUE:** sin datos publicados después de septiembre de 2025 (la AUH ya se extendió con el Boletín Mensual de ANSES).
- **Combustibles y petróleo:** desde diciembre de 2025 se estiman con las ventas de las cuatro grandes y con el índice de petróleo del INDEC; volver a la tabla oficial si la Secretaría de Energía la retoma.

## 2. Pendientes de hacer

- Ninguna ficha pendiente. Lo que se podría sumar más adelante:
  - **Leyes del oficialismo, todas las votaciones (p388, p391):** requiere procesar todas las actas nominales de Diputados y del Senado desde 2001 y clasificar qué proyectos son del oficialismo.
  - **Leyes clave (p389, p390):** faltan la Emergencia Económica de 2002, el canje de deuda de 2005 y el resultado completo de Magistratura 2006 en Diputados; no aparecen en la prensa digital ni en fuentes abiertas consultadas (habría que ver las actas en el archivo del Congreso).

## 3. Sin fuente (no se publican)

Motivo de cada una, por tema. Si conseguís una fuente para alguna, se puede retomar.

### Actividad económica, PBI y estructura productiva

- **p7** — PIB per capita regional: PIB per cápita por región: no hay PBG provincial oficial homogéneo y actualizado.
- **p9** — Actividad industrial por provincia y gobierno: Actividad industrial por provincia: no hay índice oficial provincial homogéneo.
- **p10** — Actividad económica neta por provincia de Milei del inicio a abril 2026: Actividad neta por provincia: no hay PBG provincial mensual oficial.
- **p12** — Ventas manufactureras internas pesos abril 2026 por sector: Ventas manufactureras por sector en pesos: datos ilustrativos.
- **p13** — Ventas manufactureras importadas pesos 2026 por sector: Ídem p12.
- **p14** — Ventas comerciales pesos 2026 por sector: Ventas comerciales por sector en pesos: no hay serie oficial; ver EMAE por sector e industria_por_sector.
- **p15** — Ventas primarios por sector pesos 2026: Ídem p14.
- **p16** — Ventas servicios por sector pesos abril 2026: Ídem p14.
- **p21** — Matriz de costos y ganancias de las empresas industriales en pesos constantes: Matriz de costos y ganancias: ilustrativa.

### Inflación, dinero y política monetaria

- **p35** — Inflación IPC publicada vs resultados si se hubieran aplicado cambios de la estructura basada en la nueva metodología: IPC contrafáctico con otra canasta: estimación propia.
- **p39** — Base monetaria amplia, pasivos remunerados, lecaps, boncaps, simultáneas/repos de BYMA y deuda: Lecaps, boncaps y simultáneas como agregado: datos ilustrativos sin serie pública consolidada.
- **p43** — Costo promedio de m3 de gas de red domiciliaria, comercial e industrial en argentina y EEUU: Tarifas de gas por categoría: series históricas y proyectadas sin fuente consolidada.

### Fiscal, deuda, impuestos y RIGI

- **p58** — Ingresos de impuestos municipales y comunales en pesos constantes: No hay serie nacional consolidada de recaudación municipal.
- **p62** — Resultado fiscal y superávit real al incluir la deuda futura: Resultado “con deuda futura” es una construcción propia sin base oficial.
- **p79** — Deuda social infancia UCA: UCA-ODSA no publica series abiertas; el original usaba valores ilustrativos y proyecciones.
- **p80** — Deuda social personas mayores UCA: Ídem p79.
- **p82** — Monto en pesos constantes de prestamos a funcionarios públicos del banco nacional: Préstamos a funcionarios del Banco Nación: datos ilustrativos, sin fuente pública.
- **p92** — Invap: INVAP es sociedad del Estado de Río Negro: no figura como servicio en el presupuesto nacional; los contratos no se publican como serie.
- **p93** — 7 organismos e institutos: Organismos sin identificar en el original; los organismos con fuente están en los gráficos de presupuesto.
- **p95** — Instituto de prevención sísmica: INPRES no es un servicio administrativo financiero: su gasto queda dentro de un ministerio y no se puede separar en la base por servicio.
- **p100** — Lo anterior más deuda en pesos corrientes: Igual que p39: sin serie pública consolidada.
- **p102** — Ingresos por impuestos y retenciones a provincias y al estado nacional de empresas extranjeras: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p103** — Carga fiscal efectiva total por empresa como porcentaje de la facturación industrial argentina: Carga fiscal por empresa sobre facturación: estimación propia sin base oficial.

### Sector externo, divisas y mercado cambiario

- **p110** — Valor total inversión afjp dólares constantes y número de jubilados sin moratoria real y estima: Valor AFJP y jubilados sin moratoria: construcción ilustrativa.
- **p120** — Compra dólares empresas: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p121** — Venta dólares empresas: Igual que p120: datos ilustrativos.
- **p122** — Venta dólares individuos: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p125** — Reservas de petróleo de urgencia por país: Reservas estratégicas de petróleo por país: estimaciones mixtas sin serie homogénea.
- **p126** — Reservas de gas de emergencia por país: Ídem p125 para gas.
- **p127** — Contrabando de importaciones: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p130** — Produccion agropecuaria en dólares constantes de mayo del 2026 por tipo y rango de hectáreas: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p132** — Productividad en dolares por hora de uso de maquinaria en. Argentina, china y Vietnam: Productividad por hora de máquina: no hay estadística de horas-máquina.

### Crédito, mora y sistema financiero

- **p140** — Cheques y pagarés rechazados y no pagados: El BCRA publica el rechazo de cheques sin fondos sobre el total compensado solo en el Informe Mensual de Pagos Minoristas (PDF); su nueva web no ofrece la serie descargable. Revisar más adelante.
- **p141** — Cheques y pagarés rechazados y no pagados pesos abril 2026: Ídem p140.
- **p142** — Préstamos otorgado a funcionarios públicos banco nación cantidad: Ídem p82.
- **p143** — Mismo de monto total créditos banco nacion a funcionarios: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p148** — Tasas interés préstamos personales uva 24 meses: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p150** — Tasa interés prestamos hipotecarios uva: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p153** — Ganancias reales bancos, agentes de bolsa y seguros: Ganancias reales por sector: estimaciones propias sin serie oficial.

### Empleo, salarios e ingresos

- **p157** — Cantidad de hogares por ingresos: Hogares por tramo de ingreso en pesos constantes requiere procesar microdatos de la EPH; se cubre con ingreso_por_estrato.
- **p159** — Empleo informal por sector: Informalidad por sector: datos simulados en el original; ver empleo_informalidad.
- **p169** — Personas en edad económicamente activa sin discapacidad sobre la PEA que viven con sus padres: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p170** — Juicios por cese de actividad sobre el total de despidos y terminaciones voluntarias: No hay serie pública de juicios laborales por despido a nivel nacional (cada poder judicial provincial publica distinto); la SRT solo publica juicios por accidentes de trabajo.
- **p171** — Juicios de empleados en actividad sobre total de empleados: Igual que p170: no hay serie nacional de juicios laborales.
- **p172** — Porcentaje de trabajadores con más de un empleo: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.

### Empresas y tejido productivo

- **p180** — Rentabilidad empresas transporte larga distancia: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p181** — Compras a empresas locales y puestos laborales indirectos generados por empresas extranjeras de sectores extractivos: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p182** — Puestos laborales directos de empresas extranjeras en minería y energia: El empleo por origen del capital de la empresa no se publica. El empleo total del sector está en asalariados por rama (minería y petróleo, SIPA).
- **p183** — Venta de sembradoras por empresas: Ventas de sembradoras por empresa: sin desagregación pública.
- **p184** — Ganancias reales comercio, servicios no financieros e industria: Ídem p153.
- **p185** — Ganancia real construcción, servicios no financieros, comercio e industria: Ídem p153.
- **p186** — Ganancia sector primario: Ídem p153.
- **p187** — Ganancias servicios sociales no concesionados: Ídem p153.
- **p188** — Ganancias servicios concesionados: Ídem p153.
- **p189** — Ganancias servicios concesionados de transporte: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p190** — Efectividad global del equipo como disponibilidad y eficiencia industrial de empresas argentinas: OEE país: no existe serie oficial.
- **p191** — Uso de plc y dcs en empresas industriales argentina, china y Vietnam: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p192** — Uso de sas, sistemas propios o erp de empresas industriales en argentina, china y Vietnam: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p193** — Uso de inteligencia artificial en empresas industriales china, argentina y Vietnam: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.

### Agro, ganadería y clima

- **p194** — Rentabilidad del campo: Rentabilidad del campo: márgenes modelados, sin serie oficial.
- **p202** — Rentabilidad de la ganadería por tipo de carne en pesos constantes: Rentabilidad ganadera: estimación propia.
- **p211** — Venta sembradoras: Venta de sembradoras: datos estimados; las ventas oficiales están en maquinaria_agricola.
- **p212** — Precio, ancho y precio por metro de ancho de sembradoras: Precios de sembradoras por modelo econométrico.
- **p215** — Porcentaje de tipo de productores agropecuarios por rango de cantidad de hectáreas por producto: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p217** — Cantidad de hectáreas de uso agropecuario por rango de hectáreas por productor: Basado en un censo inexistente (2004) y proyección 2025.
- **p218** — Cantidad de hectáreas agropecuarias por tipo de uso: Usos del suelo proyectados sin fuente.
- **p219** — Rentabilidad por uso agropecuario y rango de hectáreas por productor: Rentabilidad por escala: estimación propia.
- **p220** — Produccion agropecuaria por tipo y rango de hectáreas del productor en kilos: Producción por escala: estimación propia.
- **p221** — Anchos de las sembradoras nuevas por marca en argentina: Anchos de sembradoras por marca: catálogos, no estadística.
- **p222** — Precio arrendamientos rurales: Fuentes ficticias en el original.
- **p224** — Cabezas de ganado perdidas por sequía y exceso de lluvia e inundaciones: Pérdidas de ganado por clima: sin fuente especificada.
- **p226** — Probabilidad niño y super niño: Pronósticos de probabilidad ENSO cambian cada mes; no se archivan como serie.
- **p227** — Probabilidad niño y super niño: Pérdidas de granos por sequía/inundación con datos ilustrativos; no hay serie oficial consolidada.
- **p228** — Pérdidas agrícolas toneladas y porcentaje sequía e inundaciones y lluvias: Igual que p227: sin serie oficial consolidada.
- **p229** — Pérdidas agrícolas y el niño y la niña: Pérdidas agrícolas por ENSO: ilustrativo.
- **p230** — Pérdidas ganaderas y el niño y la niña: Ídem p229.
- **p231** — Siembra cosecha y faena animales ganadería agrícola agropecuarios y niño niña neutral clima: Calendario agropecuario ilustrativo.

### Energía, hidrocarburos y servicios

- **p246** — Comparativa histórica por países de población con acceso a gas natural de red domiciliaria en su horgar: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p247** — Porcentaje del consumo eléctrico de conexiones ilegales según CAMMESA (pérdidas no técnicas): CAMMESA no publica la proporción de consumo por conexiones ilegales.
- **p248** — Costo promedio electricidad residencial, comercial e industrial en argentina y EEUU: Tarifas eléctricas comparadas: estimaciones mixtas EIA/ENRE sin serie homogénea.
- **p249** — Costo promedio litro de agua de red residencial, comercial e industrial argentina y EEUU en pesos constantes: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p250** — Empleo generado por energía y minería en general: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.

### Vehículos, transporte y seguridad vial

- **p253** — Vehículos transporte y carga: La DNRPA no separa transporte y carga dentro de automotores en su serie abierta.
- **p255** — Países autos: Comparación de autos por país sin fuente identificada.
- **p256** — Autos usados, gama alta, media y baja como porcentaje del parque automotor: DNRPA no publica ventas por gama ni el parque; ver autos_0km_usados.
- **p257** — Autos nuevos gama alta, media y baja como porcentaje del total del parque automotor: Ídem p256; ver autos_0km_usados.
- **p258** — Motos usadas, gama alta, media y baja como porcentaje del parque: Sin gama ni parque de motos; ver motos_0km_usadas.
- **p259** — Motos gama alta, media y baja nuevas como porcentaje del parque: Ídem p258; ver motos_0km_usadas.
- **p260** — Venta camiones usados, nuevos gama alta, media y baja como porcentaje del parque: Sin apertura de camiones ni parque; ver autos_0km_usados.
- **p261** — Camiones nuevos por gama como porcentaje del parque: Sin datos por gama ni parque.
- **p262** — Venta de utilitarios por usados y nuevos por gama como porcentaje del parque: Sin apertura de utilitarios ni parque; ver autos_0km_usados.
- **p263** — Utilitarios nuevos por gama como porcentaje del parque: Ídem p261.
- **p265** — Robo motos sobre parque de motos: No hay base pública de robos de motos; ver robos_autos para automotores.
- **p266** — Robo automóviles como porcentaje del parque: Robos totales/parciales y parque no publicados; ver robos_autos.
- **p267** — Robo vehículos pesados sobre el parque: Ídem; ver robos_autos.
- **p268** — Robo vehículos utilitarios sobre el parque: Ídem; ver robos_autos.
- **p269** — Vehículos involucrados en accidentes como porcentaje del parque automotor: Sin parque automotor publicado para calcular la tasa.
- **p270** — Camiones accidentados sobre parque de camiones: Ídem p269.
- **p271** — Accidentes con fallecidos, solo heridos, ni fallecidos ni heridos sobre el total del parque automotor: Ídem p269.
- **p272** — Accidentes en moto sobre parque de motos: Ídem p269.
- **p273** — Accidentes en autos sobre parque: Ídem p269.
- **p274** — Accidentes vehículos utilitarios sobre parque: Ídem p269.
- **p278** — Motos por habitante: No hay serie pública del parque de motos en circulación (AFAC no las incluye; DNRPA solo publica trámites).
- **p284** — Gráfico tracción humana y animal total: Tracción a sangre: estimaciones informales.
- **p285** — Tracción a sangre humana y animal ponderada por población: Ídem p284.
- **p289** — Comparativa histórica por países de autos particulares cada 1000 habitantes: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p290** — Comparativa histórica por países de kilómetros de rutas y autopistas por habitante: Rutas por país en serie histórica: estimación propia.
- **p291** — Siniestros viales de conductores alcoholizados sobre el parque automotor total: Siniestros con alcohol sobre parque: sin parque ni serie ANSV abierta.
- **p292** — Multas por conducir alcoholizado sobre parque automotor: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p293** — Accidentes viales por causa: Accidentes por causa: estimación propia.
- **p294** — Accidentes viales con fallecidos por causa: Ídem p293.
- **p295** — Accidentes viales por causa sin fallecidos con heridos graves: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p296** — Accidentes viales con heridos leves por causa sin fallecidos ni heridos graves: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p297** — Accidentes viales sin fallecidos ni heridos, solo daños materiales por causa: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p298** — Costo promedio en pesos constantes de seguro automotor contra todo riesgo y contra terceros: Costo del seguro automotor: estimación ilustrativa.

### Comercio, consumo y bienes

- **p299** — Inmuebles comerciales vacíos o en alquiler: Locales vacíos: relevamientos parciales sin serie nacional.
- **p306** — Ventas electrodomésticos pesos abril 2026: Ventas de electrodomésticos en pesos: estimación.
- **p309** — Apuestas online, en casinos legales y juegos clandestinos en pesos constantes de abril 2026: Apuestas legales y clandestinas: estimaciones de consultoras sin serie oficial consolidada.
- **p311** — Personas sobre el total que apuestan y que tienen ludopatía: Apuestas online y ludopatía: sin serie oficial nacional periódica.

### Demografía, migración y religión

- **p312** — Población menores de 18 años, mayores por clase de empleo y jubilados y pensionados: Población por clase de empleo y jubilados: cálculo propio sin serie publicada.
- **p313** — Mismo por cantidades: Igual que p312.
- **p316** — Abortos sobre embarazos: Solo hay conteos de IVE/ILE del sector público desde 2021, con cifras revisadas y dispares (59.348 a 73.487 en 2021); no existe un dato oficial de abortos sobre embarazos.
- **p320** — Migración (emigración o re inmigración repatriación) de argentinos: Emigración de argentinos (salida/regreso) sin serie oficial; ver migracion_neta.
- **p321** — Migración de argentinos con titulo universitario completo: Migración por nivel educativo: datos ilustrativos.
- **p322** — Migración neta argentinos sin titulo universitario completo: Ídem p321.
- **p327** — Migración interna neta por regiones: Migración interna neta por región: estimación sin serie oficial.

### Pobreza, condiciones sociales y planes

- **p331** — Mercado de trabajo UCA: Ídem p79.
- **p332** — Bienestar subjetivo UCA: Igual que p331 (UCA sin serie abierta).
- **p336** — Malnutrición y desnutrición total: Malnutrición/desnutrición como % de la población: solo mediciones aisladas (ENNyS 2005 y 2018-19) con poblaciones distintas.
- **p337** — Malnutrición y desnutrición menores de edad: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.

### Salud y enfermedad

- **p341** — Tasa mortalidad 5 a 17 años: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p342** — Porcentaje población por rango etario que usa preservativo en sexo fuera de relación estable: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.

### Salud mental, suicidio y adicciones

- **p354** — Intentos de suicidio y suicidios: Intentos de suicidio notificados al SNVS desde 2023: solo en informes, sin serie abierta.

### Educación y cultura

- **p358** — Deserción por nivel educativo en porcentaje de alumnos: Deserción por nivel: estimación sin serie publicada comparable.
- **p361** — Asistentes a espectáculos y recitales de origen nacional en argentina: Asistencia a espectáculos: estimación.
- **p362** — Costo promedio etrada a espectáculos you recitales nacionales: Ídem p361.
- **p363** — Costo entrada promedio espectáculos y recitales extranjeros: Ídem p361.
- **p364** — Cantidad asistentes a espectáculos y recitales extranjeros: Asistentes a espectáculos: estimación.
- **p365** — Asistentes porcentaje población mayor de 18 espectáculos y recitales extranjeros: Ídem p361.
- **p366** — Asistentes población mayor 18 años a recitales y espectáculos nacionales: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p368** — Lectura libros semanal 10 a 80 años: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p369** — Uso pantallas más de una hora diaria por grupo etario fuera del trabajo o ámbito educativo: Uso de pantallas: curvas logísticas propias.

### Vivienda y servicios del hogar

- **p377** — Países casas formales: Casas formales por país sin fuente.
- **p378** — Ingreso y alquiler promedio 2 dormitorios: Alquiler de 2 dormitorios: relevamientos privados sin serie abierta nacional.

### Política, instituciones y opinión pública

- **p388 / p391** — Leyes oficialistas, todas las votaciones: ver sección 2.
- **p387** — Promedio encuestas y resultado electoral real primera y segunda fuerza presidenciales: No hay un promedio de encuestas consolidado y público para 2003-2023; los resultados oficiales sí existen (DINE). Podría armarse a mano con las encuestas de cada elección.
- **p392** — Audiencia televisiva por gobierno: Audiencias por gobierno: sin serie pública (Kantar IBOPE es paga).
- **p393** — Audiencia radios por gobierno: Ídem p392.
- **p394** — Audiencia diarios por gobierno: Ídem p392.
- **p395** — Audiencia digital por gobierno: Audiencia digital por gobierno: estimativa.
- **p396** — Funcionarios nacionales procesados y condenados por gobierno: Eliminada por decisión del autor: no existe registro oficial unificado de funcionarios procesados y condenados.
- **p398** — Evolución audiencia por tipo de medio por gobierno: Ídem p392.
- **p399** — Intención de voto promedio encuestas: Promedio de encuestas: sin fuente consolidada.

### Comparativas internacionales y casos de crisis

- **p406** — Despidos y no contrataciones por sector en el mundo por inteligencia artificial en miles de puestos: Despidos por IA en el mundo: sin fuente.
- **p414** — Comparativa países jubilación: Comparación de jubilaciones por país sin fuente identificada.
- **p429** — Costo laboral promedio industrial en argentina, china y Vietnam: Costo laboral comparado con datos ilustrativos.
- **p430** — Inversión en tecnología y bienes de capital por empresa industrial en china, argentina y Vietnam: Inversión por empresa: estimación propia.
- **p431** — Productividad industrial sobre inversiones por empresa en argentina, china y Vietnam: Productividad sobre inversión por empresa: elaboración propia.
- **p432** — Tasa de error humano industrial argentina, china y Vietnam: Tasa de error humano: no existen estadísticas comparables.
- **p433** — Tiempo de ciclo por empresa industrial de la maquinaria en china, argentina y Vietnam: Tiempo de ciclo: sin fuente.
- **p434** — Sensores y actuadores promedio por empresa industrial argentina, china y Vietnam: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p435** — Uso por empresa de sistemas scada/hmi industrial argentina, china Vietnam: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p436** — Uso por empresa de sistemas mes industrias argentina, china y Vietnam: Uso de sistemas MES: estimación propia.
- **p437** — Piezas defectuosos sobre el total industrial argentina, china y Vietnam: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **p438** — Costo laboral como porcentaje de la facturación industrial argentina, china y Vietnam: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.

### Criminalidad, violencia de género y homicidios

- **p442** — Asesinatos por genero con mujeres trans nacidos hombres biológicos: No hay registro oficial de población trans que permita tasas; los conteos de organizaciones no son comparables.

### Sistema previsional y AFJP

- **p447** — Estatizacion de las afjp e índice de bonos del estado nacional argentino (55% de la cartera): Índice de bonos IAMC no disponible como serie abierta.
- **p448** — Inversión afjp 2008: Las cifras publicadas de la cartera de las AFJP antes de la estatización no coinciden entre fuentes (títulos públicos 55% a 60% según la fecha); sin acceso a los boletines de la SAFJP para verificarlas.

### Sin tema (imágenes fuera del PDF)

- **c1023** — Rentabilidad del campo: Texto, no dato.
- **c1024** — Rentabilidad del campo: Texto, no dato.
- **c1137** — Tracción a sangre / recolectores (estimación analítica): Ídem p284.
- **c1301** — Consumo drogas en pesos abril 2026: Gasto en drogas sin fuente oficial.
- **c1316** — Personas con deficit de atención médica o o porcentaje de cada grupo de discapacidad, enfermedades crónicas, enfermedades congénitas, niños y adultos mayores: Déficit de atención médica por grupo: sin fuente.
- **c1325** — Gasto farmacia e ingreso promedio por hogar pesos abril 2026: El gasto en farmacia solo se mide en la ENGHo (2004/05 y 2017/18); no hay serie mensual.
- **c1407** — Genero del asesino de mujeres transexuales nacidas hombres biológicos: Ídem p442: sin estadística oficial del agresor ni población de referencia.
- **c1461** — Multas por conducir alcoholizado sobre cantidad de personas con carnet de conductor: Igual que p292.
- **c1463** — Personas con carnet de conductor sobre población de 18 años o mas: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **c1464** — Personas con carnet de conductor sobre parque automotor: Paso 8: el original usa datos simulados o ilustrativos y no hay una fuente pública sobre la cual estimar; no se publica.
- **c1553** — Procesos automatizados industriales china, argentina y Vietnam: Procesos automatizados: sin fuente.
- **c1557** — Robotizacion industrial por empresa en argentina, china y Vietnam: La IFR no publica densidad de robots para Argentina ni Vietnam en abierto (World Robotics es pago).
