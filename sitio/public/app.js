"use strict";

/* Radiografía de la Argentina: dibuja cada gráfico a partir de su JSON (series en nivel).
   Las medidas (variación, interanual, acumulado de 12 meses, base 100) se calculan acá. */

const DATOS = "datos/";
const COLORES = ["--s1", "--s2", "--s3", "--s4", "--s5", "--s6", "--s7", "--s8"];
const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const MESES_LARGO = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
const NIVELES = { primaria: "Primaria", secundaria: "Secundaria", terciaria: "Terciaria", estimacion: "Estimación" };
const TRAMOS = { estimado: "estimado", interpolado: "interpolado", proyectado: "proyectado" };
let META = null; // radiografia.json: temas, gobiernos, base del último mandato

/* ---------- Utilidades ---------- */

const nf = (dec) => new Intl.NumberFormat("es-AR", { minimumFractionDigits: dec, maximumFractionDigits: dec });
const fmt = (v, dec = 1) => (v == null || !isFinite(v) ? "s/d" : nf(dec).format(v));
const signo = (v, dec = 1) => (v == null || !isFinite(v) ? "s/d" : (v > 0 ? "+" : v < 0 ? "−" : "") + nf(dec).format(Math.abs(v)));
const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const el = (tag, attrs = {}, ...hijos) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k === "text") e.textContent = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) e.setAttribute(k, v);
  }
  for (const h of hijos) if (h != null && h !== false) e.append(h);
  return e;
};
const fecha = (s) => { const [y, m, d] = s.split("-").map(Number); const x = new Date(2000, (m || 1) - 1, d || 1); x.setFullYear(y); return x; };
const normalizar = (t) => (t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

function periodo(f, frecuencia) {
  const d = fecha(f);
  if (frecuencia === "T") return `${["I", "II", "III", "IV"][Math.floor(d.getMonth() / 3)]} trim. ${d.getFullYear()}`;
  if (frecuencia === "S") return `${d.getMonth() < 6 ? "1.er" : "2.º"} sem. ${d.getFullYear()}`;
  if (frecuencia === "A") return String(d.getFullYear());
  return `${MESES_LARGO[d.getMonth()]} ${d.getFullYear()}`;
}
function mesAnio(s) { if (!s) return ""; const [y, m] = s.split("-"); return m ? `${MESES[+m - 1]} ${y}` : y; }

// Magnitud para montos ("millones de pesos de hoy" con valores de millones -> billones)
function magnitud(unidad, maxAbs) {
  const m = (unidad || "").match(/^millones de (.*)$/);
  if (!m) return { div: 1, unidad };
  if (maxAbs >= 1e6) return { div: 1e6, unidad: `billones de ${m[1]}` };
  if (maxAbs >= 1e3) return { div: 1e3, unidad: `miles de millones de ${m[1]}` };
  return { div: 1, unidad };
}
const decimales = (v) => { const a = Math.abs(v); return a >= 100 ? 0 : a >= 10 ? 1 : 2; };
const esDiferencia = (g) => g.tipo_valor === "tasa" || g.tipo_valor === "saldo";
function sufijoDif(g) { if (/%/.test(g.unidad)) return " pp"; if (g.unidad === "puntos básicos") return " pb"; return ""; }

/* ---------- Medidas ---------- */

const MEDIDAS = {
  nivel: "Nivel",
  variacion: "Variación",
  interanual: "Interanual",
  acumulado_12m: "Acumulado 12 meses",
  base_100: "Base 100 al inicio",
};
function medidasDisponibles(g) {
  const lista = ["nivel", "variacion"];
  if (g.frecuencia !== "A") lista.push("interanual");
  if (g.flujo && (g.frecuencia === "M" || g.frecuencia === "T")) lista.push("acumulado_12m");
  if (!esDiferencia(g)) lista.push("base_100");
  return g.medidas ? lista.filter(m => g.medidas.includes(m)) : lista;
}
function nombreVariacion(g) {
  return { M: "mensual", T: "trimestral", S: "semestral", A: "anual" }[g.frecuencia] || "";
}
function textoMedida(g, medida) {
  const dif = esDiferencia(g);
  switch (medida) {
    case "nivel": return "Nivel de la serie.";
    case "variacion": return dif ? `Diferencia ${nombreVariacion(g)} (contra el período anterior).` : `Variación % ${nombreVariacion(g)} (contra el período anterior).`;
    case "interanual": return dif ? "Diferencia contra el mismo período del año anterior." : "Variación % contra el mismo período del año anterior.";
    case "acumulado_12m": return g.frecuencia === "T" ? "Suma de los últimos 4 trimestres." : "Suma de los últimos 12 meses.";
    case "base_100": return "Índice: primer dato del período elegido = 100.";
  }
}

// puntos: [{t (Date), v, tramo}] ordenados. Devuelve la medida pedida.
function aplicarMedida(puntos, medida, g) {
  const dif = esDiferencia(g);
  const cambio = (a, b) => (dif ? a - b : b === 0 ? null : (a / b - 1) * 100);
  if (medida === "variacion") {
    return puntos.slice(1).map((p, i) => ({ ...p, v: cambio(p.v, puntos[i].v), tramo: p.tramo || puntos[i].tramo }));
  }
  if (medida === "interanual") {
    const porMes = new Map(puntos.map((p) => [p.t.getFullYear() * 12 + p.t.getMonth(), p]));
    return puntos.map((p) => {
      const ant = porMes.get(p.t.getFullYear() * 12 + p.t.getMonth() - 12);
      return ant ? { ...p, v: cambio(p.v, ant.v), tramo: p.tramo || ant.tramo } : null;
    }).filter(Boolean);
  }
  if (medida === "acumulado_12m") {
    const n = g.frecuencia === "T" ? 4 : 12, salida = [];
    for (let i = n - 1; i < puntos.length; i++) {
      const ventana = puntos.slice(i - n + 1, i + 1);
      const meses = (ventana[n - 1].t.getFullYear() - ventana[0].t.getFullYear()) * 12 + ventana[n - 1].t.getMonth() - ventana[0].t.getMonth();
      if (meses !== (g.frecuencia === "T" ? 9 : 11)) continue; // ventana incompleta
      salida.push({ ...puntos[i], v: ventana.reduce((s, p) => s + p.v, 0), tramo: ventana.find((p) => p.tramo)?.tramo || null });
    }
    return salida;
  }
  return puntos.map((p) => ({ ...p }));
}

// Recorta al período y, en base 100, indexa al primer dato visible
function recortar(puntos, desde, medida, g) {
  let r = puntos.filter((p) => p.v != null && isFinite(p.v) && +p.t >= +desde);
  if (medida === "base_100" && r.length) {
    const b = r[0].v;
    r = b ? r.map((p) => ({ ...p, v: (p.v / b) * 100 })) : [];
  }
  return r;
}

/* ---------- Preparación de un gráfico ---------- */

function colorSerie(s, i) {
  if (s.color === "gris") return css("--gris-serie");
  if (s.color && s.color.startsWith("#")) return s.color;
  return css(COLORES[i % COLORES.length]);
}

function prepararTemporal(g, estado) {
  const desdePeriodo = estado.periodo === "mandato" ? fecha(META.base_ultimo_mandato) : fecha(g.desde);
  let ci = 0;
  const series = g.series.map((s) => {
    const puntos = s.puntos.map((p) => ({ t: fecha(p[0]), v: p[1], tramo: p[2] || null }));
    const color = colorSerie(s, s.color === "gris" ? 0 : ci++);
    let medidos = aplicarMedida(puntos, estado.medida, g);
    // en nivel y base 100, el último mandato arranca en el mes previo a asumir
    const desde = estado.periodo === "mandato" && (estado.medida === "nivel" || estado.medida === "base_100" || estado.medida === "acumulado_12m")
      ? desdePeriodo : estado.periodo === "mandato" ? new Date(desdePeriodo.getFullYear(), desdePeriodo.getMonth() + 1, 1) : desdePeriodo;
    return { nombre: s.nombre, color, puntos: recortar(medidos, desde, estado.medida, g), grueso: s.color !== "gris" };
  }).filter((s) => s.puntos.length);
  const enPorcentaje = !esDiferencia(g) && (estado.medida === "variacion" || estado.medida === "interanual");
  const enDif = esDiferencia(g) && (estado.medida === "variacion" || estado.medida === "interanual");
  const maxAbs = Math.max(0, ...series.flatMap((s) => s.puntos.map((p) => Math.abs(p.v))));
  let formato;
  if (enPorcentaje) {
    formato = { eje: (y) => fmt(y, maxAbs < 10 ? 1 : 0) + "%", tip: (y) => signo(y, 1) + "%", unidadEje: "" };
  } else if (estado.medida === "base_100") {
    formato = { eje: (y) => fmt(y, 0), tip: (y) => fmt(y, 1), unidadEje: "base 100" };
  } else {
    const mg = magnitud(g.unidad, maxAbs), suf = enDif ? sufijoDif(g) : "", dec = decimales(maxAbs / mg.div);
    formato = {
      eje: (y) => fmt(y / mg.div, Math.max(0, dec - 1)) + suf,
      tip: (y) => (enDif ? signo(y / mg.div, dec) : fmt(y / mg.div, dec)) + suf,
      unidadEje: enDif ? "" : mg.unidad,
    };
  }
  const referencia = enPorcentaje || enDif || g.tipo_valor === "saldo" ? 0 : estado.medida === "base_100" ? 100 : null;
  const apilar = g.tipo === "areas" && ["nivel", "acumulado_12m"].includes(estado.medida);
  const barras = g.tipo === "barras";
  const colorSigno = barras && esDiferencia(g) && series.length === 1;
  const log = estado.log && series.every((s) => s.puntos.every((p) => p.v > 0));
  return { series, ...formato, referencia: log ? null : referencia, tipoX: "fecha", apilar, barras, colorSigno, log, frecuencia: g.frecuencia,
           bandas: g.gobiernos && estado.gobiernos };
}

function prepararCategorias(g) {
  const cats = g.categorias || [];
  const nombresSerie = [...new Set(cats.map((c) => c.serie || g.titulo))];
  const categorias = [...new Set(cats.map((c) => c.categoria))];
  const maxAbs = Math.max(0, ...cats.map((c) => Math.abs(c.valor || 0)));
  const mg = magnitud(g.unidad, maxAbs), dec = decimales(maxAbs / mg.div);
  const pct = /^%/.test(g.unidad || "");
  return {
    categorias, series: nombresSerie.map((n, i) => ({ nombre: n, color: css(COLORES[i % COLORES.length]),
      valores: categorias.map((c) => cats.find((x) => x.categoria === c && (x.serie || g.titulo) === n) || null) })),
    eje: (y) => fmt(y / mg.div, Math.max(0, dec - 1)) + (pct ? "%" : ""),
    tip: (y) => fmt(y / mg.div, dec) + (pct ? "%" : ""),
    unidadEje: pct ? "" : mg.unidad,
  };
}

/* ---------- Dibujo (SVG) ---------- */

const NS = "http://www.w3.org/2000/svg";
const svgEl = (tag, attrs = {}) => { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); return e; };

