# apps/chain_web/src/features/futures/

期货监测 page at `#futures` (plan 15 ph7i, D-145). Read-only display of `GET /api/futures`; every number comes from the Python `FuturesMonitorBuilder`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `futures-page.tsx` | signals, 股指期货 table (basis, top-20 nets) with charts, families table by group (with top-20 net share) (price, changes, percentiles, curve shape, OI), charts of the picked family, spreads table and chart, notes | `FuturesPage` |
| `futures-chart.tsx` | SVG line over evenly spaced points (dates or contract months) with zero line, sparse labels, hover readout | `FuturesChart`, `ChartPoint` |
| `futures-format.ts` | pure helpers: grouping, signed percent, percentile, extremes, price, spread value, colour class, month / date labels | `spreadText`, `lotsText`, `REGIME_ZH`, `groupFamilies`, `signedPct`, `pctText`, `isExtreme`, `priceText`, `moveClass`, `shortMonth`, `ymdText`, `SHAPE_ZH` |
| `futures-format.test.ts` | vitest TC-FUF-001..004 |  |
| `futures-monitor.fixture.json` | FuturesMonitorBuilder sample (same as the Go fixture) |  |
