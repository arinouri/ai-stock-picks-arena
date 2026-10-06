// Small dependency-free SVG charts.

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function niceTicks(min, max, count = 5) {
  if (min === max) { min -= 1; max += 1; }
  const span = max - min;
  const step0 = span / count;
  const mag = 10 ** Math.floor(Math.log10(step0));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= step0) || mag * 10;
  const lo = Math.floor(min / step) * step;
  const hi = Math.ceil(max / step) * step;
  const ticks = [];
  for (let v = lo; v <= hi + step / 2; v += step) ticks.push(+v.toFixed(10));
  return ticks;
}

/** Multi-series line chart. series: [{name, color, points: [{x: "2026-10-01", y: 1000}]}] */
export function lineChart(series, { width = 1000, height = 300, baseline = null, fmt = (v) => v, label = "Chart" } = {}) {
  const all = series.flatMap((s) => s.points);
  if (!all.length) return "";
  const xs = [...new Set(all.map((p) => p.x))].sort();
  const ys = all.map((p) => p.y).concat(baseline != null ? [baseline] : []);
  const ticks = niceTicks(Math.min(...ys), Math.max(...ys));
  const [ymin, ymax] = [ticks[0], ticks[ticks.length - 1]];
  const m = { l: 64, r: 16, t: 12, b: 28 };
  const w = width - m.l - m.r, h = height - m.t - m.b;
  const X = (x) => m.l + (xs.length === 1 ? w / 2 : (xs.indexOf(x) / (xs.length - 1)) * w);
  const Y = (y) => m.t + h - ((y - ymin) / (ymax - ymin || 1)) * h;
  const grid = ticks.map((t) => `<line class="gridline" x1="${m.l}" x2="${width - m.r}" y1="${Y(t)}" y2="${Y(t)}"/>
    <text x="${m.l - 8}" y="${Y(t) + 4}" text-anchor="end">${esc(fmt(t))}</text>`).join("");
  const every = Math.max(1, Math.ceil(xs.length / 8));
  const xl = xs.filter((_, i) => i % every === 0 || i === xs.length - 1).map((x) =>
    `<text x="${X(x)}" y="${height - 6}" text-anchor="middle">${esc(shortDate(x))}</text>`).join("");
  const base = baseline != null
    ? `<line x1="${m.l}" x2="${width - m.r}" y1="${Y(baseline)}" y2="${Y(baseline)}" stroke="currentColor" stroke-opacity=".5" stroke-dasharray="4 4"/>` : "";
  const lines = series.map((s) => {
    if (!s.points.length) return "";
    const d = s.points.map((p, i) => `${i ? "L" : "M"}${X(p.x).toFixed(1)},${Y(p.y).toFixed(1)}`).join("");
    const last = s.points[s.points.length - 1];
    const dots = s.points.map((p) => `<circle cx="${X(p.x)}" cy="${Y(p.y)}" r="9" fill="transparent"><title>${esc(s.name)} · ${esc(p.x)}: ${esc(fmt(p.y))}</title></circle>`).join("");
    return `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
      <circle cx="${X(last.x)}" cy="${Y(last.y)}" r="4" fill="${s.color}"/>${dots}`;
  }).join("");
  return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(label)}">
    <g class="axis">${grid}${xl}</g>${base}${lines}</svg>`;
}

/** Intraday sparkline with reference, target and stop levels. */
export function sparkline(points, { ref, target, stop, width = 360, height = 90, mini = false } = {}) {
  if (!points || points.length < 2) return "";
  const vals = points.map((p) => p[1]);
  const levels = mini ? [ref] : [ref, target, stop];
  const lv = levels.filter((v) => v != null);
  let lo = Math.min(...vals, ...lv), hi = Math.max(...vals, ...lv);
  if (!mini && target != null && target > hi * 1.5) hi = Math.max(...vals, ref) * 1.05; // keep chart readable
  const pad = (hi - lo) * 0.08 || 1;
  lo -= pad; hi += pad;
  const X = (i) => (i / (points.length - 1)) * width;
  const Y = (v) => height - ((v - lo) / (hi - lo)) * height;
  const last = vals[vals.length - 1];
  const color = ref != null && last < ref ? "var(--down)" : "var(--up)";
  const d = vals.map((v, i) => `${i ? "L" : "M"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join("");
  const line = (v, stroke, dash, label) => v == null || v < lo || v > hi ? "" :
    `<line x1="0" x2="${width}" y1="${Y(v)}" y2="${Y(v)}" stroke="${stroke}" stroke-dasharray="${dash}" stroke-width="1"/>` +
    (mini ? "" : `<text x="${width - 2}" y="${Y(v) - 3}" text-anchor="end" font-size="11" fill="${stroke}">${label}</text>`);
  return `<svg class="${mini ? "mini" : "spark"}" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">
    ${line(ref, "var(--muted)", "3 3", "ref")}
    ${mini ? "" : line(target, "var(--up)", "2 4", "target")}
    ${mini ? "" : line(stop, "var(--down)", "2 4", "stop")}
    <path d="${d}" fill="none" stroke="${color}" stroke-width="${mini ? 1.5 : 2}" vector-effect="non-scaling-stroke"/></svg>`;
}

export function shortDate(iso) {
  const d = new Date(iso + "T12:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}