function ticksLindos(min, max, n = 5) {
  if (min === max) { min -= 1; max += 1; }
  const paso0 = (max - min) / n, pot = Math.pow(10, Math.floor(Math.log10(paso0)));
  const paso = [1, 2, 2.5, 5, 10].map((m) => m * pot).find((p) => p >= paso0);
  const ini = Math.floor(min / paso) * paso, fin = Math.ceil(max / paso) * paso, t = [];
  for (let v = ini; v <= fin + paso / 2; v += paso) t.push(+v.toFixed(10));
  return t;
}

function ticksLog(min, max) {
  const t = [];
  for (let e = Math.floor(Math.log10(min)); e <= Math.ceil(Math.log10(max)); e++)
    for (const k of [1, 2, 5]) { const v = k * Math.pow(10, e); if (v >= min / 2.01 && v <= max * 2.01) t.push(v); }
  return t.length >= 2 ? t : ticksLindos(min, max);
}

function ticksFecha(x0, x1) {
  const a0 = new Date(x0).getFullYear(), a1 = new Date(x1).getFullYear(), span = a1 - a0, t = [];
  if (span < 3) {
    for (let d = new Date(new Date(x0).getFullYear(), new Date(x0).getMonth(), 1); +d <= x1; d.setMonth(d.getMonth() + 1))
      if (d.getMonth() % 6 === 0) t.push([+d, `${MESES[d.getMonth()]} ${String(d.getFullYear()).slice(2)}`]);
    return t;
  }
  const paso = [1, 2, 4, 5, 10, 20, 25, 50].find((p) => span / p <= 8) || 50;
  for (let a = Math.ceil(a0 / paso) * paso; a <= a1; a += paso) { const d = fecha(`${a}-01-01`); if (+d >= x0) t.push([+d, String(a)]); }
  return t;
}

