---
name: html-dashboard-designer
description: Design and build polished, self-contained, interactive HTML dashboards — KPI cards with deltas and sparklines, Chart.js charts, filters that drive every panel, sortable/searchable tables, CSV export, light/dark themes, mobile layout — from CSV, Excel, JSON, SQL results or pasted numbers. Use this skill whenever the user wants a dashboard, report page, KPI/scorecard view, control tower, tracker, monitoring screen, or "visualize this data in a web page", and whenever they share a spreadsheet/export and want it turned into something visual or shareable — even if they never say "HTML" or "dashboard" (e.g. "make this shipment data look good for my manager", "build me an OTIF view", "turn this Excel into something interactive", "redesign this dashboard, it looks ugly"). Also use it to review, fix or restyle an existing HTML dashboard. Not for Power BI/Tableau/Excel-native dashboards or static matplotlib charts.
---

# HTML Dashboard Designer

You build dashboards that a busy manager can read in five seconds and an analyst can interrogate for five minutes — in one HTML file that opens anywhere, offline, with no build step.

The bundled template (`assets/dashboard-template.html`) is a complete, tested, production-quality dashboard (shipment-performance example with seeded demo data). **Start from it rather than from a blank file** — it already solves theming, formatting, filters, deltas, empty states, accessibility, print and mobile, which is where hand-rolled dashboards usually fall apart. Your job is mostly to decide *what* to show, then adapt the template's CONFIG, KPI list, charts and table columns.

## Workflow

### 1. Understand the question before the data

A dashboard is an answer to a recurring question. Before writing code, pin down (from the conversation; ask only if truly unclear):

- **Audience & decision** — who opens this and what do they do differently after? ("Ops lead deciding which carrier to escalate this week" ≠ "CFO checking spend vs budget".)
- **The 3–6 headline numbers** that answer that question. These become KPI cards. If you can't name them, the dashboard will become a chart dump.
- **Comparison baseline** — previous period, target, budget, last year? Every headline number needs one, otherwise "89.5%" means nothing.
- **Grain & dimensions** — one row per what? Which columns are worth filtering by (usually 2–5 low-cardinality ones)?

If the user just says "make a dashboard from this file", infer sensible answers from the data and domain, state your assumptions in one or two lines, and proceed — don't interrogate them.

### 2. Profile the data

```bash
python scripts/inject_data.py <data.csv|xlsx|json> --profile
```

This prints each column's type, nulls, distinct count and range after cleaning (snake_case names, ISO dates, numeric strings → numbers, `12%` → 0.12). Look for: the date column(s), measures (numeric), dimensions (few distinct values), IDs, and data-quality traps (nulls in key fields, mixed date formats, duplicate IDs, negative costs). Mention real quality issues to the user — a dashboard that silently hides bad data is worse than none.

For large data (> ~50k rows or > 5 MB JSON), pre-aggregate in Python (pandas) to the grain the charts need and embed that, keeping row-level detail only for the table (or the most recent N rows).

### 3. Plan the layout (top → bottom = summary → detail)

Use the inverted-pyramid layout the template implements. Read `references/design-system.md` for the full spec.

1. **Header** — title (2–4 words), "Data as of <latest date in the data>", row count, actions (Export, Print, Theme).
2. **Filter bar** — period + the dimensions from step 1. Every filter drives *every* panel; show "N of M rows" so filtering is never invisible.
3. **KPI row** — 3–6 cards: value, delta vs baseline coloured by whether up is good or bad, target if one exists, sparkline.
4. **Trend row** — the main time series full-width or 8/12, a supporting trend 4/12.
5. **Breakdown row** — rankings by dimension (sorted horizontal bars), composition.
6. **Detail table** — sortable, searchable, paginated; status as coloured pills with text.
7. **Footer** — source and metric definitions ("On-time = delivered on or before ETA").

