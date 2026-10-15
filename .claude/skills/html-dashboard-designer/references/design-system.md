# Dashboard Design System

The template already implements all of this. Use this file when adapting it, building a component the template lacks, or reviewing someone else's dashboard.

## Contents
1. Tokens (colour, light + dark)
2. Typography
3. Spacing, radius, elevation
4. Layout grid & responsive behaviour
5. Components: header, filter bar, KPI card, chart card, table, pills, empty/loading states
6. Writing on dashboards
7. Brand adaptation

---

## 1. Tokens

All colours are CSS custom properties on `:root`. Nothing else in the file uses a literal hex value — this is what makes dark mode and re-branding a 20-line change.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#f6f7f9` | `#0f1216` | page background (slightly off the surface so cards lift) |
| `--surface` | `#ffffff` | `#171b21` | cards, inputs |
| `--surface-2` | `#f1f3f6` | `#1e232b` | table header, hover, neutral chips |
| `--border` | `#e3e6eb` | `#2a303a` | 1px card/input borders |
| `--text` | `#16191f` | `#e8ebf0` | primary text, values |
| `--text-2` | `#5b6372` | `#a3abb9` | labels, axis ticks |
| `--text-3` | `#8a93a3` | `#6f7889` | hints, footnotes, target lines |
| `--accent` / `--accent-soft` | `#2f6fde` / `#e8f0fd` | `#6c9cf0` / `#1d2a40` | primary series, focus ring, links |
| `--good` / `--good-soft` | `#1a8a5a` / `#e3f4ec` | `#45c08a` / `#15302a` | on/above target, favourable delta |
| `--warn` / `--warn-soft` | `#b26a00` / `#fdf1dc` | `#e3a645` / `#34291a` | at risk, within tolerance |
| `--bad` / `--bad-soft` | `#c8372d` / `#fbe7e5` | `#f0736a` / `#3a1f1e` | breach, unfavourable delta |
| `--info` / `--info-soft` | = accent | = accent | neutral status ("In transit") |
| `--grid` | `#eceef2` | `#232933` | chart gridlines (barely visible on purpose) |

**Categorical series** `--s1 … --s6` (light → dark): blue `#2f6fde→#6c9cf0`, orange `#e07b1f→#f0a050`, teal `#14a38b→#3cc9ae`, violet `#8a5cd6→#b08cf0`, pink `#d6457a→#f07aa4`, slate `#6b7a8f→#8f9bb0`. The order maximises contrast between neighbours and stays distinguishable for the common colour-vision deficiencies. Beyond six series, group the tail into "Other" (slate) instead of inventing more colours.

**Sequential** (heatmaps, choropleths): interpolate from `--accent-soft` to `--accent`. **Diverging** (variance vs target): `--bad` ← `--surface-2` → `--good`.

Rules:
- Status colours mean status. Don't use green as "series 3".
- Light-mode status text on its `-soft` background meets 4.5:1; keep that pairing for pills/deltas.
- Dark mode is not inverted light mode: surfaces get *lighter* as they rise, colours get lighter/desaturated, shadows go away.
- Theme selectors (all three are needed):
  ```css
  :root { /* light */ }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { /* dark */ } }
  :root[data-theme="dark"] { /* dark (same values) */ }
  ```

## 2. Typography

System stack: `ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` — native, fast, no network. Mono for IDs: `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`.

| Role | Size / weight | Notes |
|---|---|---|
| Page title | 22px / 700, -0.01em | one line, 2–4 words |
| KPI value | 28px / 650, -0.02em | `tabular-nums`, `white-space: nowrap` |
| Card title | 14px / 600 | sentence case, says what *and* how ("Freight spend by lane") |
| Body / table | 13–14px / 400 | |
| Label / table header | 11–12px / 600, uppercase, +0.04em | `--text-2` / `--text-3` |
| Hint / footnote | 11–12px | `--text-3` |

Always `font-variant-numeric: tabular-nums` on numbers so digits align in columns and don't jitter when filters change.

## 3. Spacing, radius, elevation

4px base: 4 / 8 / 12 / 16 / 24 / 32. Card padding 14–16px, grid gap 16px, page gutter 16px mobile / 32px desktop. Radius 12px cards, 8px inputs/buttons, 999px pills. Elevation: 1px border + very soft shadow in light; border only in dark.

## 4. Layout grid

