# apps/chain_web/src/features/factors/

因子监控 page at `#factors` (plan 15 phase 7c, D-132). Read-only display of `GET /api/factor-monitor`; every number comes from the Python `FactorMonitorBuilder`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `factors-page.tsx` | headline, charts of the picked factor (cumulative return; forecast vs 21-day realized vol), style and industry tables with alerts, empty state, notes | `FactorsPage` |
| `factor-chart.tsx` | SVG daily line chart of one or two percent series with zero line, date axis and hover readout | `LineChart`, `Series` |
| `factor-format.ts` | pure helpers: style names, signed percent, vol, sigma, colour class, alert rule, table split, series points, headline | `STYLE_ZH`, `factorName`, `signedPct`, `volPct`, `sigma`, `moveClass`, `isAlert`, `splitFactors`, `toPoints`, `monitorHeadline` |
| `factor-format.test.ts` | vitest TC-FMW-001..003 |  |
| `factor-monitor.fixture.json` | FactorMonitorBuilder sample (same as the Go fixture) |  |