function dibujarGobiernos(svg, X, x0, x1, m, H) {
  const gobs = META.gobiernos;
  gobs.forEach((gob, i) => {
    const a = Math.max(+fecha(gob.desde), x0);
    const b = Math.min(i + 1 < gobs.length ? +fecha(gobs[i + 1].desde) : x1, x1);
    if (b <= a) return;
    if (i % 2 === 0) svg.append(svgEl("rect", { class: "banda", x: X(a), y: m.t, width: Math.max(0, X(b) - X(a)), height: H - m.t - m.b }));
    if (+fecha(gob.desde) >= x0) svg.append(svgEl("line", { class: "gob-linea", x1: X(a), x2: X(a), y1: m.t, y2: H - m.b }));
    if (X(b) - X(a) > 36) {
      const t = svgEl("text", { class: "banda-txt", x: X(a) + 3, y: m.t + 10 });
      t.textContent = gob.corto;
      svg.append(t);
    }
  });
}

function dibujarTemporal(contenedor, cfg) {
  contenedor.innerHTML = "";
  if (!cfg.series.length) { contenedor.append(el("p", { class: "leyenda-vista", text: "Sin datos para esta vista." })); return; }
  const W = contenedor.clientWidth || 440, H = contenedor.clientHeight || 260;
  const m = { t: cfg.unidadEje ? 26 : 16, r: 12, b: 24, l: 50 };
  // valores apilados
  let series = cfg.series;
  if (cfg.apilar) {
    const acum = new Map();
    series = series.map((s) => ({ ...s, puntos: s.puntos.map((p) => { const k = +p.t, base = acum.get(k) || 0; acum.set(k, base + p.v); return { ...p, base, v: base + p.v }; }) }));
  }
  const xs = series.flatMap((s) => s.puntos.map((p) => +p.t));
  const ys = series.flatMap((s) => s.puntos.flatMap((p) => [p.v, p.base ?? p.v]));
  if (cfg.referencia != null) ys.push(cfg.referencia);
  if (cfg.barras || cfg.apilar) ys.push(0);
  const ty = cfg.log ? ticksLog(Math.min(...ys), Math.max(...ys)) : ticksLindos(Math.min(...ys), Math.max(...ys));
  const y0 = ty[0], y1 = ty[ty.length - 1];
  let x0 = Math.min(...xs), x1 = Math.max(...xs);
  if (cfg.barras) { const pad = (x1 - x0) / Math.max(1, new Set(xs).size) / 2; x0 -= pad; x1 += pad; }
  const X = (x) => m.l + ((+x - x0) / (x1 - x0 || 1)) * (W - m.l - m.r);
  const Y = cfg.log
    ? (y) => m.t + (1 - (Math.log10(y) - Math.log10(y0)) / (Math.log10(y1) - Math.log10(y0) || 1)) * (H - m.t - m.b)
    : (y) => m.t + (1 - (y - y0) / (y1 - y0 || 1)) * (H - m.t - m.b);
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": cfg.titulo });

  if (cfg.bandas) dibujarGobiernos(svg, X, x0, x1, m, H);
  for (const t of ty) {
    svg.append(svgEl("line", { class: "grilla-h", x1: m.l, x2: W - m.r, y1: Y(t), y2: Y(t) }));
    const tx = svgEl("text", { x: m.l - 6, y: Y(t) + 4, "text-anchor": "end" });
    tx.textContent = cfg.eje(t);
    svg.append(tx);
  }
  if (cfg.unidadEje) { const u = svgEl("text", { x: 4, y: 12 }); u.textContent = cfg.unidadEje; svg.append(u); }
  if (cfg.referencia != null && cfg.referencia >= y0 && cfg.referencia <= y1)
    svg.append(svgEl("line", { class: "ref", x1: m.l, x2: W - m.r, y1: Y(cfg.referencia), y2: Y(cfg.referencia) }));
  for (const [x, lab] of ticksFecha(x0, x1)) {
    const t = svgEl("text", { x: X(x), y: H - 6, "text-anchor": "middle" });
    t.textContent = lab;
    svg.append(t);
  }

  if (cfg.barras) {
    const fechas = [...new Set(xs)].sort((a, b) => a - b);
    const ancho = Math.max(1, ((W - m.l - m.r) / fechas.length) * 0.8 / (cfg.apilar ? 1 : series.length));
    series.forEach((s, i) => s.puntos.forEach((p) => {
      const base = p.base ?? 0, x = X(+p.t) - (ancho * (cfg.apilar ? 1 : series.length)) / 2 + (cfg.apilar ? 0 : i * ancho);
      const fill = cfg.colorSigno ? css(p.v >= 0 ? "--s3" : "--estimacion") : s.color;
      svg.append(svgEl("rect", { x, y: Math.min(Y(p.v), Y(base)), width: ancho, height: Math.abs(Y(p.v) - Y(base)), fill, opacity: p.tramo ? 0.45 : 0.9 }));
    }));
  } else {
    for (const s of series) {
      if (cfg.apilar) {
        const arriba = s.puntos.map((p) => `${X(p.t).toFixed(1)},${Y(p.v).toFixed(1)}`);
        const abajo = s.puntos.slice().reverse().map((p) => `${X(p.t).toFixed(1)},${Y(p.base).toFixed(1)}`);
        svg.append(svgEl("polygon", { points: arriba.concat(abajo).join(" "), fill: s.color, opacity: 0.75 }));
      }
      // tramos observados en línea llena; estimados/proyectados en punteada
      let tramo = [];
      const cerrar = (punteada) => {
        if (tramo.length < 2) return;
        const d = tramo.map((p, i) => `${i ? "L" : "M"}${X(p.t).toFixed(1)},${Y(p.v).toFixed(1)}`).join("");
        svg.append(svgEl("path", { d, fill: "none", stroke: s.color, "stroke-width": s.grueso ? 2 : 1.4, "stroke-linejoin": "round", "stroke-linecap": "round",
          "stroke-dasharray": punteada ? "4 3" : null, opacity: s.grueso || cfg.series.length === 1 ? 1 : 0.85 }));
      };
      let actual = null;
      s.puntos.forEach((p, i) => {
        const punteada = !!p.tramo;
        if (actual === null) actual = punteada;
        if (punteada !== actual) { tramo.push(p); cerrar(actual); tramo = [s.puntos[i - 1] || p]; actual = punteada; }
        tramo.push(p);
      });
      cerrar(actual);
      if (s.puntos.length === 1) svg.append(svgEl("circle", { cx: X(s.puntos[0].t), cy: Y(s.puntos[0].v), r: 3, fill: s.color }));
    }
  }
  interaccion(svg, contenedor, series, cfg, { X, Y, x0, x1, m, W, H });
  contenedor.append(svg);
}

