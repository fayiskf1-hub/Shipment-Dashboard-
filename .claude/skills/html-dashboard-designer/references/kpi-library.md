# KPI Library

Formulas, units, which direction is good, and the traps that make dashboards wrong. Use the user's own definitions when they give them; otherwise use these and state the definition in the footer.

**General rules**
- Ratios: compute `sum(numerator) / sum(denominator)` over the filtered rows. Never average row-level or weekly percentages (unweighted → wrong).
- Rates change in **percentage points** (89.5% → 91.7% is +2.2 pp, not +2.5%).
- Decide the denominator explicitly: e.g. on-time % over *delivered* shipments only — in-transit ones have no outcome yet.
- Pick one date to bucket by and say which (ship date vs delivery date vs order date give different trends).
- "Good" column → drives delta colour in the template (`good: 'up' | 'down' | 'flat'`).

## Contents
1. Logistics & shipments
2. Inventory & replenishment
3. Procurement & supplier
4. Demand planning
5. Warehouse & fulfilment
6. Sales, finance & e-commerce
7. Operations / service

---

## 1. Logistics & shipments

| KPI | Formula | Unit | Good | Gotchas |
|---|---|---|---|---|
| Shipments | count of shipments (or containers/TEU — say which) | # | flat/up | Duplicates from multi-leg rows; dedupe on shipment ID |
| On-time delivery (OTD) | delivered with `actual ≤ promised/ETA` ÷ delivered | % | up | Which ETA? Original vs latest revised changes the answer a lot — prefer original/committed |
| OTIF | orders delivered on time **and** in full ÷ orders | % | up | In-full = delivered qty ≥ ordered qty per line, all lines. Usually lower than OTD |
| Avg transit time | mean(delivered − shipped) | days | down | Show median or P90 too; sea freight has long tails |
| Transit-time reliability | % within ±N days of planned transit | % | up | |
| ETA accuracy | |actual − ETA at departure| mean | days | down | |
| Delay days | max(0, actual − ETA) averaged over late shipments | days | down | |
| Freight spend | sum(cost) | currency | flat | Include accessorials? Currency conversion date? |
| Cost per kg / per TEU / per unit | sum(cost) ÷ sum(kg/TEU/units) | currency | down | Use chargeable weight for air (max(actual, volumetric)) if available |
| Freight cost % of goods value | freight ÷ goods value | % | down | |
| Customs clearance time | release − arrival | days/hours | down | |
| Dwell time (port/yard/DC) | departure − arrival at node | days | down | Free-time breaches → demurrage/detention risk |
| Demurrage & detention cost | sum(D&D charges) | currency | down | |
| Open exceptions | count in Delayed / Hold / Damaged status now | # | down | Snapshot — no period delta |
| Carrier scorecard | OTD, transit, cost/kg, claims rate per carrier | mixed | — | Need ≥ ~20 shipments per carrier to rank fairly |
| Container utilisation | loaded volume ÷ container capacity | % | up | |
| Claims / damage rate | shipments with claim ÷ shipments | % | down | |

## 2. Inventory & replenishment

| KPI | Formula | Unit | Good | Gotchas |
|---|---|---|---|---|
| Stock on hand (SOH) | units or value at a point in time | units/currency | — | Snapshot; never sum across dates |
| Days on hand (DOH) / days of cover | SOH ÷ avg daily sales (forward forecast or trailing N days) | days | in range | Say which demand basis. Too high = overstock, too low = stockout risk |
| Weeks of cover (WOC) | SOH ÷ avg weekly sales | weeks | in range | |
| Inventory turns | COGS (or units sold) over period ÷ avg inventory | ×/yr | up | Annualise if period < 1 year |
| Sell-through | units sold ÷ (units received + opening stock) | % | up | Retail standard over a season/phase |
| In-stock / availability | store-SKUs with SOH > 0 ÷ store-SKUs ranged | % | up | Exclude deactivated / not-ranged SKUs |
| Stockout rate | 1 − in-stock | % | down | |
| Fill rate (line / unit) | shipped ÷ ordered | % | up | Line fill vs unit fill differ — label it |
| Aged / slow-moving stock | value with no sale in N days ÷ total value | % | down | |
| Min/max compliance | SKUs with SOH between min and max ÷ SKUs | % | up | |
| Replenishment lead time | received at store − order raised | days | down | |
| Allocation accuracy | allocated in line with plan ÷ allocated | % | up | |