Pick each chart with `references/chart-guide.md` (it has Chart.js recipes). Short version: trend → line/bar over time; ranking → horizontal bar sorted; composition over time → stacked bar; part-of-whole with ≤ 4 parts → stacked bar or a single bar, donut only if the user insists; relationship → scatter; distribution → histogram. Avoid dual axes, 3D, pies with many slices, and gauges.

For domain metrics (OTIF, fill rate, transit time, dwell, cost per kg, forecast accuracy, DOH, inventory turns, sales, conversion…) use the formulas and good-direction in `references/kpi-library.md`, so numbers match how the industry defines them.

### 4. Build

1. Copy the template to the output path (e.g. `dashboard.html` or `<topic>-dashboard.html` in the working directory).
2. Embed data: `python scripts/inject_data.py data.xlsx dashboard.html` (replaces the `/*DATA_START*/…/*DATA_END*/` block; use `--rename "Ship Date=ship_date"` to map columns to what the code expects, `--sheet` for Excel, `--monthfirst` for US dates).
3. Edit, in this order:
   - **CONFIG** — title, source, currency, locale, targets.
   - **Derived fields** (section 5) — compute flags like `on_time`, `lane`, `margin` once per row, not inside every chart.
   - **FILTERS** — the dimension columns.
   - **KPIS** — each has `value(rows)`, `fmt`, `good: 'up'|'down'|'flat'`, optional `target`, `deltaFmt: 'pp'` for percentages (show percentage-point change for rates, % change for amounts).
   - **renderCharts** — keep `mount()` and `baseOptions()`; change datasets. Colours come from CSS tokens via `css('--s1')` etc. so charts re-theme automatically.
   - **COLUMNS** — table columns; `num: true` right-aligns numbers.
   - Remove the `demoData()` function once real data is embedded.
4. If the data isn't shipments, still start from the template: the shell (tokens, header, filters, KPI cards, chart mounting, table, export, theme) is domain-agnostic; replace the shipment-specific parts.

When the user only has a few summary numbers (no row data), skip filters and the table; a KPI row plus 1–3 charts with data inline is right.

### 5. Verify — always, before handing over

```bash
python scripts/check_dashboard.py dashboard.html           # static: pinned CDN, tokens, dark mode, viewport…
node scripts/render_check.mjs dashboard.html --out shots/  # browser: JS errors, overflow at 390px, screenshots
```

`render_check.mjs` needs Playwright (preinstalled in Claude Code cloud). If the sandbox can't reach the CDN, serve the library locally: `npm pack chart.js@4.4.1 && tar xzf chart.js-4.4.1.tgz` then add `--lib https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js=package/dist/chart.umd.js`. If no browser is available at all, say so and rely on the static check.

**Look at the screenshots** (desktop-light, desktop-dark, mobile) — numbers that don't add up, partial periods at the edges, clipped labels, unreadable dark-mode colours and empty charts are only visible this way. Sanity-check one KPI by hand against the raw data (e.g. pandas) — a wrong number destroys trust in every other number on the page.

### 6. Deliver

- Give the file path (and a screenshot if you can show images), plus a 3–5 line summary: what's on it, assumptions made, and any data-quality caveats.
- Offer one or two concrete next steps (another breakdown, a target line, a scheduled refresh), not a menu of ten.
- If an Artifact/publish tool is available and the user wants to share it, publish the HTML there.

## Design principles that matter most

These are the things that separate a professional dashboard from a generated-looking one. The *why* matters — apply the reasoning to cases not listed.