function interaccion(svg, contenedor, series, cfg, { X, Y, x0, x1, m, W, H }) {
  const cruz = svgEl("line", { class: "cruz", y1: m.t, y2: H - m.b, visibility: "hidden" });
  const marcas = series.map((s) => { const c = svgEl("circle", { r: 4, fill: s.color, stroke: css("--superficie"), "stroke-width": 2, visibility: "hidden" }); svg.append(c); return c; });
  svg.append(cruz);
  const capa = svgEl("rect", { x: m.l, y: 0, width: W - m.l - m.r, height: H, fill: "transparent" });
  svg.append(capa);
  const tip = document.getElementById("tooltip");
  const mover = (ev) => {
    const r = svg.getBoundingClientRect();
    const px = ((ev.touches ? ev.touches[0].clientX : ev.clientX) - r.left) * (W / r.width);
    const xv = x0 + ((px - m.l) / (W - m.l - m.r)) * (x1 - x0);
    const filas = []; let xRef = null, tramo = null;
    series.forEach((s, i) => {
      let mejor = null;
      for (const p of s.puntos) if (!mejor || Math.abs(+p.t - xv) < Math.abs(+mejor.t - xv)) mejor = p;
      if (!mejor || Math.abs(+mejor.t - xv) > 1000 * 3600 * 24 * 400) { marcas[i].setAttribute("visibility", "hidden"); return; }
      if (xRef == null) xRef = mejor.t;
      if (mejor.tramo) tramo = mejor.tramo;
      marcas[i].setAttribute("cx", X(mejor.t)); marcas[i].setAttribute("cy", Y(mejor.v)); marcas[i].setAttribute("visibility", "visible");
      filas.push([s, mejor.v - (mejor.base ?? 0)]);
    });
    if (!filas.length) return salir();
    cruz.setAttribute("x1", X(xRef)); cruz.setAttribute("x2", X(xRef)); cruz.setAttribute("visibility", "visible");
    const ym = `${xRef.getFullYear()}-${String(xRef.getMonth() + 1).padStart(2, "0")}-01`;
    tip.innerHTML = "";
    tip.append(el("div", { class: "t-fecha", text: periodo(ym, cfg.frecuencia) }));
    filas.forEach(([s, y]) => tip.append(el("div", { class: "t-fila" },
      el("span", {}, series.length > 1 ? el("i", { style: `background:${s.color}` }) : null, series.length > 1 ? s.nombre : "Valor"),
      el("span", { text: cfg.tip(y) }))));
    if (tramo) tip.append(el("div", { class: "t-tramo", text: `⚠ Dato ${TRAMOS[tramo] || tramo}` }));
    mostrarTip(tip, ev);
  };
  const salir = () => { tip.hidden = true; cruz.setAttribute("visibility", "hidden"); marcas.forEach((c) => c.setAttribute("visibility", "hidden")); };
  capa.addEventListener("mousemove", mover);
  capa.addEventListener("touchmove", mover, { passive: true });
  capa.addEventListener("mouseleave", salir);
  capa.addEventListener("touchend", salir);
}

