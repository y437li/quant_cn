# apps/chain_web/src/features/macro/

宏观监测 page at `#macro` (plan 15 ph7h, D-143). Read-only display of `GET /api/macro`; every number comes from the Python `MacroMonitorBuilder`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `macro-page.tsx` | headline, one card per line grouped by 价格 / 景气 / 货币 / 社融 (latest, change, 5-year percentile, new marker, chart), empty state, notes | `MacroPage` |
| `macro-chart.tsx` | SVG monthly line chart of one line's last 60 prints with reference line (50 for PMI, else 0), latest dot, year ticks, hover readout | `MacroChart` |
| `macro-format.ts` | pure helpers: grouping, value format by unit, extreme percentile, month label, reference line, headline | `GROUPS`, `EXTREME`, `groupSeries`, `formatValue`, `isExtreme`, `monthLabel`, `refLine`, `macroHeadline` |
| `macro-format.test.ts` | vitest TC-MCF-001..003 |  |
| `macro-monitor.fixture.json` | MacroMonitorBuilder sample (same as the Go fixture) |  |