## 3. Procurement & supplier

| KPI | Formula | Unit | Good |
|---|---|---|---|
| Supplier OTIF | POs received on time & in full ÷ POs | % | up |
| PO cycle time | PO approval → receipt | days | down |
| ASN accuracy | ASN lines matching receipt ÷ ASN lines | % | up |
| Purchase price variance | (actual − standard price) × qty | currency | down |
| Spend under contract | contracted spend ÷ total spend | % | up |
| Supplier defect rate | rejected qty ÷ received qty | % / ppm | down |

## 4. Demand planning

| KPI | Formula | Unit | Good | Gotchas |
|---|---|---|---|---|
| Forecast accuracy | 1 − Σ|A − F| ÷ ΣA (= 1 − WMAPE) | % | up | Weighted; plain MAPE explodes on low-volume SKUs |
| WMAPE | Σ|A − F| ÷ ΣA | % | down | |
| Forecast bias | Σ(F − A) ÷ ΣA | % | → 0 | Positive = over-forecast. Show sign; diverging colour |
| Tracking signal | Σ(A − F) ÷ MAD | — | within ±4 | |
| Plan vs actual | actual ÷ plan − 1 | % | context | |

## 5. Warehouse & fulfilment

| KPI | Formula | Unit | Good |
|---|---|---|---|
| Order cycle time | ship − order | hours/days | down |
| Dock-to-stock | putaway complete − receipt | hours | down |
| Pick accuracy | correct lines ÷ picked lines | % | up |
| Units per hour (UPH) | units picked ÷ labour hours | #/h | up |
| Orders shipped same day | same-day shipped ÷ orders received before cut-off | % | up |
| Capacity utilisation | used locations ÷ total locations | % | in range |

## 6. Sales, finance & e-commerce

| KPI | Formula | Unit | Good | Gotchas |
|---|---|---|---|---|
| Revenue / net sales | Σ price × qty − returns − discounts | currency | up | Gross vs net — say which |
| Gross margin % | (revenue − COGS) ÷ revenue | % | up | pp deltas |
| Average order value | revenue ÷ orders | currency | up | |
| Units per transaction | units ÷ transactions | # | up | |
| Like-for-like (LFL) growth | sales this period ÷ same period last year − 1, same stores only | % | up | Exclude new/closed stores |
| Conversion rate | orders ÷ sessions (or footfall) | % | up | |
| Return rate | returned units ÷ sold units | % | down | Lags sales — use sale-date cohort |
| Budget variance | actual − budget (and %) | currency | context | Diverging colours; favourable depends on revenue vs cost line |
| DSO | receivables ÷ revenue × days | days | down | |

## 7. Operations / service

| KPI | Formula | Unit | Good |
|---|---|---|---|
| SLA compliance | items resolved within SLA ÷ items resolved | % | up |
| Backlog | open items now | # | down (snapshot) |
| Mean time to resolve | mean(resolved − opened) | hours | down (also show P90) |
| First-contact resolution | resolved at first touch ÷ resolved | % | up |
| Throughput | items completed per period | # | up |

---

## Picking the headline KPIs

For a typical **shipment / logistics control tower**: Shipments, On-time %, Avg transit days, Freight spend, Cost per kg, Open exceptions (what the template ships with).

For **inventory / allocation**: SOH value, Days of cover, In-stock %, Sell-through %, Aged stock %, Stores below min.

For **supplier performance**: Supplier OTIF, ASN accuracy, PO cycle time, Defect rate, Spend.

For **sales**: Net sales, LFL growth, Gross margin %, AOV, Conversion, Return rate.

Six is a ceiling, not a goal. Fewer, well-chosen numbers beat a wall of tiles.
