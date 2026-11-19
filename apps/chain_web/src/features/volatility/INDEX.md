# apps/chain_web/src/features/volatility/

波动率监测 page at `#volatility` (plan 03 ph6, D-152). Read-only display of `GET /api/volatility`; every number comes from the Python `VolatilityMonitorBuilder` and, for the 小盘观察 panel, `SmallCapWatchBuilder`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `volatility-page.tsx` | headline with alerts, one card per index grouped by 美国 / A股 (latest, change, 1-year percentile and range, alert rules, chart), empty state, notes | `VolatilityPage` |
| `smallcap-panel.tsx` | 小盘观察 panel (plan 30 ph2): headline, signal table with triggered rows first (red) and near rows (amber), 中证1000 chart with the watch levels, 融资余额 and 融资余额 / 流通市值 charts (ph4) | `SmallCapPanel` |
| `smallcap-format.ts` | pure helpers: row order, value / trigger text by unit, chart points (中证1000, 融资余额, share of float cap), level lines, headline | `STATE_LABEL`, `orderRows`, `formatScValue`, `formatScTrigger`, `smallPoints`, `marginPoints`, `marginSharePoints`, `levelRefs`, `smallCapHeadline` |
| `smallcap-format.test.ts` | vitest TC-SCF-001..004 |  |
| `volatility-chart.tsx` | SVG daily line chart of one series (index or 中证1000 close) over the window with dashed reference lines (alert level or median; watch levels), latest dot, month ticks, hover readout | `VolatilityChart` |
| `volatility-format.ts` | pure helpers: grouping, value and date format, reference level, alert rule text, headline | `GROUPS`, `groupLines`, `formatVol`, `dayLabel`, `refLevel`, `alertText`, `volHeadline` |
| `volatility-format.test.ts` | vitest TC-VOF-001..003 |  |
| `volatility-monitor.fixture.json` | VolatilityMonitorBuilder sample (same as the Go fixture) plus `smallcap` (the Go smallcap_watch.json fixture) |  |
