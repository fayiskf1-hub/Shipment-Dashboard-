# Chart Guide

## Contents
1. Pick the chart from the question
2. Anti-patterns (and what to do instead)
3. Chart.js recipes (work with the template's `mount()` / `baseOptions()` / `css()` helpers)
4. When to use ECharts instead

---

## 1. Pick the chart from the question

| The user wants to know… | Use | Notes |
|---|---|---|
| How is X changing over time? | **Line** (continuous, many points) or **bar** (counts per period, ≤ ~30 bars) | Time on x, left→right. Trim partial edge periods. |
| …and what is it made of over time? | **Stacked bar** | ≤ 5 segments; the most important segment on the baseline. |
| Is it hitting target? | Line + **dashed target line**, or **bullet/progress bar** for a single value | Target in `--text-3`, dashed. |
| Who/what is best/worst? | **Horizontal bar, sorted by value** | Horizontal fits long labels. Colour by status vs target if there is one. Top/bottom N + "Other". |
| What share does each part have? | **Single stacked 100% bar** or sorted bar of % | Doughnut only for 2–4 parts and when asked; never a pie with > 5 slices. |
| How are two measures related? | **Scatter** (bubble if a third measure matters) | e.g. cost/kg vs transit days per lane. Label outliers. |
| How are values distributed? | **Histogram** (or box plot via ECharts) | e.g. transit-day distribution; mean hides the long tail. |
| Where is it happening? | **Map** (ECharts) or a ranked table if < 15 locations | Maps are only better when geography itself matters. |
| Which combination is hot? | **Heatmap** (two dims × one measure) | e.g. lane × week delay rate. ECharts or a coloured HTML table. |
| Exact values to look up | **Table** with conditional formatting | Charts are for patterns, tables for lookup. |
| One number | **KPI card**, not a chart | |

## 2. Anti-patterns

| Don't | Because | Instead |
|---|---|---|
| Dual y-axes | Readers infer correlations from arbitrary scale choices | Two aligned charts, or index both to 100 |
| Bar chart axis not starting at 0 | Bar length *is* the value; truncation lies | `beginAtZero: true` for bars (lines may zoom) |
| Pie/doughnut with many slices | Angles are hard to compare | Sorted horizontal bar |
| 3D, shadows, gradients on data | Distorts and decorates | Flat fills |
| Rainbow categorical colours > 6 | Unreadable, legend lookup hell | Top 5 + "Other" |
| Alphabetical ranking | Hides the pattern | Sort by value |
| Legend for a single series | Noise | Hide legend, name the measure in the title |
| Gauges/speedometers | Lots of ink for one number | KPI card with target, or bullet bar |
| Averages of percentages | Wrong maths (unweighted) | Recompute from numerator/denominator sums |
| Plotting weeks with n = 1 | Fake 0%/100% spikes | Minimum sample; leave a gap (`null`) |
| Animations on every filter change | Feels slow, distracts | `animation: false` (template default) |

## 3. Chart.js recipes (v4.4.1)

All recipes assume the template's helpers:
`mount(canvasId, config, isEmpty)`, `baseOptions(extra)`, `css('--token')`, `series()` (array of 6 categorical colours), `fmt.*`, `groupBy`, `sum`.

Canvas markup (fixed-height box is required):
```html
<div class="chart-box"><canvas id="c-x" role="img" aria-label="…describe the chart…"></canvas><div class="empty">No data for these filters</div></div>
```

### Stacked bar over time
```js
const o = baseOptions();
o.scales.x.stacked = true; o.scales.y.stacked = true;
mount('c-x', { type: 'bar', data: { labels, datasets: groups.map((g, i) => ({ label: g, data: valuesFor(g), backgroundColor: series()[i % 6], borderRadius: 3, maxBarThickness: 28 })) }, options: o }, !labels.length);
```

### Line with dashed target
```js
const o = baseOptions();
o.scales.y = { ...o.scales.y, beginAtZero: false, max: 100, ticks: { ...o.scales.y.ticks, callback: v => v + '%' } };
mount('c-x', { type: 'line', data: { labels, datasets: [
  { label: 'Actual', data: values, borderColor: css('--accent'), backgroundColor: css('--accent-soft'), fill: true, tension: .3, pointRadius: 0, pointHoverRadius: 4, borderWidth: 2 },
  { label: 'Target', data: values.map(() => target), borderColor: css('--text-3'), borderDash: [5, 4], borderWidth: 1.5, pointRadius: 0, fill: false },
] }, options: o }, !values.length);
```

### Sorted horizontal bar, coloured against target
```js
const rows = [...groupBy(data, r => r.carrier)].map(([k, rs]) => [k, metric(rs)]).sort((a, b) => a[1] - b[1]); // worst first
const o = baseOptions({ indexAxis: 'y' });
o.scales = { x: { ...o.scales.y }, y: { ...o.scales.x, ticks: { ...o.scales.x.ticks, autoSkip: false } } }; // swap axis styling
o.plugins.legend = { display: false };
mount('c-x', { type: 'bar', data: { labels: rows.map(r => r[0]), datasets: [{ data: rows.map(r => r[1]),
  backgroundColor: rows.map(r => r[1] >= target ? css('--good') : r[1] >= target - 10 ? css('--warn') : css('--bad')), borderRadius: 3, maxBarThickness: 22 }] }, options: o }, !rows.length);
```
Top N + Other: `const top = rows.slice(0, 7); const other = rows.slice(7).reduce((a, r) => a + r[1], 0); if (other) top.push(['Other', other]);` (only for additive measures — never sum percentages).

### Bar + line combo (same axis only)
Use only when both share a unit (e.g. actual vs forecast units). Set `type: 'bar'` on the chart and `type: 'line'` on the forecast dataset with `order: 0` so the line draws on top.

### Scatter (with tooltip labels)
```js
const o = baseOptions({ interaction: { mode: 'nearest', intersect: true } });
o.scales.x = { ...o.scales.y, title: { display: true, text: 'Transit days', color: css('--text-2') } };
o.scales.y = { ...o.scales.y, title: { display: true, text: 'Cost per kg', color: css('--text-2') } };
o.plugins.tooltip.callbacks = { label: c => ` ${c.raw.label}: ${c.raw.x} d · ${fmt.money2(c.raw.y)}/kg` };
mount('c-x', { type: 'scatter', data: { datasets: [{ data: points /* {x, y, label} */, backgroundColor: css('--accent'), pointRadius: 5, pointHoverRadius: 7 }] }, options: o }, !points.length);
```
Bubble: `type: 'bubble'`, points get `r` (scale it: `r: 4 + 12 * Math.sqrt(v / max)`).

### Histogram
```js
const bins = 12, min = Math.min(...vals), max = Math.max(...vals), w = (max - min) / bins || 1;
const counts = Array(bins).fill(0); vals.forEach(v => counts[Math.min(bins - 1, Math.floor((v - min) / w))]++);
const labels = counts.map((_, i) => `${fmt.dec(min + i * w)}–${fmt.dec(min + (i + 1) * w)}`);
mount('c-x', { type: 'bar', data: { labels, datasets: [{ data: counts, backgroundColor: css('--s1'), barPercentage: 1, categoryPercentage: .95 }] },
  options: baseOptions({ plugins: { ...baseOptions().plugins, legend: { display: false } } }) }, !vals.length);
```

### Doughnut (2–4 parts, if asked)
```js
mount('c-x', { type: 'doughnut', data: { labels, datasets: [{ data: values, backgroundColor: series().slice(0, values.length), borderColor: css('--surface'), borderWidth: 2 }] },
  options: { responsive: true, maintainAspectRatio: false, animation: false, cutout: '68%', plugins: baseOptions().plugins } }, !values.length);
```
Put the total in the middle with an absolutely-positioned div over the canvas.

### Bullet / progress (no library)
```html
<div class="bullet" style="--v:72%;--t:85%"><span></span><i></i></div>
<style>
.bullet{position:relative;height:10px;background:var(--surface-2);border-radius:5px}
.bullet span{position:absolute;inset:0 auto 0 0;width:var(--v);background:var(--accent);border-radius:5px}
.bullet i{position:absolute;top:-3px;bottom:-3px;left:var(--t);width:2px;background:var(--text)}
</style>
```

### Click-to-filter from a chart
```js
o.onClick = (evt, els, chart) => { if (!els.length) return; const v = chart.data.labels[els[0].index];
  state.carrier = state.carrier === v ? '' : v; document.getElementById('f-carrier').value = state.carrier; renderAll(); };
o.onHover = (e, els) => e.native.target.style.cursor = els.length ? 'pointer' : 'default';
```

### Useful options
- Time labels: format bucket keys with `fmt.date` yourself rather than loading the Chart.js date adapter.
- Many x labels: `ticks: { autoSkip: true, maxRotation: 0, autoSkipPadding: 12 }`.
- Value labels on bars: no plugin needed for ≤ 10 bars — draw in a tiny inline plugin:
  ```js
  const valueLabels = { id: 'vl', afterDatasetsDraw(c) { const { ctx } = c; ctx.save(); ctx.fillStyle = css('--text-2'); ctx.font = '11px system-ui'; ctx.textBaseline = 'middle';
    c.getDatasetMeta(0).data.forEach((b, i) => ctx.fillText(fmt.int(c.data.datasets[0].data[i]), b.x + 6, b.y)); ctx.restore(); } };
  // mount('c-x', { …, plugins: [valueLabels] })
  ```
  (horizontal bars; for vertical use `b.x, b.y - 8` with `textAlign = 'center'`; leave room with `layout: { padding: { right: 40 } }`).

## 4. When to use ECharts instead

Use Apache ECharts 5.5.0 (`https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.min.js`) when you need: geographic maps, sankey (flows origin → hub → destination), treemap, calendar heatmap, box plots, or > 50k points (`large: true`, `sampling: 'lttb'`). Init with `echarts.init(el, null, { renderer: 'canvas' })`, call `chart.resize()` on window resize, and rebuild the option object from CSS tokens on theme change exactly like the Chart.js path. Use one library per dashboard.