function mostrarTip(tip, ev) {
  tip.hidden = false;
  const cx = ev.touches ? ev.touches[0].clientX : ev.clientX, cy = ev.touches ? ev.touches[0].clientY : ev.clientY;
  tip.style.left = Math.min(window.innerWidth - tip.offsetWidth - 8, cx + 14) + "px";
  tip.style.top = Math.max(8, cy - tip.offsetHeight - 12) + "px";
}

// Barras por categoría (por gobierno o por país), horizontales
function dibujarCategorias(contenedor, cfg) {
  contenedor.innerHTML = "";
  const n = cfg.categorias.length, k = cfg.series.length;
  const W = contenedor.clientWidth || 440;
  const filaH = Math.max(18, 10 + 12 * k), H = Math.max(160, n * filaH + 30);
  contenedor.style.height = H + "px";
  const etiquetas = Math.min(150, Math.max(...cfg.categorias.map((c) => c.length)) * 6.5 + 8);
  const m = { t: cfg.unidadEje ? 20 : 6, r: 54, b: 18, l: etiquetas };
  const vals = cfg.series.flatMap((s) => s.valores.filter(Boolean).map((v) => v.valor)).concat([0]);
  const tx = ticksLindos(Math.min(...vals), Math.max(...vals), 4);
  const v0 = tx[0], v1 = tx[tx.length - 1];
  const X = (v) => m.l + ((v - v0) / (v1 - v0 || 1)) * (W - m.l - m.r);
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": cfg.titulo });
  for (const t of tx) {
    svg.append(svgEl("line", { class: "grilla-h", x1: X(t), x2: X(t), y1: m.t, y2: H - m.b }));
    const tt = svgEl("text", { x: X(t), y: H - 4, "text-anchor": "middle" }); tt.textContent = cfg.eje(t); svg.append(tt);
  }
  if (cfg.unidadEje) { const u = svgEl("text", { x: m.l, y: 12 }); u.textContent = cfg.unidadEje; svg.append(u); }
  const alto = (H - m.t - m.b) / n, barra = Math.min(14, (alto * 0.8) / k);
  const tip = document.getElementById("tooltip");
  cfg.categorias.forEach((c, i) => {
    const yc = m.t + i * alto + alto / 2;
    const et = svgEl("text", { class: "etq-cat", x: m.l - 6, y: yc + 4, "text-anchor": "end" }); et.textContent = c; svg.append(et);
    cfg.series.forEach((s, j) => {
      const v = s.valores[i]; if (!v) return;
      const y = yc - (barra * k) / 2 + j * barra;
      const r = svgEl("rect", { x: Math.min(X(0), X(v.valor)), y, width: Math.abs(X(v.valor) - X(0)), height: barra - 1, fill: s.color, opacity: v.tramo ? 0.45 : 0.9 });
      r.addEventListener("mousemove", (ev) => {
        tip.innerHTML = "";
        tip.append(el("div", { class: "t-fecha", text: c }), el("div", { class: "t-fila" }, el("span", { text: k > 1 ? s.nombre : "Valor" }), el("span", { text: cfg.tip(v.valor) })));
        if (v.tramo) tip.append(el("div", { class: "t-tramo", text: `⚠ Dato ${TRAMOS[v.tramo] || v.tramo}` }));
        mostrarTip(tip, ev);
      });
      r.addEventListener("mouseleave", () => { tip.hidden = true; });
      svg.append(r);
      if (k === 1) { const vt = svgEl("text", { class: "val-cat", x: X(v.valor) + (v.valor >= 0 ? 4 : -4), y: y + barra / 2 + 3, "text-anchor": v.valor >= 0 ? "start" : "end" }); vt.textContent = cfg.tip(v.valor); svg.append(vt); }
    });
  });
  svg.append(svgEl("line", { class: "ref", x1: X(0), x2: X(0), y1: m.t, y2: H - m.b }));
  contenedor.append(svg);
}

