# apps/chain_web/src/features/rates-fx/

利率汇率 page at `#rates` (plan 34, D-171). Read-only display of `GET /api/rates-fx`; every number comes from the Python `RatesFxMonitorBuilder`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `rates-fx-page.tsx` | 债市 / 汇率 switch, headline with alerts, table (level, 1w / 1m / 3m / 1y changes, 5-year percentile, 1-year range, date), government curve chart, five-year chart cards, notes | `RatesFxPage` |
| `curve-chart.tsx` | SVG government yield curve today, a month and a year earlier | `CurveChart` |
| `rates-fx-format.ts` | pure helpers: level and change text by unit, change class, group rows, headline, chart keys | `formatLevel`, `formatChange`, `changeClass`, `groupRows`, `ratesHeadline`, `CHART_KEYS` |
| `rates-fx-format.test.ts` | vitest TC-RFF-001..002 |  |
