# apps/chain_web/src/features/sector-monitor/

行业监控 page at `#sector-monitor` (plan 31 ph5, D-168; 财报季信号 plan 35, D-172). Read-only display of `GET /api/sector-monitor` and `GET /api/sector-earnings`; every number comes from the Python `SectorMonitorBuilder` (`make sector-monitor`) and `SectorEarningsSignalBuilder` (`make sector-earnings-signal`).

## Files
| File | Purpose | Contains |
|---|---|---|
| `sector-rankings.tsx` | App Store 排行榜 block: the companies' games (home grossing / free, overseas best) and the home top list | `SectorRankingsPanel` |
| `sector-monitor-page.tsx` | sector switch (房地产 / 游戏), company table (latest values, realised vol and 3-year percentile, 散户温度计), chart grid, empty state, notes | `SectorMonitorPage` |
| `sector-chart.tsx` | SVG multi-line chart on a shared period axis (index / 全部 dashed), zero line, legend focus, hover readout, inverted axis for ranks | `SectorChartCard` |
| `sector-monitor-format.ts` | pure helpers: value by unit, percentile, period labels, shared axis, table columns | `formatValue`, `formatPct`, `periodLabel`, `listPeriods`, `listColumns`, `rankChange`, `marketName`, `SectorColumn` |
| `sector-monitor-format.test.ts` | vitest: formats, period labels, axis and columns |  |
| `sector-earnings-panel.tsx` | 财报季信号 block: every Shenwan L2 sector's season reading (firing / provisional first, then the closest; all on request), past firings with what followed, record, notes | `SectorEarningsPanel` |
| `sector-earnings-format.ts` | pure helpers: season label, signed %, status label, default row pick | `seasonLabel`, `signedPct`, `statusLabel`, `pickRows` |
| `sector-earnings-format.test.ts` | vitest: labels, signs, row pick |  |