// Burbujas: x, y, tamaño por categoría; color por grupo
const COLOR_GRUPO = { "Creó empleo": "--s3", "Destruyó empleo": "--estimacion", "Sin cambios": "--gris-serie" };
function coloresGrupo(cats) {
  const grupos = [...new Set(cats.map((c) => c.grupo).filter(Boolean))];
  return Object.fromEntries(grupos.map((gr, i) => [gr, css(COLOR_GRUPO[gr] || COLORES[i % COLORES.length])]));
}
function dibujarBurbujas(contenedor, g) {
  contenedor.innerHTML = "";
  const W = contenedor.clientWidth || 440, H = contenedor.clientHeight || 300, m = { t: 22, r: 16, b: 34, l: 44 };
  const cats = g.categorias.filter((c) => c.x != null && c.y != null);
  const tx = ticksLindos(Math.min(...cats.map((c) => c.x), 0), Math.max(...cats.map((c) => c.x), 0));
  const ty = ticksLindos(0, Math.max(...cats.map((c) => c.y)));
  const X = (v) => m.l + ((v - tx[0]) / (tx[tx.length - 1] - tx[0])) * (W - m.l - m.r);
  const Y = (v) => m.t + (1 - (v - ty[0]) / (ty[ty.length - 1] - ty[0])) * (H - m.t - m.b);
  const maxT = Math.max(...cats.map((c) => c.tamano || 1));
  const colores = coloresGrupo(cats);
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": g.titulo });
  for (const t of ty) { svg.append(svgEl("line", { class: "grilla-h", x1: m.l, x2: W - m.r, y1: Y(t), y2: Y(t) })); const e = svgEl("text", { x: m.l - 6, y: Y(t) + 4, "text-anchor": "end" }); e.textContent = fmt(t, 0); svg.append(e); }
  for (const t of tx) { const e = svgEl("text", { x: X(t), y: H - 18, "text-anchor": "middle" }); e.textContent = fmt(t, 0); svg.append(e); }
  if (tx[0] < 0) svg.append(svgEl("line", { class: "ref", x1: X(0), x2: X(0), y1: m.t, y2: H - m.b }));
  if (g.eje_x) { const e = svgEl("text", { x: W - m.r, y: H - 2, "text-anchor": "end" }); e.textContent = g.eje_x; svg.append(e); }
  if (g.eje_y) { const e = svgEl("text", { x: 4, y: 11 }); e.textContent = g.eje_y; svg.append(e); }
  const tip = document.getElementById("tooltip");
  const ocupadas = [];
  const ubicar = (x, y, ancho) => { // corre la etiqueta hasta que no se pise con otra
    for (const dy of [0, 12, -12, 24, -24, 36, -36]) {
      const caja = [x, y + dy - 10, x + ancho, y + dy + 2];
      if (!ocupadas.some((o) => caja[0] < o[2] && caja[2] > o[0] && caja[1] < o[3] && caja[3] > o[1])) { ocupadas.push(caja); return y + dy; }
    }
    return y;
  };
  cats.slice().sort((a, b) => (b.tamano || 0) - (a.tamano || 0)).forEach((c) => {
    const r = 5 + 20 * Math.sqrt((c.tamano || 1) / maxT);
    const circ = svgEl("circle", { cx: X(c.x), cy: Y(c.y), r, fill: colores[c.grupo] || css("--s1"), opacity: c.tramo ? 0.3 : 0.55, stroke: colores[c.grupo] || css("--s1") });
    circ.addEventListener("mousemove", (ev) => {
      tip.innerHTML = "";
      tip.append(el("div", { class: "t-fecha", text: c.categoria }),
        el("div", { class: "t-fila" }, el("span", { text: "Actividad" }), el("span", { text: signo(c.x) + "%" })),
        el("div", { class: "t-fila" }, el("span", { text: "Participación" }), el("span", { text: fmt(c.y) + "%" })),
        c.var_y != null ? el("div", { class: "t-fila" }, el("span", { text: "Empleo, interanual" }), el("span", { text: signo(c.var_y) + "%" })) : null);
      mostrarTip(tip, ev);
    });
    circ.addEventListener("mouseleave", () => { tip.hidden = true; });
    svg.append(circ);
    const ancho = c.categoria.length * 5.6, derecha = X(c.x) + r + 3 + ancho < W;
    const lx = derecha ? X(c.x) + r + 3 : X(c.x) - r - 3 - ancho;
    const e = svgEl("text", { class: "etq-cat", x: lx, y: ubicar(lx, Y(c.y) + 4, ancho) }); e.textContent = c.categoria; svg.append(e);
  });
  contenedor.append(svg);
  return colores;
}

/* ---------- Ficha de cada gráfico ---------- */

function insigniaNivel(n) { return el("span", { class: `nivel nivel-${n}`, text: NIVELES[n] || n }); }