- **Every number needs context.** A value without a comparison (target, prior period, benchmark) can't be judged. Deltas compare equal-length periods; label them ("vs previous 90 days" in a tooltip).
- **Colour carries meaning, so spend it carefully.** Neutral greys for structure, one accent for "the main series", green/amber/red only for good/warning/bad status — never as decoration. A delta is green when it's *good*, not when it goes up (transit time going up is red). Always pair colour with text or an arrow (colour-blind users, greyscale print).
- **Sort by value, not alphabet**, for ranking charts; put the worst performer where the eye lands first when the dashboard's purpose is finding problems.
- **Format numbers for humans**: `$1.4M` in KPIs, `$3,891.00` in tables, `89.5%`, one decimal for averages, `tabular-nums` so columns align, `—` for missing (never `NaN`, `undefined`, `null`, or `0` pretending to be missing).
- **"As of" = the latest date in the data**, not the viewer's clock — otherwise a week-old export shows empty "last 30 days" panels.
- **Edges lie.** Partial first/last periods and tiny samples produce fake dips and spikes. Trim partial buckets, and leave gaps for buckets below a minimum sample (the template's `minWeeklySample`).
- **Design for the empty state and the extremes**: zero rows after filtering, one category, a 40-character carrier name, 10 years of data. The template shows "No shipments match these filters" rather than a broken chart.
- **Restraint**: ≤ 6 KPIs, ≤ 6 charts above the table, ≤ 6 series per chart (group the rest as "Other"). If something doesn't change a decision, cut it.
- **Accessible by default**: real `<button>`/`<select>` elements, visible focus, `aria-label` on canvases, `aria-sort` on table headers, text contrast ≥ 4.5:1 in both themes.

## Technical rules

- **One self-contained file.** Inline CSS/JS/data. External scripts only from cdnjs.cloudflare.com (preferred), cdn.jsdelivr.net/npm, or unpkg.com, **pinned to an exact version** (`Chart.js/4.4.1`, never `latest` or `@4`). Fonts: system stack (or Google Fonts if the user wants a brand font).
- **Charting library**: Chart.js 4.4.1 by default (small, good defaults, canvas = fast). Reach for Apache ECharts 5.5.0 (`https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.min.js`) only for maps, sankey, treemaps, heatmap calendars or > 50k points. Hand-rolled SVG is fine for sparklines/bullets. Don't mix libraries.
- **Theming via CSS custom properties** on `:root`, dark overrides under `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {…} }` and again under `:root[data-theme="dark"]`. Charts read tokens at render time and are rebuilt on theme change — never hard-code hex colours in chart configs.
- **State in one object**, one `renderAll()` that derives everything from `state` + data. No panel keeps its own filtered copy — this is what keeps filters consistent across panels.
- **Escape anything from the data** before putting it in `innerHTML` (`esc()`), and escape `</` in embedded JSON (`inject_data.py` does).
- **Storage is optional**: wrap `localStorage` in try/catch; the page must work without it.
- **Mobile**: works at 390px wide — grid collapses to one column, tables scroll inside their card, no horizontal page scroll.
- **Deterministic demo data** (seeded RNG) if you need placeholders, so screenshots and reviews are reproducible; clearly label it as demo data in the footer.

## Reviewing or restyling an existing dashboard

Run both check scripts on it first, screenshot it, then report findings grouped as: **wrong** (incorrect numbers, broken filters, JS errors), **misleading** (truncated axes on bars, dual axes, unsorted rankings, red/green without meaning, partial periods), **hard to read** (density, contrast, formatting, mobile), **polish**. Fix in that order. When restyling, port the existing logic onto the template's token system and components rather than tweaking colours one by one.

## Reference files

- `references/design-system.md` — tokens, palettes (light/dark, categorical, status), typography scale, spacing, grid, and specs for KPI cards, filter bar, chart cards, tables, pills, empty states.
- `references/chart-guide.md` — which chart for which question, anti-patterns, and copy-paste Chart.js recipes (stacked bar, target line, sorted horizontal bar, combo, scatter, histogram, doughnut, bullet/progress) plus an ECharts note.
- `references/kpi-library.md` — formulas, units, good-direction and gotchas for supply-chain/logistics, inventory, procurement, sales/finance and ops KPIs.
- `assets/dashboard-template.html` — the working template.
- `scripts/inject_data.py` — profile/clean data and embed it. `scripts/check_dashboard.py` — static QA. `scripts/render_check.mjs` — browser QA + screenshots.
