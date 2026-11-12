# apps/chain_web/src/features/watchlist/

观察账本 page at `#watchlist` (plan 15 phase 7, D-120). Read-only display of `GET /api/watchlist` and `GET /api/etf-proxy`; every number comes from the Python `WatchlistBuilder` / `EtfProxyBuilder`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `watchlist-page.tsx` | headline (nearest stock, as-of), one card per stock, valuation table, empty state, data notes | `WatchlistPage` |
| `watchlist-charts.tsx` | SVG range bar (52-week line, buy zone, broker target box, price dot) and weekly close chart with hover tooltip | `RangeBar`, `WeeklyChart` |
| `etf-proxy-panel.tsx` | 国家队 ETF panel (phase 7b): headline, weekly core / other position chart with hover, weekly core flow bars, last days, per-index table | `EtfProxyPanel` |
| `etf-proxy-format.ts` | pure helpers of the panel: 亿元 and signed flows, flow class, headline | `yi`, `signedYi`, `flowClass`, `proxyHeadline` |
| `etf-proxy-format.test.ts` | vitest TC-EPW-001..003 |  |
| `watchlist-format.ts` | pure display helpers: status label, number formats, nearest entry, badge count, label placement, scales | `STATUS_ZH`, `statusLabel`, `gapText`, `nearestEntry`, `badgeCount`, `placeLabels`, `niceTicks` |
| `watchlist-format.test.ts` | vitest TC-WL-001..008 against the sample |  |
| `watchlist.fixture.json` | WatchlistBuilder sample of 2026-11-06 (same as the Go fixture) |  |