function cifra(g) {
  if (!g.series || g.tipo === "barras_gobierno" || g.tipo === "lineas_pais") return null;
  const s = g.series.find((x) => x.color !== "gris") || g.series[0];
  const p = s.puntos[s.puntos.length - 1];
  if (!p) return null;
  const pts = s.puntos.map((q) => ({ t: fecha(q[0]), v: q[1], tramo: q[2] }));
  // Índices en base 100 o reales: el nivel no dice nada solo, se muestra la variación interanual
  const medCifra = g.medida_inicial === "base_100" ? (g.frecuencia === "A" ? "variacion" : "interanual") : g.medida_inicial;
  if (medCifra === "variacion" || medCifra === "interanual") {
    const med = aplicarMedida(pts, medCifra, g), u = med[med.length - 1];
    if (!u) return null;
    const txt = esDiferencia(g) ? signo(u.v, decimales(u.v)) + sufijoDif(g) : signo(u.v) + "%";
    const prefijo = g.medida_inicial === "base_100" ? `${s.nombre}, ` : "";
    return { grande: txt, chica: `${prefijo}${medCifra === "variacion" ? nombreVariacion(g) : "interanual"} · ${periodo(p[0], g.frecuencia)}` };
  }
  let v = p[1];
  if (g.tipo === "areas") v = g.series.reduce((t, x) => t + (x.puntos.find((q) => q[0] === p[0])?.[1] || 0), 0);
  if (g.medida_inicial === "acumulado_12m" && g.tipo !== "areas") { const med = aplicarMedida(pts, "acumulado_12m", g); v = med[med.length - 1]?.v; }
  const mg = magnitud(g.unidad, Math.abs(v));
  return { grande: fmt(v / mg.div, decimales(v / mg.div)), chica: `${mg.unidad}${g.medida_inicial === "acumulado_12m" ? " (12 meses)" : ""} · ${periodo(p[0], g.frecuencia)}` };
}

function detalle(g) {
  const fuentes = el("ul", {}, ...g.fuentes.map((f) => el("li", {},
    insigniaNivel(f.nivel), " ",
    f.url ? el("a", { href: f.url, target: "_blank", rel: "noopener", text: f.nombre }) : f.nombre,
    f.desde || f.hasta ? ` (${f.desde ? mesAnio(f.desde) : "inicio"} – ${f.hasta ? mesAnio(f.hasta) : "hoy"})` : "",
    f.nota ? `. ${f.nota}` : "")));
  const tramos = (g.tramos || []).length ? el("ul", {}, ...g.tramos.map((t) => el("li", {},
    `⚠ ${t.tipo[0].toUpperCase() + t.tipo.slice(1)}${t.serie ? ` (${(g.series.find((x) => x.serie === t.serie) || {}).nombre || t.serie})` : ""}: ${t.desde ? mesAnio(String(t.desde)) : "inicio"} – ${t.hasta ? mesAnio(String(t.hasta)) : "hoy"}`,
    t.nota ? `. ${t.nota}` : ""))) : null;
  return el("details", { class: "detalle" },
    el("summary", { text: "Fuentes y método" }),
    el("h4", { text: "Fuentes" }), fuentes,
    g.metodo ? el("h4", { text: "Método" }) : null, g.metodo ? el("p", { text: g.metodo }) : null,
    tramos ? el("h4", { text: "Tramos no observados" }) : null, tramos,
    g.original ? el("p", { class: "leyenda-vista", text: `Reemplaza al gráfico ${g.original.ficha || ""} del documento (imagen ${g.original.imagen || "s/d"}).` }) : null);
}