- Max width 1440px, centred.
- 12-column CSS grid for chart cards: `span-8 + span-4` (main trend + supporting), `span-6 + span-6` (two breakdowns), `span-4 ×3` (small multiples). Below 900px everything spans 12.
- KPI row: `grid-template-columns: repeat(auto-fit, minmax(190px, 1fr))` — wraps itself from 6 across to 2 or 1.
- Chart cards need a **fixed height container** (`.chart-box { position: relative; height: 260px }`) with `maintainAspectRatio: false`, otherwise Chart.js grows forever or collapses.
- Set `min-width: 0` on grid children so long labels don't blow out the grid.
- Wide tables scroll *inside* their card (`overflow-x: auto` wrapper); the page itself never scrolls horizontally.

Reading order follows importance: KPIs → main trend → breakdowns → detail. Put the chart that answers the dashboard's main question top-left of the chart grid.

## 5. Components

### Header
Title, then a sub-line: `Data as of 15 October 2026 · 900 shipments`. Actions right-aligned: Export CSV (filtered rows), Print, Theme toggle. On mobile they wrap under the title.

### Filter bar
- Native `<select>` elements in `<label>`s (accessible, mobile-friendly, zero code). First option "All <things>".
- Period selector first. Options relative to *as-of*: Last 30 / 90 / 180 days / All. Add "YTD" or month pickers if the business thinks in months.
- Live count "410 of 900 shipments · 2 filters" and a Reset button.
- Cascading filters (carrier list narrows when mode chosen) are nice-to-have; only add when lists are long.
- Click-to-filter from charts (Chart.js `onClick` → set state → `renderAll()`) is a strong upgrade for exploration dashboards; always reflect it in the filter bar so it's visible and reversible.

### KPI card
```
┌────────────────────────────────┐
│ On-time delivery   Target 95.0%│  label (text-2) + target (text-3)
│ 89.5%                          │  value 28px
│ ▲ 2.2 pp            ╱╲╱╲_╱     │  delta pill + sparkline (84×26)
└────────────────────────────────┘
```
- Delta pill: arrow shows direction, colour shows good/bad given `good: 'up'|'down'|'flat'`. Rates use **percentage points** (`pp`), amounts use **%**. Tooltip explains the comparison.
- `flat` = informational (spend going up isn't inherently good or bad) → grey pill.
- No comparison available → muted text ("current snapshot", "all time"), never an empty gap or a fake 0%.
- Optionally colour the value itself red/amber/green against target — but only one of value or delta, not both.

### Chart card
Title (what + by what), hint on the right (unit, basis, "top 8", "worst first"), then the fixed-height chart box with an `.empty` overlay. Legend at the bottom only when there are ≥ 2 series; otherwise hide it and let the title name the measure.

### Table
- Sticky header on `--surface-2`, uppercase 11px labels, `aria-sort` on the sorted column, click to sort, click again to reverse.
- Numbers right-aligned with `tabular-nums`; dates short (`Oct 15`); IDs in mono.
- Status as pills: soft background + strong text in the status colour + the word itself.
- Search box (debounced 150ms) across the human-meaningful columns. Pagination at 25 rows; show "Page 1 of 17" and "410 rows".
- Optional: conditional formatting cells (e.g. transit days over SLA in `--bad`), inline data bars for one numeric column.

### Empty, loading and error states
- Zero rows: chart shows "No shipments match these filters"; KPIs show `—`; table shows a single centred row.
- Library failed to load (offline + CDN): show "Chart library failed to load" in each chart box rather than throwing — KPIs and table still work because they're plain HTML.
- Never show `NaN`, `Infinity`, `undefined`, `null`, `[object Object]`, or `Invalid Date`.

## 6. Writing on dashboards

- Titles state the measure and the cut: "On-time % by carrier", not "Carrier Analysis".
- Units in the hint or axis, not repeated on every tick when obvious.
- Footer defines every non-obvious metric and names the source and refresh.
- Use the user's vocabulary (their column names, their business terms: "OTIF", "DOH", "ASN") — a dashboard is for them, not a generic audience.
- An optional one-line "headline" under the title ("On-time slipped 3 pp, driven by MSC on Rotterdam → Jebel Ali") is high value for executive audiences; compute it from the data rather than hard-coding it.

## 7. Brand adaptation

To apply a company brand: set `--accent` (+ `--accent-soft`, a ~10% tint) to the brand primary, move the brand secondary into `--s2`, keep status colours standard (brands rarely define good/warn/bad well), and if a brand font is required load it from Google Fonts with `display=swap` and put it first in `--font`. Re-run `render_check.mjs` and look at both themes — brand colours often fail contrast in dark mode and need a lighter dark-mode variant.