function ficha(g) {
  const temporal = !!g.series && g.tipo !== "barras_gobierno";
  const estado = { periodo: "completo", medida: g.medida_inicial || "nivel", gobiernos: true };
  if (temporal && !medidasDisponibles(g).includes(estado.medida)) estado.medida = "nivel";
  const grafico = el("div", { class: g.tipo === "burbujas" ? "grafico burbujas" : "grafico" });
  const leyendaVista = el("p", { class: "leyenda-vista" });
  const leyenda = el("ul", { class: "leyenda", hidden: true });
  const controles = el("div", { class: "controles" });
  if (temporal) {
    const botones = [["completo", `Completo (desde ${g.frecuencia === "A" ? g.desde.slice(0, 4) : mesAnio(g.desde.slice(0, 7))})`], ["mandato", "Último mandato"]].map(([id, txt]) =>
      el("button", { type: "button", "aria-pressed": String(estado.periodo === id), text: txt, onclick: () => { estado.periodo = id; botones.forEach((b, i) => b.setAttribute("aria-pressed", String(i === (id === "completo" ? 0 : 1)))); render(); } }));
    if (g.ultimo < META.base_ultimo_mandato) { botones[1].disabled = true; botones[1].title = "La serie termina antes del último mandato"; }
    controles.append(el("div", { class: "segmentos", role: "group", "aria-label": "Período" }, ...botones));
    const sel = el("select", { "aria-label": "Medida", onchange: () => { estado.medida = sel.value; render(); } },
      ...medidasDisponibles(g).map((k) => el("option", { value: k, text: MEDIDAS[k], selected: k === estado.medida })));
    controles.append(sel);
    const valores = g.series.flatMap((x) => x.puntos.map((p) => p[1]));
    if (valores.every((v) => v > 0) && Math.max(...valores) / Math.min(...valores) > 15)
      controles.append(el("label", { class: "chk" }, el("input", { type: "checkbox", onchange: (e) => { estado.log = e.target.checked; render(); } }), "Escala logarítmica"));
    if (g.gobiernos) controles.append(el("label", { class: "chk" },
      el("input", { type: "checkbox", checked: true, onchange: (e) => { estado.gobiernos = e.target.checked; render(); } }), "Gobiernos"));
  }
  function render() {
    tipHide();
    if (!temporal) {
      leyendaVista.textContent = g.tipo === "barras_gobierno" ? `Por gobierno, en ${g.unidad}.` : g.tipo === "burbujas" && g.ultimo ? `Datos a ${periodo(g.ultimo, "M")}.` : (g.unidad ? `En ${g.unidad}.` : "");
      if (g.tipo === "burbujas") {
        const colores = dibujarBurbujas(grafico, g);
        leyenda.innerHTML = ""; leyenda.hidden = false;
        Object.entries(colores).forEach(([n, c]) => leyenda.append(el("li", {}, el("i", { style: `background:${c};height:8px;width:8px;border-radius:50%` }), n)));
        leyenda.append(el("li", { text: "Tamaño: cantidad de asalariados" }));
      }
      else { const cfg = { ...prepararCategorias(g), titulo: g.titulo }; ponerLeyenda(cfg.series, []); dibujarCategorias(grafico, cfg); }
      return;
    }
    leyendaVista.textContent = textoMedida(g, estado.medida);
    const cfg = { ...prepararTemporal(g, estado), titulo: `${g.titulo}: ${textoMedida(g, estado.medida)}` };
    const hayTramos = cfg.series.some((s) => s.puntos.some((p) => p.tramo));
    ponerLeyenda(cfg.series, hayTramos ? ["⚠ Estimado o proyectado"] : []);
    dibujarTemporal(grafico, cfg);
  }
  function ponerLeyenda(series, extras) {
    leyenda.innerHTML = "";
    leyenda.hidden = series.length < 2 && !extras.length;
    if (series.length > 1) series.forEach((s) => leyenda.append(el("li", {}, el("i", { style: `background:${s.color}` }), s.nombre)));
    extras.forEach((x) => leyenda.append(el("li", {}, el("i", { class: "punteada" }), x)));
  }
  const c = cifra(g);
  const art = el("article", { class: "ficha", id: g.id },
    el("div", { class: "ficha-cab" },
      el("div", {},
        el("h3", { text: g.titulo }),
        el("div", { class: "insignias" }, ...(g.niveles_fuente || []).map(insigniaNivel),
          g.alerta ? el("span", { class: "alerta", title: "Parte o todo el gráfico es estimado, interpolado o proyectado" }, "⚠ ", g.estimacion ? "Estimación" : "Tramos estimados") : null)),
      c ? el("div", { class: "cifra" }, el("span", { class: "grande", text: c.grande }), el("span", { class: "chica", text: c.chica })) : null),
    g.que_muestra ? el("p", { class: "que-muestra", text: g.que_muestra }) : null,
    g.estimacion ? el("p", { class: "aviso" }, el("strong", { text: "⚠ Estimación. " }), g.estimacion) : null,
    g.sensible ? el("p", { class: "aviso sensible" }, el("strong", { text: "Sobre estos datos. " }), g.sensible) : null,
    controles, leyendaVista, grafico, leyenda,
    g.nota ? el("p", { class: "leyenda-vista", text: g.nota }) : null,
    detalle(g),
    el("div", { class: "ficha-pie" },
      el("span", { text: g.ultimo ? `Último dato: ${periodo(g.ultimo, g.frecuencia)}` : "" }),
      el("a", { href: `${DATOS}graficos/${g.id}.csv`, download: `${g.id}.csv`, text: "Descargar CSV" })));
  new ResizeObserver(() => render()).observe(grafico);
  return art;
}
function tipHide() { const t = document.getElementById("tooltip"); if (t) t.hidden = true; }

/* ---------- Página ---------- */

async function json(ruta) { const r = await fetch(DATOS + ruta, { cache: "no-cache" }); if (!r.ok) throw new Error(ruta); return r.json(); }

async function iniciar() {
  META = await json("radiografia.json");
  document.getElementById("actualizado").textContent =
    `${META.graficos.length} gráficos · actualizado el ${META.actualizado.split("-").reverse().join("/")}`;
  const graficos = await Promise.all(META.graficos.map((x) => json(`graficos/${x.id}.json`).catch(() => null)));
  const porTema = new Map();
  for (const g of graficos.filter(Boolean)) { if (!porTema.has(g.tema)) porTema.set(g.tema, []); porTema.get(g.tema).push(g); }
  const main = document.getElementById("temas"), nav = document.getElementById("nav-temas");
  document.getElementById("cargando").remove();
  const secciones = [];
  for (const t of META.temas) {
    const lista = porTema.get(t.numero);
    if (!lista) continue;
    const grilla = el("div", { class: "grilla" }, ...lista.map(ficha));
    const sec = el("section", { class: "tema", id: `tema-${t.numero}` }, el("h2", {}, el("span", { class: "n", text: String(t.numero) }), t.nombre), grilla);
    main.insertBefore(sec, document.getElementById("sin-resultados"));
    nav.append(el("a", { href: `#tema-${t.numero}` }, el("span", { class: "n", text: String(t.numero) }), t.nombre));
    secciones.push({ sec, fichas: lista.map((g) => ({ g, nodo: grilla.querySelector(`#${CSS.escape(g.id)}`) })) });
  }
  const buscar = document.getElementById("buscar");
  buscar.addEventListener("input", () => {
    const q = normalizar(buscar.value.trim());
    let total = 0;
    for (const s of secciones) {
      let visibles = 0;
      for (const { g, nodo } of s.fichas) {
        const ok = !q || normalizar(`${g.titulo} ${g.que_muestra || ""} ${g.tema_nombre} ${(g.fuentes || []).map((f) => f.nombre).join(" ")}`).includes(q);
        nodo.hidden = !ok; if (ok) visibles++;
      }
      s.sec.hidden = !visibles; total += visibles;
    }
    document.getElementById("sin-resultados").hidden = total > 0;
  });
}

iniciar().catch((e) => { const c = document.getElementById("cargando"); if (c) c.textContent = "No se pudieron cargar los datos."; console.error(e); });
